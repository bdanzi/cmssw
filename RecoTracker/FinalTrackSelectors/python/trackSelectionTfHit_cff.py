import FWCore.ParameterSet.Config as cms
from Configuration.ProcessModifiers.trackingLowPtRun3_cff import trackingLowPtRun3
from PhysicsTools.TensorFlow.tfGraphDefProducer_cfi import tfGraphDefProducer as _tfGraphDefProducer

# Cluster-level track-selection DNNs (TrackTfClassifier with useClusterFeatures) used with the trackingLowPtRun3 procModifier:
# the track-level TrackTfClassifier inputs plus the cluster-level inputs of TrackTfFeatures.h, trained on 2024 TTbar PU MC.
# Training recipe (it reads the graph groups and the iterations from here): RecoTracker/FinalTrackSelectors/test/trackHitDNN/README.md

_HIT_DNN_DATA = "RecoTracker/FinalTrackSelectors/data/TrackTfClassifier"

# graph group -> (ES label, frozen graph), one graph per group as for the production Run 3 DNNs
HIT_DNN_GRAPHS = {
    "MkFit": ("trackSelectionTfHit", f"{_HIT_DNN_DATA}/MkFitHit_Run3_2024.pb"),
    "CKF": ("trackSelectionTfHitCKF", f"{_HIT_DNN_DATA}/CKFHit_Run3_2024.pb"),
    "MkFitPixelLessOnly": ("trackSelectionTfHitPLess", f"{_HIT_DNN_DATA}/MkFitPixelLessOnlyHit_Run3_2024.pb"),
}

# iteration classifier -> (graph group, qualityCuts [loose, tight, highPurity]); each cut passes the same
# number of fake tracks as the production TrackTfClassifier cut on the validation sample
HIT_DNN_CUTS = {
    "initialStep": ("MkFit", [-0.5776, -0.1255, 0.0747]),
    "highPtTripletStep": ("MkFit", [0.3192, 0.3992, 0.4739]),
    "detachedQuadStep": ("MkFit", [-0.8789, -0.5055, 0.1301]),
    "detachedTripletStep": ("MkFit", [-0.7844, -0.2712, 0.5898]),
    "pixelPairStep": ("MkFit", [-0.5739, -0.4365, -0.1857]),
    "mixedTripletStep": ("MkFit", [-0.9510, -0.8659, -0.6909]),
    "tobTecStep": ("MkFit", [-0.9263, -0.8876, -0.8496]),
    "lowPtQuadStep": ("CKF", [-0.6446, -0.2177, 0.0445]),
    "lowPtTripletStep": ("CKF", [-0.5243, -0.1422, 0.1940]),
    "pixelLessStep": ("MkFitPixelLessOnly", [-0.9332, -0.8962, -0.7832]),
}


def _addHitGraphs(process):
    """the graphs are added only with trackingLowPtRun3, so that other jobs do not need their files"""
    for label, graph in HIT_DNN_GRAPHS.values():
        setattr(process, label, _tfGraphDefProducer.clone(ComponentName=label, FileName=graph))


trackingLowPtRun3HitGraphs = trackingLowPtRun3.makeProcessModifier(_addHitGraphs)


def trackHitTfSettings(iteration):
    """TrackTfClassifier parameters for the cluster-level DNN of an iteration, to be used with toModify"""
    group, cuts = HIT_DNN_CUTS[iteration]
    return dict(mva=dict(tfDnnLabel=HIT_DNN_GRAPHS[group][0], useClusterFeatures=True), qualityCuts=cuts)
