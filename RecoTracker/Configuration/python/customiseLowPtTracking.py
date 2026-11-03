"""Improved low-pT and displaced-track reconstruction for Run 3 (2024/2025 conditions).

Every iteration keeps its default algorithm (mkFit or CKF); only the track selection, the seeding regions
and one mkFit parameter are changed:
  - track-selection DNN with 10 extra hit-level inputs (TrackHitTfClassifier), working points at the
    production fake rate
  - seeding regions open to lower pT (lowPtQuad, lowPtTriplet, pixelPair, detached, pixelLess, tobTec) and
    to displaced tracks (pixelPair, detached, mixedTriplet, pixelLess)
  - one more hole allowed per candidate in pixelLessStep (mkFit)

Usage with cmsDriver:
  --customise RecoTracker/Configuration/customiseLowPtTracking.customiseLowPtTracking

The hit-level DNNs were trained on 2024 TTbar PU MC; data files come from cms-data
(RecoTracker-FinalTrackSelectors, RecoTracker-MkFit); the training recipe is in
RecoTracker/FinalTrackSelectors/test/trackHitDNN/README.md.
"""
import FWCore.ParameterSet.Config as cms

_HIT_DNN_DATA = "RecoTracker/FinalTrackSelectors/data/TrackTfClassifier"  # cms-data RecoTracker-FinalTrackSelectors

# graph group -> (ES label, frozen graph)
HIT_DNN_GRAPHS = {
    "MkFit": ("trackSelectionTfHit", f"{_HIT_DNN_DATA}/MkFitHit_Run3_2024.pb"),
    "CKF": ("trackSelectionTfHitCKF", f"{_HIT_DNN_DATA}/CKFHit_Run3_2024.pb"),
    "MkFitPixelLessOnly": ("trackSelectionTfHitPLess", f"{_HIT_DNN_DATA}/MkFitPixelLessOnlyHit_Run3_2024.pb"),
}

# iteration classifier -> (graph group, qualityCuts [loose, tight, highPurity])
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

# seeding region -> {RegionPSet parameter: value}; Run 3 defaults in the comments
SEEDING_REGIONS = {
    "lowPtQuadStepTrackingRegions": {"ptMin": 0.1},                              # 0.15
    "lowPtTripletStepTrackingRegions": {"ptMin": 0.1},                           # 0.2
    "pixelPairStepTrackingRegions": {"ptMin": 0.4, "originRadius": 0.1},         # 0.6, 0.015
    "pixelPairStepTrackingRegionsSeedLayersB": {"ptMin": 0.4, "originRadius": 0.1},  # 0.6, 0.015
    "detachedQuadStepTrackingRegions": {"ptMin": 0.25, "originRadius": 2.5},     # 0.3, 1.5
    "detachedTripletStepTrackingRegions": {"ptMin": 0.2, "originRadius": 2.5},   # 0.25, 1.5
    "mixedTripletStepTrackingRegionsA": {"ptMin": 0.3, "originRadius": 2.5},     # 0.4, 1.5
    "mixedTripletStepTrackingRegionsB": {"ptMin": 0.45, "originRadius": 2.5},    # 0.6, 1.5
    "pixelLessStepTrackingRegions": {"ptMin": 0.3, "originRadius": 2.0},         # 0.4, 1.0
    "tobTecStepTrackingRegionsTripl": {"ptMin": 0.45},                           # 0.55
    "tobTecStepTrackingRegionsPair": {"ptMin": 0.5},                             # 0.6
}
DETACHED_TRIPLET_CA_HARD_PT_CUT = 0.0  # GeV, default 0.2

# mkFit pixelLessStep configuration with maxHolesPerCand + 1 (cms-data RecoTracker-MkFit)
PIXEL_LESS_MKFIT_CONFIG = "RecoTracker/MkFit/data/mkfit-phase1-pixelLessStep-lowPt.json"


def customiseHitDNNSelection(process):
    """Replace the TrackTfClassifier of every iteration with TrackHitTfClassifier and the hit-level DNNs."""
    from PhysicsTools.TensorFlow.tfGraphDefProducer_cfi import tfGraphDefProducer

    for label, graph in HIT_DNN_GRAPHS.values():
        setattr(process, label, tfGraphDefProducer.clone(ComponentName=label, FileName=cms.FileInPath(graph)))

    for iteration, (group, cuts) in HIT_DNN_CUTS.items():
        if not hasattr(process, iteration):
            continue
        classifier = getattr(process, iteration)
        if classifier.type_() != "TrackTfClassifier":
            raise RuntimeError(f"{iteration} is a {classifier.type_()}, expected TrackTfClassifier")
        replacement = cms.EDProducer("TrackHitTfClassifier", **classifier.parameters_())
        replacement.mva.tfDnnLabel = HIT_DNN_GRAPHS[group][0]
        replacement.qualityCuts = cms.vdouble(cuts)
        setattr(process, iteration, replacement)
    return process


def customiseLowPtSeeding(process):
    """Seeding regions open to lower-pT and displaced tracks, one more hole in pixelLessStep."""
    for region, parameters in SEEDING_REGIONS.items():
        region_pset = getattr(process, region).RegionPSet
        for name, value in parameters.items():
            setattr(region_pset, name, value)
    process.detachedTripletStepHitTriplets.CAHardPtCut = DETACHED_TRIPLET_CA_HARD_PT_CUT
    process.pixelLessStepTrackCandidatesMkFitConfig.config = cms.FileInPath(PIXEL_LESS_MKFIT_CONFIG)
    return process


def customiseLowPtTracking(process):
    process = customiseHitDNNSelection(process)
    return customiseLowPtSeeding(process)
