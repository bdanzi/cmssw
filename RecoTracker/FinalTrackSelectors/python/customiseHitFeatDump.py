"""Add HitFeatDumper (training inputs of the hit-level track-selection DNNs) to a step3 configuration that runs
the tracking validation (it needs quickTrackAssociatorByHits and the TrackingParticles of the mixing module).

Usage:
  --customise RecoTracker/FinalTrackSelectors/customiseHitFeatDump.customiseHitFeatDump
"""
import FWCore.ParameterSet.Config as cms

# the order defines the "iter" index stored in the tree; trainTrackHitDNN.py uses the same list
DUMPED_ITERATIONS = ["initialStep", "highPtTripletStep", "lowPtQuadStep", "lowPtTripletStep", "detachedQuadStep",
                     "detachedTripletStep", "pixelPairStep", "mixedTripletStep", "pixelLessStep", "tobTecStep",
                     "jetCoreRegionalStepBarrel", "jetCoreRegionalStepEndcap", "displacedRegionalStep"]


def customiseHitFeatDump(process, fileName="hit_dump.root"):
    process.hitFeatDumper = cms.EDAnalyzer("HitFeatDumper",
        tracks=cms.vstring([getattr(process, iteration).src.value() for iteration in DUMPED_ITERATIONS]),
        classifiers=cms.vstring(DUMPED_ITERATIONS),
        beamspot=cms.InputTag("offlineBeamSpot"),
        vertices=cms.InputTag("firstStepPrimaryVertices"),
        trackingParticles=cms.InputTag("mix", "MergedTrackTruth"),
        associator=cms.InputTag("quickTrackAssociatorByHits"))
    process.TFileService = cms.Service("TFileService", fileName=cms.string(fileName))
    process.hitFeatDumpPath = cms.Path(process.hitFeatDumper)
    process.schedule.append(process.hitFeatDumpPath)
    return process
