import FWCore.ParameterSet.Config as cms

# Same era/geometry/conditions as SimTracker/TrackerMaterialAnalysis/test/runHLT_tt_currentGeometry_mkFitFit.py,
# so the mkFit-side TrackerInfo dumped here matches what that HLT job actually uses.
from Configuration.Eras.Era_Phase2C22I13M9_cff import Phase2C22I13M9
from Configuration.ProcessModifiers.trackingMkFitFit_cff import trackingMkFitFit

process = cms.Process('DUMP', Phase2C22I13M9, trackingMkFitFit)

# import of standard configurations
process.load('Configuration.StandardSequences.Services_cff')
process.load('FWCore.MessageService.MessageLogger_cfi')
process.load('Configuration.Geometry.GeometryExtendedRun4D121Reco_cff')
process.load('Configuration.StandardSequences.MagneticField_cff')
process.load('Configuration.StandardSequences.Reconstruction_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')

from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, 'auto:phase2_realistic_T35', '')

process.MessageLogger.cerr.threshold = "INFO"
process.MessageLogger.cerr.MkFitGeometryESProducer = dict(limit=-1)

process.source = cms.Source("EmptySource")
process.maxEvents.input = 1

process.add_(cms.ESProducer("MkFitGeometryESProducer"))

defaultOutputFileName = "phase2-D121-trackerinfo-current.bin"

# level: 0 - no printout; 1 - print layers, 2 - print shapes and modules
# outputFileName: binary dump file; no dump if empty string
process.dump = cms.EDAnalyzer("DumpMkFitGeometry",
                              level = cms.untracked.int32(2),
                              outputFileName = cms.untracked.string(defaultOutputFileName)
                              )

print("Requesting MkFit geometry dump into file:", defaultOutputFileName, "\n")
process.p = cms.Path(process.dump)
