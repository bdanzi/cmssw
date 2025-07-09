import FWCore.ParameterSet.Config as cms

def customizePhase2hltHighPtTripletStepTracks(process):
    
    sequence_found = any(
    "hltHighPtTripletStepSeeds" in str(path) for path in process.paths.values()
    )

    if not sequence_found:
        print("[WARNING] hltHighPtTripletStepSequence non available in any path presente. Skipping customizer...")
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

    process.hltHighPtTripletStepTrackCandidatesMkFitConfig = cms.ESProducer("MkFitIterationConfigESProducer",
        ComponentName = cms.string('hltHighPtTripletStepTrackCandidatesMkFitConfig'),
        appendToDataLabel = cms.string(''),
        config = cms.FileInPath('RecoTracker/MkFit/data/mkfit-phase2-initialStep.json'),
        maxClusterSize = cms.uint32(8),
        minPt = cms.double(0.9)
    )

    process.hltHighPtTripletStepTrackCandidatesMkFitSeeds = cms.EDProducer("MkFitSeedConverter",
        maxNSeeds = cms.uint32(500000),
        mightGet = cms.optional.untracked.vstring,
        seeds = cms.InputTag("hltHighPtTripletStepSeeds"),
        ttrhBuilder = cms.ESInputTag("","WithTrackAngle")
    )

    process.hltHighPtTripletStepTrackCandidatesMkFit = cms.EDProducer("MkFitProducer",
        backwardFitInCMSSW = cms.bool(False),
        buildingRoutine = cms.string('cloneEngine'),
        clustersToSkip = cms.InputTag(""),
        config = cms.ESInputTag("","hltHighPtTripletStepTrackCandidatesMkFitConfig"),
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
        seeds = cms.InputTag("hltHighPtTripletStepTrackCandidatesMkFitSeeds"),
        stripHits = cms.InputTag("mkFitSiPhase2Hits")
    )

    process.hltHighPtTripletStepTrackCandidates = cms.EDProducer("MkFitOutputConverter",
        batchSize = cms.int32(16),
        candMVASel = cms.bool(False),
        candWP = cms.double(0),
        doErrorRescale = cms.bool(True),
        mightGet = cms.optional.untracked.vstring,
        mkFitEventOfHits = cms.InputTag("mkFitEventOfHits"),
        mkFitPixelHits = cms.InputTag("mkFitSiPixelHits"),
        mkFitSeeds = cms.InputTag("hltHighPtTripletStepTrackCandidatesMkFitSeeds"),
        mkFitStripHits = cms.InputTag("mkFitSiPhase2Hits"),
        propagatorAlong = cms.ESInputTag("","PropagatorWithMaterial"),
        propagatorOpposite = cms.ESInputTag("","PropagatorWithMaterialOpposite"),
        qualityMaxInvPt = cms.double(100),
        qualityMaxPosErr = cms.double(100),
        qualityMaxR = cms.double(120),
        qualityMaxZ = cms.double(280),
        qualityMinTheta = cms.double(0.01),
        qualitySignPt = cms.bool(True),
        seeds = cms.InputTag("hltHighPtTripletStepSeeds"),
        tfDnnLabel = cms.string('trackSelectionTf'),
        tracks = cms.InputTag("hltHighPtTripletStepTrackCandidatesMkFit"),
        ttrhBuilder = cms.ESInputTag("","WithTrackAngle")
    )

    process.HLTHighPtTripletStepSequence= cms.Sequence(process.hltHighPtTripletStepSeeds+process.mkFitSiPixelHits+process.mkFitSiPhase2Hits+process.mkFitEventOfHits+process.hltHighPtTripletStepTrackCandidatesMkFitSeeds+process.hltHighPtTripletStepTrackCandidatesMkFit+process.hltHighPtTripletStepTrackCandidates+process.hltHighPtTripletStepTracks+process.hltHighPtTripletStepTrackCutClassifier+process.hltHighPtTripletStepTrackSelectionHighPurity)


#    process.HLTItLocalRecoSequence = cms.Sequence(process.hltSiPhase2Clusters+process.hltSiPhase2RecHits+process.hltSiPixelClusters+process.hltSiPixelClusterShapeCache+process.hltSiPixelRecHits)

    return process


