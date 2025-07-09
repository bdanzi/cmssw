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
    process.hltHighPtTripletStepSeedTracks = cms.EDProducer(
        "TrackFromSeedProducer",
     src = cms.InputTag("hltHighPtTripletStepSeeds"),
     beamSpot = cms.InputTag("hltOnlineBeamSpot"),
     TTRHBuilder = cms.string("hltESPTTRHBuilderWithoutRefit")
    )
    process.hltInitialStepSeedTracks = cms.EDProducer(
        "TrackFromSeedProducer",
        src = cms.InputTag("hltInitialStepSeeds"),
        beamSpot = cms.InputTag("hltOnlineBeamSpot"),
        TTRHBuilder = cms.string("hltESPTTRHBuilderWithoutRefit")
    )
    
    if hasattr(process, "HLTHighPtTripletStepSequence"):
        process.HLTHighPtTripletStepSequence += (
        process.hltHighPtTripletStepSeedTracks
    )

    if hasattr(process, "HLTInitialStepSequence"):
        process.HLTInitialStepSequence += (
        process.hltInitialStepSeedTracks
    )
    return process


def customizePhase2hltHighPtTripletStepTracks(process):
    if not hasattr(process, 'hltInitialStepTrackCandidates'):
        print("Skipping unseeded event: hltInitialStepTrackCandidates not found")
        return process
    sequence_found = any(
        "hltInitialStepSeeds" in str(path) for path in process.paths.values()
    )
    if not sequence_found:
        print("[WARNING] hltHighPtTripletStepClusters non available in any path presente. Skipping customizer...")
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
        minPt = cms.double(0.5)
    )
    process.hltHighPtTripletStepTrackCandidatesMkFitSeeds = cms.EDProducer("MkFitSeedConverter",
        maxNSeeds = cms.uint32(500000),
        mightGet = cms.optional.untracked.vstring,
        seeds = cms.InputTag("hltInitialStepTrackCandidates", "", "HLTX"),
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

    process.hltHighPtTripletStepTrackCandidatespLSTCLST = cms.EDProducer("MkFitOutputConverter",
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
        seeds = cms.InputTag("hltInitialStepTrackCandidates", "", "HLTX"),
        tfDnnLabel = cms.string('trackSelectionTf'),
        tracks = cms.InputTag("hltHighPtTripletStepTrackCandidatesMkFit"),
        ttrhBuilder = cms.ESInputTag("","WithTrackAngle")
    )
    
    index = process.HLTHighPtTripletStepSequence.index(process.hltHighPtTripletStepTrackCandidatespLSTCLST)
    process.HLTHighPtTripletStepSequence.insert(index,process.mkFitSiPixelHits+process.mkFitSiPhase2Hits+process.mkFitEventOfHits+process.hltHighPtTripletStepTrackCandidatesMkFitSeeds+process.hltHighPtTripletStepTrackCandidatesMkFit)


    # MkFit as building in one iteration
    process.hltGeneralTracks = cms.EDProducer("TrackListMerger",
            Epsilon = cms.double(-0.001),
            FoundHitBonus = cms.double(5.0),
            LostHitPenalty = cms.double(5.0),
            MaxNormalizedChisq = cms.double(1000.0),
            MinFound = cms.int32(3),
            MinPT = cms.double(0.9),
            ShareFrac = cms.double(0.19),
            TrackProducers = cms.VInputTag("hltHighPtTripletStepTrackSelectionHighPuritypLSTCLST"),
            allowFirstHitShare = cms.bool(False),
            copyExtras = cms.untracked.bool(True),
            copyMVA = cms.bool(False),
            hasSelector = cms.vint32(0),
            indivShareFrac = cms.vdouble(0.1),
            makeReKeyedSeeds = cms.untracked.bool(False),
            newQuality = cms.string('confirmed'),
            selectedTrackQuals = cms.VInputTag("hltHighPtTripletStepTrackSelectionHighPuritypLSTCLST"),
            setsToMerge = cms.VPSet(cms.PSet(
                pQual = cms.bool(True),
                tLists = cms.vint32(0)
            )),
            trackAlgoPriorityOrder = cms.string('trackAlgoPriorityOrder'),
            writeOnlyTrkQuals = cms.bool(False)
    )
    return process


    

