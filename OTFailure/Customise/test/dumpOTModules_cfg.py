import FWCore.ParameterSet.Config as cms
from Configuration.Eras.Era_Phase2C22I13M9_cff import Phase2C22I13M9
process = cms.Process("DUMP", Phase2C22I13M9)
process.load("Configuration.Geometry.GeometryExtendedRun4D121Reco_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, "auto:phase2_realistic_T35", "")
process.source = cms.Source("EmptySource")
process.maxEvents = cms.untracked.PSet(input = cms.untracked.int32(1))
process.dump = cms.EDAnalyzer("OTModuleDumper", output = cms.string("OTModules_D121.txt"))
process.p = cms.Path(process.dump)

import sys
if "IT" in sys.argv:
    process.dump.output = "ITModules_D121.txt"
    process.dump.dumpIT = cms.untracked.bool(True)
