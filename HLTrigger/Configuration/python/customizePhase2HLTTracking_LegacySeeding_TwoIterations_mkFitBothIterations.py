import FWCore.ParameterSet.Config as cms

def customizeSeedTracks(process):
    process.hltESPTTRHBuilderWithoutRefit = cms.ESProducer("TkTransientTrackingRecHitBuilderESProducer",
         ComponentName = cms.string('hltESPTTRHBuilderWithoutRefit'),
         ComputeCoarseLocalPositionFromDisk = cms.bool(False),
         Matcher = cms.string('Fake'),
         Phase2StripCPE = cms.string(''),
         PixelCPE = cms.string('Fake'),
         StripCPE = cms.string('Fake')
    )
    """
    process.hltHighPtTripletStepSeedTracks = cms.EDProducer(
        "TrackFromSeedProducer",
     src = cms.InputTag("hltHighPtTripletStepSeeds"),
     beamSpot = cms.InputTag("hltOnlineBeamSpot"),
     TTRHBuilder = cms.string("hltESPTTRHBuilderWithoutRefit")
    )
    """
    process.hltInitialStepSeedTracks = cms.EDProducer(
        "TrackFromSeedProducer",
        src = cms.InputTag("hltInitialStepSeeds"),
        beamSpot = cms.InputTag("hltOnlineBeamSpot"),
        TTRHBuilder = cms.string("hltESPTTRHBuilderWithoutRefit")
    )
    """
    if hasattr(process, "HLTHighPtTripletStepSequence"):
        process.HLTHighPtTripletStepSequence += (
        process.hltHighPtTripletStepSeedTracks
    )
    """
    if hasattr(process, "HLTInitialStepSequence"):
        process.HLTInitialStepSequence += (
        process.hltInitialStepSeedTracks
    )
    process.hltHighPtTripletStepClusters = cms.EDProducer("TrackClusterRemoverPhase2",
    TrackQuality = cms.string('highPurity'),
    maxChi2 = cms.double(9.0),
    mightGet = cms.optional.untracked.vstring,
    minNumberOfLayersWithMeasBeforeFiltering = cms.int32(0),
    oldClusterRemovalInfo = cms.InputTag(""),
    overrideTrkQuals = cms.InputTag(""),
    phase2OTClusters = cms.InputTag("hltSiPhase2Clusters"),
    phase2pixelClusters = cms.InputTag("hltSiPixelClusters"),
    trackClassifier = cms.InputTag("","QualityMasks"),
    trajectories = cms.InputTag("hltInitialStepSeedTracks")
    )
    return process

def customizePhase2HLTMkFitInitialStepTracks(process):
    
    sequence_found = any(
    "hltInitialStepSeeds" in str(path) for path in process.paths.values()
    )

    if not sequence_found:
        print("[WARNING] hltInitialStepSequence non available in any path presente. Skipping customizer...")
        return process
    if hasattr(process, "hltMkFitGeometryESProducer"):
        delattr(process, "hltMkFitGeometryESProducer")

    process.hltInitialStepSeeds = cms.EDProducer("SeedGeneratorFromProtoTracksEDProducer",
    InputCollection = cms.InputTag("hltPhase2PixelTracks"),
    InputVertexCollection = cms.InputTag(""),
    SeedCreatorPSet = cms.PSet(
        refToPSet_ = cms.string('seedFromProtoTracks')
    ),
    TTRHBuilder = cms.string('WithTrackAngle'),
    includeFourthHit = cms.bool(False),
    originHalfLength = cms.double(0.3),
    originRadius = cms.double(0.1),
    useEventsWithNoVertex = cms.bool(True),
    usePV = cms.bool(False),
    useProtoTrackKinematics = cms.bool(False)
    )
    
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

    import RecoTracker.MkFit.mkFitGeometryESProducer_cfi as mkFitGeometryESProducer_cfi
    process.load("RecoTracker.MkFit.mkFitGeometryESProducer_cfi")


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
        seeds = cms.InputTag("hltInitialStepSeeds"),
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
        candCutSel = cms.bool(True),
        candMinNHitsCut = cms.int32(3),
        candMinPtCut = cms.double(0.7),
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
        seeds = cms.InputTag("hltInitialStepSeeds"),
        tfDnnLabel = cms.string('trackSelectionTf'),
        tracks = cms.InputTag("hltInitialStepTrackCandidatesMkFit"),
        ttrhBuilder = cms.ESInputTag("","WithTrackAngle")
    )

    idx = process.HLTInitialStepSequence.index(process.hltInitialStepSeeds)

    modules = [
        process.mkFitSiPixelHits,
        process.mkFitSiPhase2Hits,
        process.mkFitEventOfHits,
        process.hltInitialStepTrackCandidatesMkFitSeeds,
        process.hltInitialStepTrackCandidatesMkFit,
    ]

    for i, m in enumerate(modules):
        process.HLTInitialStepSequence.insert(idx + 1 + i, m)
    idx = process.HLTItLocalRecoSequence.index(process.hltSiPhase2Clusters)
    modules = [
        process.hltSiPhase2RecHits
    ]
    for i, m in enumerate(modules):
        process.HLTItLocalRecoSequence.insert(idx + 1 + i, m)

    return process


def customizePhase2hltHighPtTripletStepTracks(process):
    
    sequence_found = any(
    "hltHighPtTripletStepSeeds" in str(path) for path in process.paths.values()
    )

    if not sequence_found:
        print("[WARNING] hltHighPtTripletStepSeeds non available in any path presente. Skipping customizer...")
        return process
    
    import RecoTracker.MkFit.mkFitGeometryESProducer_cfi as mkFitGeometryESProducer_cfi
    process.load("RecoTracker.MkFit.mkFitGeometryESProducer_cfi")
    process.hltHighPtTripletStepTrackCandidatesMkFitConfig = cms.ESProducer("MkFitIterationConfigESProducer",
        ComponentName = cms.string('hltHighPtTripletStepTrackCandidatesMkFitConfig'),
        appendToDataLabel = cms.string(''),
        config = cms.FileInPath('RecoTracker/MkFit/data/mkfit-phase2-highPtTripletStep.json'),
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
        clustersToSkip = cms.InputTag("hltHighPtTripletStepClusters"),
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
        candCutSel = cms.bool(True),
        candMinNHitsCut = cms.int32(4),
        candMinPtCut = cms.double(0.9),
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
    
    idx = process.HLTHighPtTripletStepSequence.index(process.HLTHighPtTripletStepSeedingSequence)
    modules = [
        process.hltHighPtTripletStepTrackCandidatesMkFitSeeds,
        process.hltHighPtTripletStepTrackCandidatesMkFit,
    ]

    for i, m in enumerate(modules):
        process.HLTHighPtTripletStepSequence.insert(idx + 1 + i, m)
        
    return process


