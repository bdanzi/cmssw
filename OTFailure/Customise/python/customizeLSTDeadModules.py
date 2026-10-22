import FWCore.ParameterSet.Config as cms
#
# HLT-step customisation: dead-aware LST module map (needs the LST dead-module patch on LSTModulesDevESProducer).
# The dead OT modules of a scenario (data/badModuleLists) are passed to LST as their lower/upper sensor detIds
# (module detId + 1, + 2); LST then connects the layer before a dead layer directly to the layer after it.
# Without this customisation deadModules is empty and the module map is the nominal one.
#
from OTFailure.Customise.scenarioData import badModuleList

def _lstDeadModules(process, scenario):
    dead = badModuleList(scenario)
    sensors = sorted(set([d + 1 for d in dead] + [d + 2 for d in dead]))
    for label, es in process.es_producers_().items():
        if es.type_().startswith("LSTModulesDevESProducer"):
            es.deadModules = cms.vuint32(*sensors)
            print("# LSTskip: %s %d dead sensors (%s)" % (label, len(sensors), scenario))
    return process

def customiseLSTDeadModulesBaseline(process):         return process   # nothing dead: nominal map
def customiseLSTDeadModulesDeadModules1Pct(process):  return _lstDeadModules(process, "DeadModules1Pct")
def customiseLSTDeadModulesDeadModules5Pct(process):  return _lstDeadModules(process, "DeadModules5Pct")
def customiseLSTDeadModulesDeadModules10Pct(process): return _lstDeadModules(process, "DeadModules10Pct")
def customiseLSTDeadModulesDeadPhiSector(process):    return _lstDeadModules(process, "DeadPhiSector")
def customiseLSTDeadModulesDeadLayerTBPS1(process):   return _lstDeadModules(process, "DeadLayerTBPS1")
def customiseLSTDeadModulesDeadLayerTBPS2(process):   return _lstDeadModules(process, "DeadLayerTBPS2")

# Variants of the gap handling in LST (ES parameters of the LST dead-module patch), to be used after
# customiseLSTDeadModules<Scenario>: by default both the T3 r-z fix and the DNN bypass are on (v12 "LSTmapDNN").
def _lstGapSwitches(process, t3rz, dnnBypass):
    for label, es in process.es_producers_().items():
        if es.type_().startswith("LSTModulesDevESProducer"):
            es.gapT3RZ = cms.bool(t3rz)
            es.gapDNNBypass = cms.bool(dnnBypass)
            print("# LSTskip: %s gapT3RZ %s, gapDNNBypass %s" % (label, t3rz, dnnBypass))
    return process

def customiseLSTGapMapOnly(process): return _lstGapSwitches(process, False, False)   # v8 "lstskip", v11 "LSTmap"
def customiseLSTGapT3Only(process):  return _lstGapSwitches(process, True, False)    # v11 "LSTmapT3"
