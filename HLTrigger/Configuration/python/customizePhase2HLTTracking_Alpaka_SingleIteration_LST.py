import FWCore.ParameterSet.Config as cms

def customizePhase2HLTMkFitInitialStepTracks(process):
    
    sequence_found = any(
    "hltInitialStepSeeds" in str(path) for path in process.paths.values()
    )

    if not sequence_found:
        print("[WARNING] hltInitialStepSequence non available in any path presente. Skipping customizer...")
        return process

    process.mkFitSiPixelHits = cms.EDProducer("MkFitSiPixelHitConverter",
        hits = cms.InputTag("hltSiPixelRecHits"),
        clusters = cms.InputTag("hltSiPixelClusters"),
        mightGet = cms.optional.untracked.vstring,
        ttrhBuilder = cms.ESInputTag("","WithTrackAngle")
    )

    process.mkFitSiStripHits = cms.EDProducer("MkFitSiStripHitConverter",
        mightGet = cms.optional.untracked.vstring,
        minGoodStripCharge = cms.PSet(
            refToPSet_ = cms.string('SiStripClusterChargeCutLoose')
        ),
        rphiHits = cms.InputTag("siStripMatchedRecHits","rphiRecHit"),
        stereoHits = cms.InputTag("siStripMatchedRecHits","stereoRecHit"),
        ttrhBuilder = cms.ESInputTag("","WithTrackAngle")
    )

    process.mkFitSiPhase2Hits = cms.EDProducer("MkFitPhase2HitConverter",
        mightGet = cms.optional.untracked.vstring,
        hits = cms.InputTag("hltSiPhase2RecHits"),
        clusters = cms.InputTag("hltSiPhase2Clusters"),
        ttrhBuilder = cms.ESInputTag("","WithTrackAngle")
    )

    process.mkFitEventOfHits = cms.EDProducer("MkFitEventOfHitsProducer",
        beamSpot = cms.InputTag("offlineBeamSpot"),
        mightGet = cms.optional.untracked.vstring,
        pixelHits = cms.InputTag("mkFitSiPixelHits"),
        stripHits = cms.InputTag("mkFitSiPhase2Hits"),
        usePixelQualityDB = cms.bool(True),
        useStripStripQualityDB = cms.bool(False)
    )

    process.mkFitGeometryESProducer = cms.ESProducer("MkFitGeometryESProducer",
        appendToDataLabel = cms.string('')
    )

    process.hltInitialStepTrackCandidatesMkFitConfig = cms.ESProducer("MkFitIterationConfigESProducer",
        ComponentName = cms.string('hltInitialStepTrackCandidatesMkFitConfig'),
        appendToDataLabel = cms.string(''),
        config = cms.FileInPath('RecoTracker/MkFit/data/mkfit-phase2-initialStep.json'),
        maxClusterSize = cms.uint32(8),
        minPt = cms.double(0.9)
    )

    process.hltInitialStepTrackCandidatesMkFitSeeds = cms.EDProducer("MkFitSeedConverter",
        maxNSeeds = cms.uint32(500000),
        mightGet = cms.optional.untracked.vstring,
        seeds = cms.InputTag("hltInitialStepTrajectorySeedsLST"),
        ttrhBuilder = cms.ESInputTag("","WithTrackAngle")
    )

    process.hltInitialStepTrackCandidatesMkFit = cms.EDProducer("MkFitProducer",
        backwardFitInCMSSW = cms.bool(False),
        buildingRoutine = cms.string('cloneEngine'),
        clustersToSkip = cms.InputTag(""),
        config = cms.ESInputTag("","hltInitialStepTrackCandidatesMkFitConfig"),
        eventOfHits = cms.InputTag("mkFitEventOfHits"),
        limitConcurrency = cms.untracked.bool(False),
        mightGet = cms.optional.untracked.vstring,
        minGoodStripCharge = cms.PSet(
            refToPSet_ = cms.string('SiStripClusterChargeCutLoose')
        ),
        mkFitSilent = cms.untracked.bool(True),
        pixelHits = cms.InputTag("mkFitSiPixelHits"),
        removeDuplicates = cms.bool(True),
        seedCleaning = cms.bool(True),
        seeds = cms.InputTag("hltInitialStepTrackCandidatesMkFitSeeds"),
        stripHits = cms.InputTag("mkFitSiPhase2Hits")
    )

    process.hltInitialStepTrackCandidates = cms.EDProducer("MkFitOutputConverter",
        batchSize = cms.int32(16),
        candMVASel = cms.bool(False),
        candWP = cms.double(0),
        doErrorRescale = cms.bool(True),
        mightGet = cms.optional.untracked.vstring,
        mkFitEventOfHits = cms.InputTag("mkFitEventOfHits"),
        mkFitPixelHits = cms.InputTag("mkFitSiPixelHits"),
        mkFitSeeds = cms.InputTag("hltInitialStepTrackCandidatesMkFitSeeds"),
        mkFitStripHits = cms.InputTag("mkFitSiPhase2Hits"),
        propagatorAlong = cms.ESInputTag("","PropagatorWithMaterial"),
        propagatorOpposite = cms.ESInputTag("","PropagatorWithMaterialOpposite"),
        qualityMaxInvPt = cms.double(100),
        qualityMaxPosErr = cms.double(100),
        qualityMaxR = cms.double(120),
        qualityMaxZ = cms.double(280),
        qualityMinTheta = cms.double(0.01),
        qualitySignPt = cms.bool(True),
        seeds = cms.InputTag("hltInitialStepTrajectorySeedsLST"),
        tfDnnLabel = cms.string('trackSelectionTf'),
        tracks = cms.InputTag("hltInitialStepTrackCandidatesMkFit"),
        ttrhBuilder = cms.ESInputTag("","WithTrackAngle")
    )

    idx = process.HLTInitialStepSequence.index(process.hltInitialStepTrajectorySeedsLST)

    modules = [
    process.mkFitSiPixelHits,
    process.mkFitSiPhase2Hits,
    process.mkFitEventOfHits,
    process.hltInitialStepTrackCandidatesMkFitSeeds,
    process.hltInitialStepTrackCandidatesMkFit,
    ]

    for i, m in enumerate(modules):
        process.HLTInitialStepSequence.insert(idx + 1 + i, m)

    #process.hltGeneralTracks.TrackProducers = cms.VInputTag("hltInitialStepTrackSelectionHighPurity")
    return process


