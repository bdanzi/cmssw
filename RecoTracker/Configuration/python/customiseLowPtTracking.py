"""Customisations for improved low-pT tracking in Run 3 (2024/2025 conditions).

Every iteration keeps its default algorithm (mkFit or CKF); only the track selection, seeding regions,
seeding layer sets and one mkFit parameter are changed.

  customiseHitDNNSelection       track-selection DNN with 10 extra hit-level inputs (TrackHitTfClassifier)
  customiseLowPtSeeding          pixelPair regions open to displaced tracks, lower-pT detached seeding,
                                 one more hole allowed in pixelLessStep (mkFit)
  customiseLowPtSeedingExtended  layer-skipping triplets in detachedTripletStep, pixel+TIB1 seeds in
                                 mixedTripletStep (~2x CPU of the standard reconstruction)

  customiseLowPtTrackingA = customiseHitDNNSelection + customiseLowPtSeeding
  customiseLowPtTrackingB = customiseLowPtTrackingA + customiseLowPtSeedingExtended

Usage with cmsDriver:
  --customise RecoTracker/Configuration/customiseLowPtTracking.customiseLowPtTrackingA

The hit-level DNNs were trained on 2024 TTbar PU MC; their working points give the same number of fake
tracks as the production DNN working points on that sample. Data files come from cms-data
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

# seeding regions
PIXEL_PAIR_ORIGIN_RADIUS = 0.1  # cm, default 0.015: keeps tracks from B/D decays and from inactive pixel areas
PIXEL_PAIR_INACTIVE_AREA_PT_MIN = 0.4  # GeV, default 0.6
DETACHED_QUAD_PT_MIN = 0.25  # GeV, default 0.3
DETACHED_TRIPLET_PT_MIN = 0.2  # GeV, default 0.25
DETACHED_TRIPLET_CA_HARD_PT_CUT = 0.0  # GeV, default 0.2

# mkFit pixelLessStep configuration with maxHolesPerCand + 1 (cms-data RecoTracker-MkFit)
PIXEL_LESS_MKFIT_CONFIG = "RecoTracker/MkFit/data/mkfit-phase1-pixelLessStep-lowPt.json"

# extra pixel + TIB1 seeding layer sets for mixedTripletStep (B), used when the outer pixel layers are missing
MIXED_TRIPLET_B_LAYERS = ["BPix3+BPix4+TIB1", "BPix2+BPix3+TIB1", "BPix2+BPix4+TIB1", "BPix1+BPix2+TIB1", "BPix1+BPix3+TIB1"]


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
    """Seeding regions open to displaced and low-pT tracks, one more hole in pixelLessStep."""
    process.pixelPairStepTrackingRegions.RegionPSet.originRadius = PIXEL_PAIR_ORIGIN_RADIUS
    inactive_area_regions = process.pixelPairStepTrackingRegionsSeedLayersB.RegionPSet
    inactive_area_regions.originRadius = PIXEL_PAIR_ORIGIN_RADIUS
    inactive_area_regions.ptMin = PIXEL_PAIR_INACTIVE_AREA_PT_MIN

    process.detachedQuadStepTrackingRegions.RegionPSet.ptMin = DETACHED_QUAD_PT_MIN
    process.detachedTripletStepTrackingRegions.RegionPSet.ptMin = DETACHED_TRIPLET_PT_MIN
    process.detachedTripletStepHitTriplets.CAHardPtCut = DETACHED_TRIPLET_CA_HARD_PT_CUT

    process.pixelLessStepTrackCandidatesMkFitConfig.config = cms.FileInPath(PIXEL_LESS_MKFIT_CONFIG)
    return process


def customiseLowPtSeedingExtended(process):
    """Layer-skipping triplets in detachedTripletStep and pixel+TIB1 seeds in mixedTripletStep."""
    process.detachedTripletStepSeedLayers.layerList = cms.vstring(*process.lowPtTripletStepSeedLayers.layerList)
    process.mixedTripletStepSeedLayersB.layerList = cms.vstring(*MIXED_TRIPLET_B_LAYERS)
    return process


def customiseLowPtTrackingA(process):
    process = customiseHitDNNSelection(process)
    return customiseLowPtSeeding(process)


def customiseLowPtTrackingB(process):
    process = customiseLowPtTrackingA(process)
    return customiseLowPtSeedingExtended(process)
