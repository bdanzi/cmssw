#!/usr/bin/env python3
"""Train the hit-level track-selection DNNs used by TrackHitTfClassifier.

Input: ROOT files written by HitFeatDumper (tree hitFeatDumper/tracks), one directory per sample chunk
(".../chunk<N>/hit_dump.root"). Chunks are split by number into training and validation sets.

Output, in --outdir:
  <group>Hit_Run3_2024.pb   frozen graphs, inputs x[39] (raw features) and y[1] (originalAlgo), output Identity
  cuts.json                 per-iteration qualityCuts giving the same number of fake tracks as the production
                            working points on the validation chunks

The training is deterministic (fixed seeds, TensorFlow op determinism): the same inputs give the same graphs.
"""
import argparse
import glob
import json
import os
import re

import numpy as np
import ROOT
import tensorflow as tf
from tensorflow.python.framework.convert_to_constants import convert_variables_to_constants_v2

# iteration index used by HitFeatDumper (order of its "tracks" parameter)
ITERATIONS = ["initialStep", "highPtTripletStep", "lowPtQuadStep", "lowPtTripletStep", "detachedQuadStep",
              "detachedTripletStep", "pixelPairStep", "mixedTripletStep", "pixelLessStep", "tobTecStep",
              "jetCoreRegionalStepBarrel", "jetCoreRegionalStepEndcap", "displacedRegionalStep"]

# one model per group, as for the production Run3 models
GROUPS = {
    "MkFit": ["initialStep", "highPtTripletStep", "detachedQuadStep", "detachedTripletStep", "pixelPairStep",
              "mixedTripletStep", "tobTecStep"],
    "CKF": ["lowPtQuadStep", "lowPtTripletStep"],
    "MkFitPixelLessOnly": ["pixelLessStep"],
}

# production qualityCuts (loose, tight, highPurity) of the Run3 TrackTfClassifier working points
PRODUCTION_CUTS = {
    "initialStep": [-0.35, 0.1, 0.28], "highPtTripletStep": [0.47, 0.55, 0.62], "lowPtQuadStep": [-0.33, 0.13, 0.35],
    "lowPtTripletStep": [-0.23, 0.15, 0.41], "detachedQuadStep": [-0.66, -0.15, 0.46],
    "detachedTripletStep": [-0.42, 0.16, 0.78], "pixelPairStep": [-0.31, -0.13, 0.13],
    "mixedTripletStep": [-0.86, -0.68, -0.43], "pixelLessStep": [-0.8, -0.69, -0.4], "tobTecStep": [-0.76, -0.65, -0.55],
}

N_TRACK_FEATURES = 29  # TrackTfClassifier inputs
N_HIT_FEATURES = 10    # HitFeatDumper / TrackHitTfClassifier hit-level inputs
N_FEATURES = N_TRACK_FEATURES + N_HIT_FEATURES
N_ALGOS = 48           # one-hot size for originalAlgo
LOG_FEATURES = [0, 4, 8, 9, 14, 15, 16, 19, 20]            # pt, inner/outer rho, errors, chi2/ndof
LOG1P_FEATURES = [N_TRACK_FEATURES + i for i in (3, 4, 8)]  # pixel mean/max charge, strip mean charge
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
    hit_features = np.stack([np.asarray(row, dtype=np.float32) for row in columns["h"]])
    return {
        "features": np.hstack([track_features, hit_features]),
        "algo": columns["algo"].astype(np.float32).reshape(-1, 1),
        "production_score": columns["mva"],
        "label": columns["label"].astype(np.float32),
        "iteration": columns["iter"].astype(int),
    }


def select(sample, mask):
    return {key: value[mask] for key, value in sample.items()}


def transform(x):
    """feature transformation done inside the graph, so that CMSSW feeds raw values"""
    columns = []
    for i in range(N_FEATURES):
        column = x[:, i:i + 1]
        if i in LOG_FEATURES:
            column = tf.math.log(tf.maximum(column, 1e-6))
        elif i in LOG1P_FEATURES:
            column = tf.math.log1p(tf.maximum(column, 0.))
        columns.append(column)
    return tf.concat(columns, axis=1)


def build_model(mean, std):
    x = tf.keras.Input(shape=(N_FEATURES,), name="x")
    y = tf.keras.Input(shape=(1,), name="y")
    features = tf.keras.layers.Lambda(transform)(x)
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
    signature = [tf.TensorSpec([None, N_FEATURES], tf.float32, name="x"), tf.TensorSpec([None, 1], tf.float32, name="y")]
    function = tf.function(lambda x, y: model([x, y], training=False), input_signature=signature)
    graph = convert_variables_to_constants_v2(function.get_concrete_function()).graph.as_graph_def()
    node_names = {node.name for node in graph.node}
    assert {"x", "y", "Identity"} <= node_names, "graph inputs/outputs not found"
    with open(path, "wb") as f:
        f.write(graph.SerializeToString(deterministic=True))  # byte-identical output


def matched_cuts(new_score, production_score, label, production_cuts):
    """thresholds on the new score passing the same number of fakes as each production threshold"""
    fake_scores = np.sort(new_score[label == 0])[::-1]
    cuts = []
    for cut in production_cuts:
        n_fakes = int(((production_score > cut) & (label == 0)).sum())
        if 0 < n_fakes <= len(fake_scores):
            cuts.append(float(fake_scores[n_fakes - 1]))
        else:
            cuts.append(float(fake_scores[0] + 1e-3))
    return cuts


def train_group(group, train, val, args):
    indices = [ITERATIONS.index(i) for i in GROUPS[group]]
    train = select(train, np.isin(train["iteration"], indices))
    val = select(val, np.isin(val["iteration"], indices))

    transformed = transform(tf.constant(train["features"][:MAX_ROWS_FOR_NORMALISATION])).numpy()
    model = build_model(tf.constant(transformed.mean(0)), tf.constant(transformed.std(0) + 1e-6))
    callbacks = [tf.keras.callbacks.EarlyStopping(monitor="val_auc", mode="max", patience=3, restore_best_weights=True),
                 tf.keras.callbacks.ReduceLROnPlateau(monitor="val_auc", mode="max", factor=0.3, patience=1)]
    model.fit([train["features"], train["algo"]], train["label"],
              validation_data=([val["features"], val["algo"]], val["label"]),
              batch_size=BATCH_SIZE, epochs=args.epochs, callbacks=callbacks, verbose=2)
    export_graph(model, os.path.join(args.outdir, f"{group}Hit_Run3_2024.pb"))

    score = 2 * model.predict([val["features"], val["algo"]], batch_size=16384, verbose=0)[:, 0] - 1
    cuts = {}
    for iteration in GROUPS[group]:
        in_iteration = val["iteration"] == ITERATIONS.index(iteration)
        cuts[iteration] = {"model": group, "production": PRODUCTION_CUTS[iteration],
                           "new": matched_cuts(score[in_iteration], val["production_score"][in_iteration],
                                               val["label"][in_iteration], PRODUCTION_CUTS[iteration])}
    return cuts


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    tf.keras.utils.set_random_seed(args.seed)
    tf.config.experimental.enable_op_determinism()

    train = load(args.inputs, chunk_range(args.train_chunks))
    val = load(args.inputs, chunk_range(args.val_chunks))
    print(f"training rows {len(train['label'])}, validation rows {len(val['label'])}", flush=True)

    cuts = {}
    for group in GROUPS:
        cuts.update(train_group(group, train, val, args))
    with open(os.path.join(args.outdir, "cuts.json"), "w") as f:
        json.dump(cuts, f, indent=1)
    for iteration, entry in cuts.items():
        print(f'    "{iteration}": ("{entry["model"]}", [{", ".join("%.4f" % c for c in entry["new"])}]),')
    print("TRAINING_DONE")


if __name__ == "__main__":
    main()
