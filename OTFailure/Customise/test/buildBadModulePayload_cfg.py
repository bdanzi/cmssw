# Build SiPixelQuality payloads (OT and/or IT bad modules) with SiPhase2BadModuleByHandBuilder (DigitizerExtensionForBadModules)
# usage: cmsRun build_cfg.py <ot_list|none> <it_list|none> <out.db>
import sys
import FWCore.ParameterSet.Config as cms
ot, it, out = sys.argv[-3], sys.argv[-2], sys.argv[-1]
process = cms.Process("WRITE")
process.load("Configuration.Geometry.GeometryExtendedRun4D121Reco_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, "auto:phase2_realistic_T35", "")
process.load("FWCore.MessageService.MessageLogger_cfi")
process.source = cms.Source("EmptyIOVSource", timetype = cms.string("runnumber"), firstValue = cms.uint64(1), lastValue = cms.uint64(1), interval = cms.uint64(1))
toPut = []; seq = []
for lst, rec, tag in ((ot, "SiPhase2OuterTrackerBadModuleRcd", "OTBadModules"), (it, "SiPhase2InnerTrackerBadModuleRcd", "ITBadModules")):
    if lst == "none": continue
    toPut.append(cms.PSet(record = cms.string(rec), tag = cms.string(tag)))
    m = cms.EDAnalyzer("SiPhase2BadModuleByHandBuilder", Record = cms.string(rec), SinceAppendMode = cms.bool(True), IOVMode = cms.string("Run"),
                       doStoreOnDB = cms.bool(True), badModuleListFile = cms.untracked.string(lst), targetRecord = cms.untracked.string(rec),
                       printDebug = cms.untracked.bool(False))
    setattr(process, "b" + tag, m); seq.append(m)
process.PoolDBOutputService = cms.Service("PoolDBOutputService", DBParameters = cms.PSet(authenticationPath = cms.untracked.string("")),
    connect = cms.string("sqlite_file:" + out), toPut = cms.VPSet(*toPut))
process.p = cms.Path(sum(seq[1:], seq[0]))
