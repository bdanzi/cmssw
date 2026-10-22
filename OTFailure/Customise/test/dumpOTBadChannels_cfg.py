# usage: cmsRun dumpOTBadChannels_cfg.py <fracS> <fracP> <output.txt>   (same ESSource and seed as the v5 runs)
import sys
import FWCore.ParameterSet.Config as cms
from Configuration.Eras.Era_Phase2C22I13M9_cff import Phase2C22I13M9
fs, fp, out = float(sys.argv[-3]), float(sys.argv[-2]), sys.argv[-1]
process = cms.Process("DUMPBAD", Phase2C22I13M9)
process.load("Configuration.Geometry.GeometryExtendedRun4D121Reco_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, "auto:phase2_realistic_T35", "")
process.SiPhase2OTFakeBadStripsESSource = cms.ESSource("SiPhase2BadStripConfigurableFakeESSource",
    seed = cms.uint32(1), badComponentsFraction = cms.double(fs), badComponentsFractionPSP = cms.double(fp), deadDetIds = cms.vuint32())
process.es_prefer_bad = cms.ESPrefer("SiPhase2BadStripConfigurableFakeESSource", "SiPhase2OTFakeBadStripsESSource")
process.source = cms.Source("EmptySource")
process.maxEvents = cms.untracked.PSet(input = cms.untracked.int32(1))
process.dump = cms.EDAnalyzer("OTBadChannelDumper", output = cms.string(out))
process.p = cms.Path(process.dump)
