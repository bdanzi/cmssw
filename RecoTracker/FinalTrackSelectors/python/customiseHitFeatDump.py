"""Add HitFeatDumper (training inputs of the cluster-level track-selection DNNs) to a step3 configuration that runs
the tracking validation (it needs quickTrackAssociatorByHits and the TrackingParticles of the mixing module).
Run it with --procModifiers trackingLowPtRun3, to train on the tracks the DNNs select. The stored "mva" is the score
of the production DNN on the same tracks (the working points are matched to it): with the modifier, a clone of the
classifier with the production graph is added for each iteration.

Usage:
  --customise RecoTracker/FinalTrackSelectors/customiseHitFeatDump.customiseHitFeatDump
"""
import FWCore.ParameterSet.Config as cms
from RecoTracker.FinalTrackSelectors.trackSelectionTfHit_cff import HIT_DNN_CUTS, HIT_DNN_GRAPHS

# the order defines the "iter" index stored in the tree (trainTrackHitDNN.py imports this list)
DUMPED_ITERATIONS = ["initialStep", "highPtTripletStep", "lowPtQuadStep", "lowPtTripletStep", "detachedQuadStep",
                     "detachedTripletStep", "pixelPairStep", "mixedTripletStep", "pixelLessStep", "tobTecStep",
                     "jetCoreRegionalStepBarrel", "jetCoreRegionalStepEndcap", "displacedRegionalStep"]


def _productionScore(process, iteration):
    """label of the classifier with the production DNN score of the iteration"""
    classifier = getattr(process, iteration)
    if iteration not in HIT_DNN_CUTS or not classifier.mva.getParameter("useClusterFeatures"):
        return iteration
    group = HIT_DNN_CUTS[iteration][0]
    label = iteration + "ProductionScore"
    setattr(process, label, classifier.clone(mva=dict(tfDnnLabel=HIT_DNN_GRAPHS[group][2], useClusterFeatures=False)))
    return label


def customiseHitFeatDump(process, fileName="hit_dump.root"):
    classifiers = [_productionScore(process, iteration) for iteration in DUMPED_ITERATIONS]
    process.hitFeatDumper = cms.EDAnalyzer("HitFeatDumper",
        tracks=cms.vstring([getattr(process, iteration).src.value() for iteration in DUMPED_ITERATIONS]),
        classifiers=cms.vstring(classifiers),
        beamspot=cms.InputTag("offlineBeamSpot"),
        vertices=cms.InputTag("firstStepPrimaryVertices"),
        trackingParticles=cms.InputTag("mix", "MergedTrackTruth"),
        associator=cms.InputTag("quickTrackAssociatorByHits"))
    process.TFileService = cms.Service("TFileService", fileName=cms.string(fileName))
    productionScores = cms.Task(*[getattr(process, label) for label in classifiers if label not in DUMPED_ITERATIONS])
    process.hitFeatDumpPath = cms.Path(process.hitFeatDumper, productionScores)
    process.schedule.append(process.hitFeatDumpPath)
    return process
