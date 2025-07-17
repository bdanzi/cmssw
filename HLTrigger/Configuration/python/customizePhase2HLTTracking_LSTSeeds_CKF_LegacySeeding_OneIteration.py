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
    import RecoTracker.MkFit.mkFitGeometryESProducer_cfi as mkFitGeometryESProducer_cfi
    process.load("RecoTracker.MkFit.mkFitGeometryESProducer_cfi")
    process.hltHighPtTripletStepTrackCandidatespLSTCLST = cms.EDProducer("CkfTrackCandidateMaker",
            MeasurementTrackerEvent = cms.InputTag("hltMeasurementTrackerEvent"),
            NavigationSchool = cms.string('SimpleNavigationSchool'),
            RedundantSeedCleaner = cms.string('CachingSeedCleanerBySharedInput'),
            TrajectoryBuilderPSet = cms.PSet(
                refToPSet_ = cms.string('highPtTripletStepTrajectoryBuilder')
            ),
            TrajectoryCleaner = cms.string('highPtTripletStepTrajectoryCleanerBySharedHits'),
            TransientInitialStateEstimatorParameters = cms.PSet(
            numberMeasurementsForFit = cms.int32(4),
            propagatorAlongTISE = cms.string('PropagatorWithMaterialParabolicMf'),
            propagatorOppositeTISE = cms.string('PropagatorWithMaterialParabolicMfOpposite')
            ),
            cleanTrajectoryAfterInOut = cms.bool(True),
            doSeedingRegionRebuilding = cms.bool(True),
            maxNSeeds = cms.uint32(100000),
            maxSeedsBeforeCleaning = cms.uint32(1000),
            numHitsForSeedCleaner = cms.int32(50),
            onlyPixelHitsForSeedCleaner = cms.bool(True),
    phase2clustersToSkip = cms.InputTag(""),
    reverseTrajectories = cms.bool(False),
    src = cms.InputTag("hltInitialStepTrackCandidates","AllSeeds"),
    useHitsSplitting = cms.bool(False)
)
    
    process.hltGeneralTracks = cms.EDProducer("TrackListMerger",
            Epsilon = cms.double(-0.001),
            FoundHitBonus = cms.double(5.0),
            LostHitPenalty = cms.double(5.0),
            MaxNormalizedChisq = cms.double(1000.0),
            MinFound = cms.int32(3),
            MinPT = cms.double(0.9),
            ShareFrac = cms.double(0.19),
            TrackProducers = cms.VInputTag("hltHighPtTripletStepTrackSelectionHighPuritypLSTCLST"),
            allowFirstHitShare = cms.bool(True),
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
    

