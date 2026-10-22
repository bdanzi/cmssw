import FWCore.ParameterSet.Config as cms
#
# HLT-step customisation: make the reconstruction aware of the dead modules of a failure scenario, reading the same
# SiPixelQuality payloads used by the digitizer (data/payloads/<Scenario>.db, cms-sw/cmssw#52130):
#  - OT: MeasurementTrackerEventProducer.phase2OTBadModulesFromDB (dead OT sensors inactive for CKF) and
#        MkFitEventOfHitsProducer.usePhase2OTBadModuleDB (dead OT modules as mkFit dead regions)   [patched code]
#  - IT: the IT payload is also served as SiPixelQualityRcd, already read by the MeasurementTracker
#        (UsePixelModuleQualityDB) and by mkFit (usePixelQualityDB)
# LST and the CA (pixel tracks) do not use this information.
#
from OTFailure.Customise.scenarioData import payloadConnect

def _aware(process, name, ot, it):
    toGet = []
    if ot:
        toGet.append(cms.PSet(record = cms.string("SiPhase2OuterTrackerBadModuleRcd"), tag = cms.string("OTBadModules")))
    if it:
        toGet.append(cms.PSet(record = cms.string("SiPhase2InnerTrackerBadModuleRcd"), tag = cms.string("ITBadModules")))
        toGet.append(cms.PSet(record = cms.string("SiPixelQualityRcd"), tag = cms.string("ITBadModules")))
    process.recoAwareBadModules = cms.ESSource("PoolDBESSource", connect = cms.string(payloadConnect(name)),
                                               toGet = cms.VPSet(*toGet))
    process.es_prefer_recoAwareBadModules = cms.ESPrefer("PoolDBESSource", "recoAwareBadModules")
    nmte = nmkf = 0
    for label, mod in process.producers_().items():
        if mod.type_() == "MeasurementTrackerEventProducer" and ot:
            mod.phase2OTBadModulesFromDB = cms.bool(True); nmte += 1
        if mod.type_() == "MkFitEventOfHitsProducer":
            if ot: mod.usePhase2OTBadModuleDB = cms.bool(True)
            if it: mod.usePixelQualityDB = cms.bool(True)
            nmkf += 1
    for label, es in process.es_producers_().items():
        if es.type_() == "MeasurementTrackerESProducer" and it:
            es.UsePixelModuleQualityDB = cms.bool(True)
            es.UsePixelROCQualityDB = cms.bool(False)   # whole modules only (no cabling map in Phase-2)
    print("# RecoAware: %s (OT %s, IT %s): %d MeasurementTrackerEvent, %d mkFit producers configured" % (name, ot, it, nmte, nmkf))
    return process

def customiseRecoAwareBaseline(process):           return process
def customiseRecoAwareStefanExample(process):      return _aware(process, "StefanExample", True, True)
def customiseRecoAwareDeadModules1Pct(process):    return _aware(process, "DeadModules1Pct", True, False)
def customiseRecoAwareDeadModules5Pct(process):    return _aware(process, "DeadModules5Pct", True, False)
def customiseRecoAwareDeadModules10Pct(process):   return _aware(process, "DeadModules10Pct", True, False)
def customiseRecoAwareDeadPhiSector(process):      return _aware(process, "DeadPhiSector", True, False)
def customiseRecoAwareDeadLayerTBPS1(process):     return _aware(process, "DeadLayerTBPS1", True, False)
def customiseRecoAwareDeadLayerTBPS2(process):     return _aware(process, "DeadLayerTBPS2", True, False)
def customiseRecoAwareDeadITModules1Pct(process):  return _aware(process, "DeadITModules1Pct", False, True)
def customiseRecoAwareDeadITModules5Pct(process):  return _aware(process, "DeadITModules5Pct", False, True)
