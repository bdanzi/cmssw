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

    process.hltGeneralTracks = cms.EDProducer("TrackListMerger",                                                                                     Epsilon = cms.double(-0.001),
      FoundHitBonus = cms.double(5.0),
      LostHitPenalty = cms.double(5.0),
      MaxNormalizedChisq = cms.double(1000.0),
      MinFound = cms.int32(3),
      MinPT = cms.double(0.9),
      ShareFrac = cms.double(0.19),                                                                                                            TrackProducers = cms.VInputTag("hltInitialStepTrackSelectionHighPuritypTTCLST", "hltInitialStepTrackSelectionHighPuritypLSTCLST", "hltInitialStepTracksT5TCLST"),
      allowFirstHitShare = cms.bool(False),
      copyExtras = cms.untracked.bool(True),
      copyMVA = cms.bool(False),
      hasSelector = cms.vint32(0,0,0),
      indivShareFrac = cms.vdouble(0.1,0.1,0.1),
      makeReKeyedSeeds = cms.untracked.bool(False),                                                                                
      newQuality = cms.string('confirmed'),                                                                                        
      selectedTrackQuals = cms.VInputTag("hltInitialStepTrackSelectionHighPuritypTTCLST", "hltInitialStepTrackSelectionHighPuritypLSTCLST", "hltInitialStepTracksT5TCLST"),                                  
            setsToMerge = cms.VPSet(cms.PSet(                                                                                            
                pQual = cms.bool(True),                                                                                                  
                tLists = cms.vint32(0,1,2)                                                                                                   
            )),                                                                                                                          
            trackAlgoPriorityOrder = cms.string('trackAlgoPriorityOrder'),                                                               
            writeOnlyTrkQuals = cms.bool(False)                                                                                           
    )
    
    process.HLTInitialStepSequence += (
        process.hltInitialStepTrackspLSTCLST+process.hltInitialStepTrackCutClassifierpLSTCLST+process.hltInitialStepTrackSelectionHighPuritypLSTCLST
    )
    return process


    

