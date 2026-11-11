#!/usr/bin/env python3
"""Train the cluster-level track-selection DNNs (TrackTfClassifier with useClusterFeatures).

Input: ROOT files written by HitFeatDumper (tree hitFeatDumper/tracks), one directory per sample chunk
(".../chunk<N>/hit_dump.root"). Chunks are split by number into training and validation sets.

Graph groups, file names and iterations are those of RecoTracker/FinalTrackSelectors/python/trackSelectionTfHit_cff.py,
the iteration order of the dump that of customiseHitFeatDump.py, and the production working points are read from the
Run3_2024 configuration: run in a CMSSW environment.

Output, in --outdir:
  <group>Hit_Run3_2024.pb   frozen graphs, inputs x[39] (raw features) and y[1] (originalAlgo), output Identity
  cuts.json                 per-iteration qualityCuts giving the same number of fake tracks as the production
                            working points on the validation chunks

The training is deterministic (fixed seeds, TensorFlow op determinism): the same inputs give the same graphs
with the same release and CPU model.
"""
import argparse
import glob
import json
import os
import re

import FWCore.ParameterSet.Config as cms
import numpy as np
import ROOT
import tensorflow as tf
from Configuration.Eras.Era_Run3_2024_cff import Run3_2024
from RecoTracker.FinalTrackSelectors.customiseHitFeatDump import DUMPED_ITERATIONS
from RecoTracker.FinalTrackSelectors.trackSelectionTfHit_cff import HIT_DNN_CUTS, HIT_DNN_GRAPHS
from tensorflow.python.framework.convert_to_constants import convert_variables_to_constants_v2

# one model per group, as for the production Run3 models
GROUPS = {group: [iteration for iteration, (g, _) in HIT_DNN_CUTS.items() if g == group] for group in HIT_DNN_GRAPHS}

N_ALGOS = 48                                   # one-hot size for originalAlgo
LOG_TRACK_FEATURES = [0, 4, 8, 9, 14, 15, 16, 19, 20]  # pt, inner/outer rho, errors, chi2/ndof
LOG1P_CLUSTER_FEATURES = [3, 4, 8]                     # pixel mean/max charge, strip mean charge
HIDDEN_LAYERS = (256, 256, 128, 64)
DROPOUT = 0.1
BATCH_SIZE = 4096
MAX_ROWS_FOR_NORMALISATION = 2_000_000


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--inputs", required=True, help="glob of HitFeatDumper files, e.g. '/path/chunk*/hit_dump.root'")
    parser.add_argument("--train-chunks", default="0-39", help="chunk numbers used for training (range a-b)")
    parser.add_argument("--val-chunks", default="40-47", help="chunk numbers used for validation and working points")
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--seed", type=int, default=1)
    return parser.parse_args()


def production_cuts():
    """qualityCuts (loose, tight, highPurity) of the production TrackTfClassifier of each iteration"""
    process = cms.Process("CUTS", Run3_2024)
    process.load("RecoTracker.IterativeTracking.iterativeTk_cff")
    return {iteration: list(getattr(process, iteration).qualityCuts) for iteration in HIT_DNN_CUTS}


def chunk_range(text):
    first, last = (int(x) for x in text.split("-"))
    return set(range(first, last + 1))


def chunk_number(path):
    return int(re.search(r"chunk(\d+)", path).group(1))


def load(pattern, chunks):
    files = [f for f in sorted(glob.glob(pattern)) if chunk_number(f) in chunks]
    names = ROOT.std.vector("string")()
    for f in files:
        names.push_back(f)
    columns = ROOT.RDataFrame("hitFeatDumper/tracks", names).AsNumpy(["x", "h", "algo", "mva", "label", "iter"])
    track_features = np.stack([np.asarray(row, dtype=np.float32) for row in columns["x"]])
    cluster_features = np.stack([np.asarray(row, dtype=np.float32) for row in columns["h"]])
    return track_features.shape[1], {
        "features": np.hstack([track_features, cluster_features]),
        "algo": columns["algo"].astype(np.float32).reshape(-1, 1),
        "production_score": columns["mva"],
        "label": columns["label"].astype(np.float32),
        "iteration": columns["iter"].astype(int),
    }


def select(sample, mask):
    return {key: value[mask] for key, value in sample.items()}


def transform(x, n_track_features):
    """feature transformation done inside the graph, so that CMSSW feeds raw values; x = track then cluster features"""
    log1p_features = [n_track_features + i for i in LOG1P_CLUSTER_FEATURES]
    columns = []
    for i in range(x.shape[1]):
        column = x[:, i:i + 1]
        if i in LOG_TRACK_FEATURES:
            column = tf.math.log(tf.maximum(column, 1e-6))
        elif i in log1p_features:
            column = tf.math.log1p(tf.maximum(column, 0.))
        columns.append(column)
    return tf.concat(columns, axis=1)


def build_model(mean, std, n_track_features):
    x = tf.keras.Input(shape=(mean.shape[0],), name="x")
    y = tf.keras.Input(shape=(1,), name="y")
    features = tf.keras.layers.Lambda(lambda a: transform(a, n_track_features))(x)
    features = tf.keras.layers.Lambda(lambda a: tf.clip_by_value((a - mean) / std, -10., 10.))(features)
    algo = tf.keras.layers.Lambda(lambda a: tf.one_hot(tf.cast(a[:, 0], tf.int32), N_ALGOS))(y)
    hidden = tf.keras.layers.Concatenate()([features, algo])
    for width in HIDDEN_LAYERS:
        hidden = tf.keras.layers.Dense(width, activation="relu")(hidden)
        hidden = tf.keras.layers.Dropout(DROPOUT)(hidden)
    output = tf.keras.layers.Dense(1, activation="sigmoid")(hidden)
    model = tf.keras.Model([x, y], output)
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="binary_crossentropy",
                  metrics=[tf.keras.metrics.AUC(name="auc")])
    return model


def export_graph(model, path):
    n_features = model.inputs[0].shape[1]
    signature = [tf.TensorSpec([None, n_features], tf.float32, name="x"), tf.TensorSpec([None, 1], tf.float32, name="y")]
    function = tf.function(lambda x, y: model([x, y], training=False), input_signature=signature)
    graph = convert_variables_to_constants_v2(function.get_concrete_function()).graph.as_graph_def()
    node_names = {node.name for node in graph.node}
    assert {"x", "y", "Identity"} <= node_names, "graph inputs/outputs not found"
    with open(path, "wb") as f:
        f.write(graph.SerializeToString(deterministic=True))  # byte-identical output


def matched_cuts(new_score, production_score, label, production_cuts):
    """thresholds on the new score passing the same number of fakes as each production threshold"""
    fake_scores = np.sort(new_score[label == 0])[::-1]
    if len(fake_scores) == 0:
        return [1.] * len(production_cuts)  # no fakes in the validation sample: nothing to match
    cuts = []
    for cut in production_cuts:
        n_fakes = int(((production_score > cut) & (label == 0)).sum())
        if 0 < n_fakes <= len(fake_scores):
            cuts.append(float(fake_scores[n_fakes - 1]))
        else:
            cuts.append(float(fake_scores[0] + 1e-3))
    return cuts


def train_group(group, train, val, n_track_features, reference_cuts, args):
    indices = [DUMPED_ITERATIONS.index(i) for i in GROUPS[group]]
    train = select(train, np.isin(train["iteration"], indices))
    val = select(val, np.isin(val["iteration"], indices))

    transformed = transform(tf.constant(train["features"][:MAX_ROWS_FOR_NORMALISATION]), n_track_features).numpy()
    model = build_model(tf.constant(transformed.mean(0)), tf.constant(transformed.std(0) + 1e-6), n_track_features)
    callbacks = [tf.keras.callbacks.EarlyStopping(monitor="val_auc", mode="max", patience=3, restore_best_weights=True),
                 tf.keras.callbacks.ReduceLROnPlateau(monitor="val_auc", mode="max", factor=0.3, patience=1)]
    model.fit([train["features"], train["algo"]], train["label"],
              validation_data=([val["features"], val["algo"]], val["label"]),
              batch_size=BATCH_SIZE, epochs=args.epochs, callbacks=callbacks, verbose=2)
    export_graph(model, os.path.join(args.outdir, os.path.basename(HIT_DNN_GRAPHS[group][1])))

    score = 2 * model.predict([val["features"], val["algo"]], batch_size=16384, verbose=0)[:, 0] - 1
    cuts = {}
    for iteration in GROUPS[group]:
        in_iteration = val["iteration"] == DUMPED_ITERATIONS.index(iteration)
        cuts[iteration] = {"model": group, "production": reference_cuts[iteration],
                           "new": matched_cuts(score[in_iteration], val["production_score"][in_iteration],
                                               val["label"][in_iteration], reference_cuts[iteration])}
    return cuts


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    tf.keras.utils.set_random_seed(args.seed)
    tf.config.experimental.enable_op_determinism()

    n_track_features, train = load(args.inputs, chunk_range(args.train_chunks))
    _, val = load(args.inputs, chunk_range(args.val_chunks))
    print(f"training rows {len(train['label'])}, validation rows {len(val['label'])}", flush=True)

    reference_cuts = production_cuts()
    cuts = {}
    for group in GROUPS:
        cuts.update(train_group(group, train, val, n_track_features, reference_cuts, args))
    with open(os.path.join(args.outdir, "cuts.json"), "w") as f:
        json.dump(cuts, f, indent=1)
    for iteration, entry in cuts.items():
        print(f'    "{iteration}": ("{entry["model"]}", [{", ".join("%.4f" % c for c in entry["new"])}]),')
    print("TRAINING_DONE")


if __name__ == "__main__":
    main()
