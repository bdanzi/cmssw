# Auto generated configuration file
# using: 
# Revision: 1.19 
# Source: /local/reps/CMSSW/CMSSW/Configuration/Applications/python/ConfigBuilder.py,v 
# with command line options: step3 -s RAW2DIGI,RECO:reconstruction_trackingOnly,VALIDATION:@trackingOnlyValidation,DQM:@trackingOnlyDQM --conditions auto:phase2_realistic_T33 --datatier GEN-SIM-RECO,DQMIO -n 10 --eventcontent RECOSIM,DQM --geometry ExtendedRun4D110 --era Phase2C17I13M9 --accelerators cpu --filein file:step2.root --fileout file:step3.root
import FWCore.ParameterSet.Config as cms

from Configuration.Eras.Era_Phase2C17I13M9_cff import Phase2C17I13M9

process = cms.Process('RECO',Phase2C17I13M9)

# import of standard configurations
process.load('Configuration.StandardSequences.Services_cff')
process.load('SimGeneral.HepPDTESSource.pythiapdt_cfi')
process.load('FWCore.MessageService.MessageLogger_cfi')
process.load('Configuration.EventContent.EventContent_cff')
process.load('SimGeneral.MixingModule.mixNoPU_cfi')
process.load('Configuration.Geometry.GeometryExtendedRun4D110Reco_cff')
process.load('Configuration.StandardSequences.MagneticField_cff')
process.load('Configuration.StandardSequences.RawToDigi_cff')
process.load('Configuration.StandardSequences.Reconstruction_cff')
process.load('Configuration.StandardSequences.Validation_cff')
process.load('DQMServices.Core.DQMStoreNonLegacy_cff')
process.load('DQMOffline.Configuration.DQMOfflineMC_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(10),
    output = cms.optional.untracked.allowed(cms.int32,cms.PSet)
)

# Input source
process.source = cms.Source("PoolSource",
    fileNames = cms.untracked.vstring('file:step2.root'),
    secondaryFileNames = cms.untracked.vstring()
)

process.options = cms.untracked.PSet(
    IgnoreCompletely = cms.untracked.vstring(),
    Rethrow = cms.untracked.vstring(),
    TryToContinue = cms.untracked.vstring(),
    accelerators = cms.untracked.vstring('*'),
    allowUnscheduled = cms.obsolete.untracked.bool,
    canDeleteEarly = cms.untracked.vstring(),
    deleteNonConsumedUnscheduledModules = cms.untracked.bool(True),
    dumpOptions = cms.untracked.bool(False),
    emptyRunLumiMode = cms.obsolete.untracked.string,
    eventSetup = cms.untracked.PSet(
        forceNumberOfConcurrentIOVs = cms.untracked.PSet(
            allowAnyLabel_=cms.required.untracked.uint32
        ),
        numberOfConcurrentIOVs = cms.untracked.uint32(0)
    ),
    fileMode = cms.untracked.string('FULLMERGE'),
    forceEventSetupCacheClearOnNewRun = cms.untracked.bool(False),
    holdsReferencesToDeleteEarly = cms.untracked.VPSet(),
    makeTriggerResults = cms.obsolete.untracked.bool,
    modulesToCallForTryToContinue = cms.untracked.vstring(),
    modulesToIgnoreForDeleteEarly = cms.untracked.vstring(),
    numberOfConcurrentLuminosityBlocks = cms.untracked.uint32(0),
    numberOfConcurrentRuns = cms.untracked.uint32(1),
    numberOfStreams = cms.untracked.uint32(0),
    numberOfThreads = cms.untracked.uint32(1),
    printDependencies = cms.untracked.bool(False),
    sizeOfStackForThreadsInKB = cms.optional.untracked.uint32,
    throwIfIllegalParameter = cms.untracked.bool(True),
    wantSummary = cms.untracked.bool(False)
)

# Production Info
process.configurationMetadata = cms.untracked.PSet(
    annotation = cms.untracked.string('step3 nevts:10'),
    name = cms.untracked.string('Applications'),
    version = cms.untracked.string('$Revision: 1.19 $')
)

# Output definition

process.RECOSIMoutput = cms.OutputModule("PoolOutputModule",
    dataset = cms.untracked.PSet(
        dataTier = cms.untracked.string('GEN-SIM-RECO'),
        filterName = cms.untracked.string('')
    ),
    fileName = cms.untracked.string('file:step3.root'),
    outputCommands = process.RECOSIMEventContent.outputCommands,
    splitLevel = cms.untracked.int32(0)
)

process.DQMoutput = cms.OutputModule("DQMRootOutputModule",
    dataset = cms.untracked.PSet(
        dataTier = cms.untracked.string('DQMIO'),
        filterName = cms.untracked.string('')
    ),
    fileName = cms.untracked.string('file:step3_inDQM_LSTSeeds.root'),
    outputCommands = process.DQMEventContent.outputCommands,
    splitLevel = cms.untracked.int32(0)
)

# Additional output definition

# Other statements
process.mix.playback = True
process.mix.digitizers = cms.PSet()
for a in process.aliases: delattr(process, a)
process.RandomNumberGeneratorService.restoreStateLabel=cms.untracked.string("randomEngineStateProducer")
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, 'auto:phase2_realistic_T33', '')

# Path and EndPath definitions
process.raw2digi_step = cms.Path(process.RawToDigi)
process.reconstruction_step = cms.Path(process.reconstruction_trackingOnly)
process.prevalidation_step = cms.Path(process.globalPrevalidationTrackingOnly)
process.validation_step = cms.EndPath(process.globalValidationTrackingOnly)
process.dqmoffline_step = cms.EndPath(process.DQMOfflineTracking)
process.dqmofflineOnPAT_step = cms.EndPath(process.PostDQMOffline)
process.RECOSIMoutput_step = cms.EndPath(process.RECOSIMoutput)
process.DQMoutput_step = cms.EndPath(process.DQMoutput)

# Schedule definition
process.schedule = cms.Schedule(process.raw2digi_step,process.reconstruction_step,process.prevalidation_step,process.validation_step,process.dqmoffline_step,process.dqmofflineOnPAT_step,process.RECOSIMoutput_step,process.DQMoutput_step)
from PhysicsTools.PatAlgos.tools.helpers import associatePatAlgosToolsTask
associatePatAlgosToolsTask(process)

# Enable only these accelerator backends
process.load('Configuration.StandardSequences.Accelerators_cff')
process.options.accelerators = ['cpu']

# customisation of the process.

# Automatic addition of the customisation function from SimGeneral.MixingModule.fullMixCustomize_cff
from SimGeneral.MixingModule.fullMixCustomize_cff import setCrossingFrameOn 

#call to customisation function setCrossingFrameOn imported from SimGeneral.MixingModule.fullMixCustomize_cff
process = setCrossingFrameOn(process)

# End of customisation functions


process.lstPixelSeedInputProducer = cms.EDProducer("LSTPixelSeedInputProducer",
    beamSpot = cms.InputTag("offlineBeamSpot"),
    mightGet = cms.optional.untracked.vstring,
    seedTracks = cms.VInputTag("lstInitialStepSeedTracks"),
    #ptCut = cms.double(0.5)
)
process.lstProducer = cms.EDProducer("LSTProducer@alpaka",
        alpaka = cms.untracked.PSet(
        backend = cms.untracked.string(''),
        synchronize = cms.optional.untracked.bool
    ),
        mightGet = cms.optional.untracked.vstring,
        nopLSDupClean = cms.bool(False),
        phase2OTHitsInput = cms.InputTag("lstPhase2OTHitsInputProducer"),
        pixelSeedInput = cms.InputTag("lstPixelSeedInputProducer"),
        ptCut = cms.double(0.6),
        ptCutLabel = cms.string('0.6'),
        tcpLSTriplets = cms.bool(False),
    verbose = cms.bool(False)
)

process.lstModulesDevESProducer = cms.ESProducer("LSTModulesDevESProducer@alpaka",
    alpaka = cms.untracked.PSet(
        backend = cms.untracked.string(''),
        synchronize = cms.optional.untracked.bool
    ),
    appendToDataLabel = cms.string(''),
    ptCutLabel = cms.string('0.6')
)
                                     
process.initialStepLSTSeeds = cms.EDProducer("LSTOutputConverter",
    SeedCreatorPSet = cms.PSet(
        ComponentName = cms.string('SeedFromConsecutiveHitsCreator'),
        MinOneOverPtError = cms.double(1),
        OriginTransverseErrorMultiplier = cms.double(1),
        SeedMomentumForBOFF = cms.double(5),
        TTRHBuilder = cms.string('WithTrackAngle'),
        forceKinematicWithRegionDirection = cms.bool(False),
        magneticField = cms.string(''),
        propagator = cms.string('PropagatorWithMaterial')
    ),
    includeNonpLSTSs = cms.bool(True),
    includeT5s = cms.bool(True),
    lstOutput = cms.InputTag("lstProducer"),
    lstPixelSeeds = cms.InputTag("lstPixelSeedInputProducer"),
    mightGet = cms.optional.untracked.vstring,
    phase2OTHits = cms.InputTag("lstPhase2OTHitsInputProducer"),
    propagatorAlong = cms.ESInputTag("","PropagatorWithMaterial"),
    propagatorOpposite = cms.ESInputTag("","PropagatorWithMaterialOpposite")
)

process.initialStepTrackCandidatesMkFitSeeds = cms.EDProducer("MkFitSeedConverter",
    maxNSeeds = cms.uint32(500000),
    mightGet = cms.optional.untracked.vstring,
    seeds = cms.InputTag("initialStepLSTSeeds"),
    ttrhBuilder = cms.ESInputTag("","WithTrackAngle")
)

process.initialStepTrackCandidates = cms.EDProducer("MkFitOutputConverter",
    batchSize = cms.int32(16),
    candMVASel = cms.bool(False),
    candWP = cms.double(0),
    doErrorRescale = cms.bool(True),
    mightGet = cms.optional.untracked.vstring,
    mkFitEventOfHits = cms.InputTag("mkFitEventOfHits"),
    mkFitPixelHits = cms.InputTag("mkFitSiPixelHits"),
    mkFitSeeds = cms.InputTag("initialStepTrackCandidatesMkFitSeeds"),
    mkFitStripHits = cms.InputTag("mkFitSiPhase2Hits"),
    propagatorAlong = cms.ESInputTag("","PropagatorWithMaterial"),
    propagatorOpposite = cms.ESInputTag("","PropagatorWithMaterialOpposite"),
    qualityMaxInvPt = cms.double(100),
    qualityMaxPosErr = cms.double(100),
    qualityMaxR = cms.double(120),
    qualityMaxZ = cms.double(280),
    qualityMinTheta = cms.double(0.01),
    qualitySignPt = cms.bool(True),
    seeds = cms.InputTag("initialStepLSTSeeds"),
    tfDnnLabel = cms.string('trackSelectionTf'),
    tracks = cms.InputTag("initialStepTrackCandidatesMkFit"),
    ttrhBuilder = cms.ESInputTag("","WithTrackAngle")
)


# Customisation from command line
process.InitialStepTask = cms.Task(process.caloJetsForTrkTask, process.firstStepPrimaryVertices, process.firstStepPrimaryVerticesUnsorted, process.initialStepHitDoublets, process.initialStepHitQuadruplets, process.initialStepSeedLayers, process.initialStepSeeds, process.initialStepSelector, 
process.initialStepLSTSeeds,  process.lstInitialStepSeedTracks, process.lstPhase2OTHitsInputProducer, process.lstPixelSeedInputProducer, process.lstProducerTask, process.siPhase2RecHits,
process.initialStepTrackCandidates, process.initialStepTrackCandidatesMkFit, process.initialStepTrackCandidatesMkFitConfig, process.initialStepTrackCandidatesMkFitSeeds, process.initialStepTrackRefsForJets, process.initialStepTrackingRegions, process.initialStepTracks, process.mkFitEventOfHits, process.mkFitGeometryESProducer, process.mkFitSiPhase2Hits, process.mkFitSiPixelHits, process.siPhase2RecHits)



process.TrackSeedMoninitialStep = cms.EDProducer("TrackingMonitor",
**dict(
    [
        ("AbsDxyBin" , cms.int32(120) ),
        ("AbsDxyMax" , cms.double(60.0) ),
        ("AbsDxyMin" , cms.double(0.0) ),
        ("AlgoName" , cms.string('initialStep') ),
        ("BSFolderName" , cms.string('Tracking/TrackParameters/BeamSpotParameters') ),
        ("BXlumiSetup" , cms.PSet(
        BXlumiBin = cms.int32(400),
        BXlumiMax = cms.double(6000),
        BXlumiMin = cms.double(2000),
        lumi = cms.InputTag("lumiProducer"),
        lumiScale = cms.double(6.37)
    ) ),
        ("Chi2Bin" , cms.int32(50) ),
        ("Chi2Max" , cms.double(199.5) ),
        ("Chi2Min" , cms.double(-0.5) ),
        ("Chi2NDFBin" , cms.int32(50) ),
        ("Chi2NDFMax" , cms.double(19.5) ),
        ("Chi2NDFMin" , cms.double(-0.5) ),
        ("Chi2ProbBin" , cms.int32(100) ),
        ("Chi2ProbMax" , cms.double(1.0) ),
        ("Chi2ProbMin" , cms.double(0.0) ),
        ("ClusterLabels" , cms.vstring('Pix') ),
        ("DxyBin" , cms.int32(100) ),
        ("DxyErrBin" , cms.int32(200) ),
        ("DxyErrMax" , cms.double(0.1) ),
        ("DxyMax" , cms.double(0.5) ),
        ("DxyMin" , cms.double(-0.5) ),
        ("Eta2DBin" , cms.int32(26) ),
        ("EtaBin" , cms.int32(46) ),
        ("EtaMax" , cms.double(4.5) ),
        ("EtaMin" , cms.double(-4.5) ),
        ("FolderName" , cms.string('Tracking/TrackParameters/generalTracks/SeedMon/initialStep') ),
        ("GoodPVtx" , cms.PSet(
        GoodPVtxBin = cms.int32(200),
        GoodPVtxMax = cms.double(200.0),
        GoodPVtxMin = cms.double(0.0)
    ) ),
        ("LSBin" , cms.int32(2000) ),
        ("LSMax" , cms.double(2000.0) ),
        ("LSMin" , cms.double(0) ),
        ("LUMIBin" , cms.int32(700) ),
        ("LUMIMax" , cms.double(70000.0) ),
        ("LUMIMin" , cms.double(200.0) ),
        ("LongDCABins" , cms.int32(100) ),
        ("LongDCAMax" , cms.double(8.0) ),
        ("LongDCAMin" , cms.double(-8.0) ),
        ("MVABin" , cms.int32(100) ),
        ("MVAMax" , cms.double(1) ),
        ("MVAMin" , cms.double(-1) ),
        ("MVAProducers" , cms.vstring(
        'initialStepClassifier1',
        'initialStepClassifier2'
    ) ),
        ("MeanHitBin" , cms.int32(30) ),
        ("MeanHitMax" , cms.double(29.5) ),
        ("MeanHitMin" , cms.double(-0.5) ),
        ("MeanLayBin" , cms.int32(25) ),
        ("MeanLayMax" , cms.double(24.5) ),
        ("MeanLayMin" , cms.double(-0.5) ),
        ("MeasurementState" , cms.string('ImpactPoint') ),
        ("NClusPxBin" , cms.int32(100) ),
        ("NClusPxMax" , cms.double(20000) ),
        ("NClusPxMin" , cms.double(-0.5) ),
        ("NClusStrBin" , cms.int32(500) ),
        ("NClusStrMax" , cms.double(199999.5) ),
        ("NClusStrMin" , cms.double(-0.5) ),
        ("NTrk2D" , cms.PSet(
        NTrk2DBin = cms.int32(50),
        NTrk2DMax = cms.double(1999.5),
        NTrk2DMin = cms.double(-0.5)
    ) ),
        ("NTrkPVtx" , cms.PSet(
        NTrkPVtxBin = cms.int32(100),
        NTrkPVtxMax = cms.double(100.0),
        NTrkPVtxMin = cms.double(0.0)
    ) ),
        ("PVBin" , cms.int32(125) ),
        ("PVFolderName" , cms.string('Tracking/PrimaryVertices') ),
        ("PVMax" , cms.double(249.5) ),
        ("PVMin" , cms.double(-0.5) ),
        ("PXBLayBin" , cms.int32(6) ),
        ("PXBLayMax" , cms.double(5.5) ),
        ("PXBLayMin" , cms.double(-0.5) ),
        ("PXFLayBin" , cms.int32(6) ),
        ("PXFLayMax" , cms.double(5.5) ),
        ("PXFLayMin" , cms.double(-0.5) ),
        ("Phi2DBin" , cms.int32(32) ),
        ("PhiBin" , cms.int32(32) ),
        ("PhiMax" , cms.double(3.141592654) ),
        ("PhiMin" , cms.double(-3.141592654) ),
        ("Quality" , cms.string('') ),
        ("RecHitBin" , cms.int32(40) ),
        ("RecHitMax" , cms.double(39.5) ),
        ("RecHitMin" , cms.double(-0.5) ),
        ("RecLayBin" , cms.int32(25) ),
        ("RecLayMax" , cms.double(24.5) ),
        ("RecLayMin" , cms.double(-0.5) ),
        ("RecLostBin" , cms.int32(10) ),
        ("RecLostMax" , cms.double(9.5) ),
        ("RecLostMin" , cms.double(-0.5) ),
        ("RegionCandidatePtBin" , cms.int32(100) ),
        ("RegionCandidatePtMax" , cms.double(1000) ),
        ("RegionCandidatePtMin" , cms.double(0) ),
        ("RegionCandidates" , cms.InputTag("") ),
        ("RegionProducer" , cms.InputTag("") ),
        ("RegionSeedingLayersProducer" , cms.InputTag("") ),
        ("RegionSizeBin" , cms.int32(20) ),
        ("RegionSizeMax" , cms.double(19.5) ),
        ("RegionSizeMin" , cms.double(-0.5) ),
        ("SeedCandBin" , cms.int32(20) ),
        ("SeedCandMax" , cms.double(19.5) ),
        ("SeedCandMin" , cms.double(-0.5) ),
        ("SeedDxyBin" , cms.int32(100) ),
        ("SeedDxyMax" , cms.double(0.5) ),
        ("SeedDxyMin" , cms.double(-0.5) ),
        ("SeedDzBin" , cms.int32(120) ),
        ("SeedDzMax" , cms.double(30.0) ),
        ("SeedDzMin" , cms.double(-30.0) ),
        ("SeedHitBin" , cms.int32(6) ),
        ("SeedHitMax" , cms.double(5.5) ),
        ("SeedHitMin" , cms.double(-0.5) ),
        ("SeedProducer" , cms.InputTag("initialStepLSTSeeds") ),
        ("SumPtPVtx" , cms.PSet(
        SumPtPVtxBin = cms.int32(100),
        SumPtPVtxMax = cms.double(500.0),
        SumPtPVtxMin = cms.double(0.0)
    ) ),
        ("TCDxyBin" , cms.int32(100) ),
        ("TCDxyMax" , cms.double(100.0) ),
        ("TCDxyMin" , cms.double(-100.0) ),
        ("TCDzBin" , cms.int32(100) ),
        ("TCDzMax" , cms.double(400.0) ),
        ("TCDzMin" , cms.double(-400.0) ),
        ("TCHitBin" , cms.int32(40) ),
        ("TCHitMax" , cms.double(39.5) ),
        ("TCHitMin" , cms.double(-0.5) ),
        ("TCProducer" , cms.InputTag("initialStepTrackCandidates") ),
        ("TCSizeBin" , cms.int32(200) ),
        ("TCSizeMax" , cms.double(999.5) ),
        ("TCSizeMin" , cms.double(-0.5) ),
        ("TECLayBin" , cms.int32(15) ),
        ("TECLayMax" , cms.double(14.5) ),
        ("TECLayMin" , cms.double(-0.5) ),
        ("TIBLayBin" , cms.int32(6) ),
        ("TIBLayMax" , cms.double(5.5) ),
        ("TIBLayMin" , cms.double(-0.5) ),
        ("TIDLayBin" , cms.int32(6) ),
        ("TIDLayMax" , cms.double(5.5) ),
        ("TIDLayMin" , cms.double(-0.5) ),
        ("TOBLayBin" , cms.int32(10) ),
        ("TOBLayMax" , cms.double(9.5) ),
        ("TOBLayMin" , cms.double(-0.5) ),
        ("TTRHBuilder" , cms.string('WithTrackAngle') ),
        ("ThetaBin" , cms.int32(32) ),
        ("ThetaMax" , cms.double(3.2) ),
        ("ThetaMin" , cms.double(0.0) ),
        ("TkSeedSizeBin" , cms.int32(100) ),
        ("TkSeedSizeMax" , cms.double(5000) ),
        ("TkSeedSizeMin" , cms.double(0) ),
        ("TkSizeBin" , cms.int32(100) ),
        ("TkSizeMax" , cms.double(99.5) ),
        ("TkSizeMin" , cms.double(-0.5) ),
        ("TrackPBin" , cms.int32(100) ),
        ("TrackPMax" , cms.double(100) ),
        ("TrackPMin" , cms.double(0) ),
        ("TrackProducer" , cms.InputTag("generalTracks") ),
        ("TrackProducerForMVA" , cms.InputTag("initialStepTracks") ),
        ("TrackPt2DBin" , cms.int32(100) ),
        ("TrackPtBin" , cms.int32(100) ),
        ("TrackPtMax" , cms.double(100) ),
        ("TrackPtMin" , cms.double(0.1) ),
        ("TrackPxBin" , cms.int32(50) ),
        ("TrackPxMax" , cms.double(50.0) ),
        ("TrackPxMin" , cms.double(-50.0) ),
        ("TrackPyBin" , cms.int32(50) ),
        ("TrackPyMax" , cms.double(50.0) ),
        ("TrackPyMin" , cms.double(-50.0) ),
        ("TrackPzBin" , cms.int32(50) ),
        ("TrackPzMax" , cms.double(50.0) ),
        ("TrackPzMin" , cms.double(-50.0) ),
        ("TrackQBin" , cms.int32(8) ),
        ("TrackQMax" , cms.double(2.5) ),
        ("TrackQMin" , cms.double(-2.5) ),
        ("TransDCABins" , cms.int32(100) ),
        ("TransDCAMax" , cms.double(8.0) ),
        ("TransDCAMin" , cms.double(-8.0) ),
        ("VXBin" , cms.int32(100) ),
        ("VXMax" , cms.double(0.5) ),
        ("VXMin" , cms.double(-0.5) ),
        ("VYBin" , cms.int32(100) ),
        ("VYMax" , cms.double(0.5) ),
        ("VYMin" , cms.double(-0.5) ),
        ("VZBin" , cms.int32(100) ),
        ("VZBinProf" , cms.int32(100) ),
        ("VZMax" , cms.double(30.0) ),
        ("VZMaxProf" , cms.double(0.2) ),
        ("VZMin" , cms.double(-30.0) ),
        ("VZMinProf" , cms.double(-0.2) ),
        ("VZ_PVMax" , cms.double(30.0) ),
        ("VZ_PVMin" , cms.double(-30.0) ),
        ("X0Bin" , cms.int32(100) ),
        ("X0Max" , cms.double(0.5) ),
        ("X0Min" , cms.double(-0.5) ),
        ("Y0Bin" , cms.int32(100) ),
        ("Y0Max" , cms.double(0.5) ),
        ("Y0Min" , cms.double(-0.5) ),
        ("Z0Bin" , cms.int32(120) ),
        ("Z0Max" , cms.double(60.0) ),
        ("Z0Min" , cms.double(-60.0) ),
        ("allTrackProducer" , cms.InputTag("generalTracks") ),
        ("beamSpot" , cms.InputTag("offlineBeamSpot") ),
        ("denCut" , cms.string(' pt >= 1 ') ),
        ("doAllPlots" , cms.bool(False) ),
        ("doAllTrackCandHistos" , cms.bool(False) ),
        ("doBeamSpotPlots" , cms.bool(False) ),
        ("doDCAPlots" , cms.bool(False) ),
        ("doDCAwrt000Plots" , cms.bool(False) ),
        ("doDCAwrtPVPlots" , cms.bool(False) ),
        ("doEffFromHitPatternVsBX" , cms.bool(False) ),
        ("doEffFromHitPatternVsLUMI" , cms.bool(False) ),
        ("doEffFromHitPatternVsPU" , cms.bool(False) ),
        ("doGeneralPropertiesPlots" , cms.bool(False) ),
        ("doHIPlots" , cms.bool(False) ),
        ("doHitPropertiesPlots" , cms.bool(False) ),
        ("doLayersVsPhiVsEtaPerTrack" , cms.bool(False) ),
    ] +
    [
        ("doLumiAnalysis" , cms.bool(False) ),
        ("doMVAPlots" , cms.bool(False) ),
        ("doMeasurementStatePlots" , cms.bool(False) ),
        ("doPUmonitoring" , cms.bool(False) ),
        ("doPlotsVsBX" , cms.bool(False) ),
        ("doPlotsVsBXlumi" , cms.bool(False) ),
        ("doPlotsVsGoodPVtx" , cms.bool(False) ),
        ("doPlotsVsLUMI" , cms.bool(False) ),
        ("doPrimaryVertexPlots" , cms.bool(False) ),
        ("doProfilesVsLS" , cms.bool(False) ),
        ("doRecHitVsPhiVsEtaPerTrack" , cms.bool(False) ),
        ("doRecHitVsPtVsEtaPerTrack" , cms.bool(False) ),
        ("doRecHitsPerTrackProfile" , cms.bool(False) ),
        ("doRegionCandidatePlots" , cms.bool(False) ),
        ("doRegionPlots" , cms.bool(False) ),
        ("doSIPPlots" , cms.bool(False) ),
        ("doSeedDxyHisto" , cms.bool(False) ),
        ("doSeedDzHisto" , cms.bool(False) ),
        ("doSeedETAHisto" , cms.bool(True) ),
        ("doSeedLumiAnalysis" , cms.bool(True) ),
        ("doSeedNRecHitsHisto" , cms.bool(False) ),
        ("doSeedNVsEtaProf" , cms.bool(False) ),
        ("doSeedNVsPhiProf" , cms.bool(False) ),
        ("doSeedNumberHisto" , cms.bool(True) ),
        ("doSeedPHIHisto" , cms.bool(True) ),
        ("doSeedPHIVsETAHisto" , cms.bool(True) ),
        ("doSeedPTHisto" , cms.bool(True) ),
        ("doSeedParameterHistos" , cms.bool(False) ),
        ("doSeedQHisto" , cms.bool(False) ),
        ("doSeedThetaHisto" , cms.bool(False) ),
        ("doSeedVsClusterHisto" , cms.bool(True) ),
        ("doStopSource" , cms.bool(True) ),
        ("doTestPlots" , cms.bool(False) ),
        ("doThetaPlots" , cms.bool(False) ),
        ("doTrackCandHistos" , cms.bool(True) ),
        ("doTrackPxPyPlots" , cms.bool(False) ),
        ("doTrackerSpecific" , cms.bool(False) ),
        ("etaErrBin" , cms.int32(50) ),
        ("etaErrMax" , cms.double(0.1) ),
        ("etaErrMin" , cms.double(0.0) ),
        ("forceSCAL" , cms.bool(False) ),
        ("genericTriggerEventPSet" , cms.PSet(

    ) ),
        ("metadata" , cms.InputTag("onlineMetaDataDigis") ),
        ("minNumberOfPixelsPerCluster" , cms.int32(2) ),
        ("minPixelClusterCharge" , cms.double(15000.0) ),
        ("numCut" , cms.string(" pt >= 1 & quality(\'highPurity\') ") ),
        ("pErrBin" , cms.int32(50) ),
        ("pErrMax" , cms.double(1.0) ),
        ("pErrMin" , cms.double(0.0) ),
        ("phiErrBin" , cms.int32(50) ),
        ("phiErrMax" , cms.double(0.1) ),
        ("phiErrMin" , cms.double(0.0) ),
        ("pixelCluster" , cms.InputTag("siPixelClusters") ),
        ("pixelCluster4lumi" , cms.InputTag("siPixelClustersPreSplitting") ),
        ("primaryVertex" , cms.InputTag("offlinePrimaryVertices") ),
        ("primaryVertexInputTags" , cms.VInputTag() ),
        ("ptErrBin" , cms.int32(50) ),
        ("ptErrMax" , cms.double(1.0) ),
        ("ptErrMin" , cms.double(0.0) ),
        ("pvLabels" , cms.vstring() ),
        ("pvNDOF" , cms.int32(4) ),
        ("pxErrBin" , cms.int32(50) ),
        ("pxErrMax" , cms.double(1.0) ),
        ("pxErrMin" , cms.double(0.0) ),
        ("pyErrBin" , cms.int32(50) ),
        ("pyErrMax" , cms.double(1.0) ),
        ("pyErrMin" , cms.double(0.0) ),
        ("pzErrBin" , cms.int32(50) ),
        ("pzErrMax" , cms.double(1.0) ),
        ("pzErrMin" , cms.double(0.0) ),
        ("qualityString" , cms.string('highPurity') ),
        ("scal" , cms.InputTag("scalersRawToDigi") ),
        ("selPrimaryVertexInputTags" , cms.VInputTag() ),
        ("stripCluster" , cms.InputTag("siStripClusters") ),
        ("subdetectorBin" , cms.int32(25) ),
        ("subdetectors" , cms.vstring(
        'TIB',
        'TOB',
        'TID',
        'TEC',
        'PixBarrel',
        'PixEndcap',
        'Pixel',
        'Strip'
    ) ),
        ("useBPixLayer1" , cms.bool(False) ),
        ]
    )
)
        

# Automatic addition of the customisation function from Validation.RecoTrack.customiseTrackingNtuple
from Validation.RecoTrack.customiseTrackingNtuple import customiseTrackingNtuple,extendedContent 
process = customiseTrackingNtuple(process)
#process.trackingNtuple.clusterMasks = []

#process.seedTracksinitialStepLSTSeeds = cms.EDProducer("TrackFromSeedProducer",
process.seedTracksinitialStepSeeds = cms.EDProducer("TrackFromSeedProducer",
    TTRHBuilder = cms.string('WithoutRefit'),
    beamSpot = cms.InputTag("offlineBeamSpot"),
    src = cms.InputTag("initialStepLSTSeeds")
)

#process.trackingNtuple.seedTracks = [
#        "seedTracksinitialStepLSTSeeds", "seedTrackshighPtTripletStepSeeds", "seedTrackslowPtQuadStepSeeds", "seedTrackslowPtTripletStepSeeds", "seedTracksdetachedQuadStepSeeds",
#        "seedTrackspixelPairStepSeeds", "seedTracksmuonSeededSeedsInOut", "seedTracksmuonSeededSeedsOutIn"
#]

#process.trackingNtuple.includeTrackCandidates = cms.untracked.bool(True)

#process.trackingNtupleSeedSelectors = cms.Task(process.seedTracksdetachedQuadStepSeeds, process.seedTrackshighPtTripletStepSeeds, process.seedTracksinitialStepSeeds, process.seedTracksinitialStepLSTSeeds, process.seedTrackslowPtQuadStepSeeds, process.seedTrackslowPtTripletStepSeeds, process.seedTracksmuonSeededSeedsInOut, process.seedTracksmuonSeededSeedsOutIn, process.seedTrackspixelPairStepSeeds)
#process.trackValidatorSeedingTrackingOnly.label = ["seedTracksinitialStepLSTSeeds", "seedTrackshighPtTripletStepSeeds", "seedTrackslowPtQuadStepSeeds", "seedTrackslowPtTripletStepSeeds", "seedTracksdetachedQuadStepSeeds",
#        "seedTrackspixelPairStepSeeds", "seedTracksmuonSeededSeedsInOut", "seedTracksmuonSeededSeedsOutIn"]


#process.tracksValidationSeedSelectorsTrackingOnly = cms.Task(process.seedTracksdetachedQuadStepSeeds, process.seedTrackshighPtTripletStepSeeds, process.seedTracksinitialStepLSTSeeds, process.seedTrackslowPtQuadStepSeeds, process.seedTrackslowPtTripletStepSeeds, process.seedTracksmuonSeededSeedsInOut, process.seedTracksmuonSeededSeedsOutIn, process.seedTrackspixelPairStepSeeds, process.tracksValidationSeedSelectorsPreSplittingTrackingOnly)

# Customisation from command line

#call to customisation function customiseTrackingNtuple imported from Validation.RecoTrack.customiseTrackingNtuple

#call to customisation function extendedContent imported from Validation.RecoTrack.customiseTrackingNtuple
process = extendedContent(process)

process.trackingNtuple.clusterMasks=[]

#Have logErrorHarvester wait for the same EDProducers to finish as those providing data for the OutputModule
from FWCore.Modules.logErrorHarvester_cff import customiseLogErrorHarvesterUsingOutputCommands
process = customiseLogErrorHarvesterUsingOutputCommands(process)

# Add early deletion of temporary data products to reduce peak memory need
from Configuration.StandardSequences.earlyDeleteSettings_cff import customiseEarlyDelete
process = customiseEarlyDelete(process)
# End adding early deletion
