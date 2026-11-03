import FWCore.ParameterSet.Config as cms
#
# LST dead-hit option: the dead OT sensors of a scenario are passed to LSTInputProducer (deadHitDetIds), which puts a
# placeholder hit at the centre of each. A placeholder makes a minidoublet with every hit of the live partner sensor,
# with its position moved from the live hit along the line from the beam spot onto the dead sensor (MiniDoublet.h).
# Every LST object built on it then updates that position from its own real hits (DeadHitPlacement.h).
# By default only strip sensors get a placeholder: a placeholder on a PS macro-pixel sensor makes the minidoublet anchor
# from a strip hit, whose z is known only within the strip length, and that loses efficiency (100-event test).
# The customiseLSTDeadHitsAllSensors* variants put placeholders on the macro-pixel sensors too: the objects then refine
# such an anchor from their other minidoublets.
#
# Dead stacks (whole-module payload scenarios): both sensors of every dead module get a placeholder, PS macro-pixel
# included since there is no live hit to rebuild from. The two placeholders make a fully fake minidoublet, which each
# LST object places along its own track (RecoTracker/LSTCore/src/alpaka/DeadHitPlacement.h). A module gets this
# treatment only when both of its sensors are listed, so the single-sensor scenarios above are unchanged.
#
# Option bits (LSTInputProducer deadHitOptions, lst::deadhit in RecoTracker/LSTCore/interface/Common.h), default
# DEFAULT_DEAD_HIT_OPTIONS; setDeadHitOptions(process, bits) changes them (runScenario.sh --lstdeadopts).
# LSTInputProducer takes the half sizes of the dead sensors from the tracker geometry; its deadHitTolerance (cm)
# bounds how far outside them LST may place a position on a dead module.
#
# Use on the HLT step, after the scenario customise of the DIGI step: e.g.
#   --customise OTFailure/Customise/customizeLSTDeadHits.customiseLSTDeadHitsDeadPSensorsTBPS2
#
from OTFailure.Customise.customizeOTFailureScenarios import deadSensors, SINGLE_SENSOR_SCENARIOS, _otModules

DEAD_HIT_OPTIONS = {
    "beamSpot": 1 << 0,                  # project and point from the beam spot instead of the origin
    "segmentCircle": 1 << 1,             # segments place half-fake minidoublets on a circle
    "segmentTwoHalfFake": 1 << 2,        # segments of two half-fake minidoublets
    "segmentHalfAndFullyFake": 1 << 3,   # segments of a half-fake and a fully fake minidoublet
    "t5StripErrors": 1 << 4,             # T5 chi2: strip-size errors for placeholder positions
    "noTightFlagWithPlaceholder": 1 << 5,  # unused (no-op): the retrained T5 DNN (cms-sw/cmssw#52011) has no tightCutFlag
    "onePlaceholderPerT3": 1 << 6,       # at most one placeholder minidoublet per T3
}
# Default (100-event TTbar test, 6 scenarios, CMSSW_20_1_0_pre4): beam spot, both segment combinations and one
# placeholder per T3 (77) are never worse than nominal or versions 1-3. The segment circle and the T5 strip errors lose.
# Dropping the T5 tightCutFlag with a placeholder (+32 = 109) was studied in pre4; since the T5 DNN retraining
# (cms-sw/cmssw#52011) there is no tightCutFlag and bit 32 does nothing.
DEFAULT_DEAD_HIT_OPTIONS = (DEAD_HIT_OPTIONS["beamSpot"] | DEAD_HIT_OPTIONS["segmentTwoHalfFake"]
                            | DEAD_HIT_OPTIONS["segmentHalfAndFullyFake"] | DEAD_HIT_OPTIONS["onePlaceholderPerT3"])

def _lstInputProducers(process):
    return [p for p in process.producers_().values() if "LSTInputProducer" in p.type_()]

def describeDeadHitOptions(options):
    names = [name for name, bit in DEAD_HIT_OPTIONS.items() if options & bit]
    return "%d (%s)" % (options, ", ".join(names) if names else "none")

def setDeadHitOptions(process, options):
    """Dead-hit option bits of every LSTInputProducer (only used with placeholder hits)."""
    for producer in _lstInputProducers(process):
        producer.deadHitOptions = cms.uint32(options)
    print("# OTFailure: LST dead-hit options %s" % describeDeadHitOptions(options))
    return process

def _stripSensors(sensors):
    macroPixel = set(m["rawId"] for m in _otModules() if m["type"] == "PSP")
    return [s for s in sensors if s not in macroPixel]

def _deadHits(process, scenario, macroPixelSensors=False):
    dead = deadSensors(scenario)
    sensors = list(dead) if macroPixelSensors else _stripSensors(dead)
    producers = _lstInputProducers(process)
    if not producers:
        raise RuntimeError("customizeLSTDeadHits: no LSTInputProducer in the process")
    for producer in producers:
        producer.deadHitDetIds = cms.vuint32(*sorted(sensors))
    print("# OTFailure: LST dead hits on %d of %d dead sensors, macro-pixel sensors %s (%s)"
          % (len(sensors), len(dead), "included" if macroPixelSensors else "excluded",
             SINGLE_SENSOR_SCENARIOS[scenario]))
    return setDeadHitOptions(process, DEFAULT_DEAD_HIT_OPTIONS)

# ---- dead stacks: whole dead modules of the payload scenarios
DEAD_STACK_SCENARIOS = ["DeadLayerTBPS1", "DeadLayerTBPS2", "DeadModules10Pct", "DeadPhiSector"]

def deadStackSensors(scenario):
    """detIds of both sensors of every dead OT module (stack detIds in the scenario's bad module list)."""
    from OTFailure.Customise.scenarioData import badModuleList
    deadStacks = set(badModuleList(scenario))
    return [m["rawId"] for m in _otModules() if m["stack"] in deadStacks]

def _deadStacks(process, scenario):
    sensors = deadStackSensors(scenario)
    producers = _lstInputProducers(process)
    if not producers:
        raise RuntimeError("customizeLSTDeadHits: no LSTInputProducer in the process")
    for producer in producers:
        producer.deadHitDetIds = cms.vuint32(*sorted(sensors))
    print("# OTFailure: LST dead stacks, placeholders on both sensors of %d dead modules (%s)"
          % (len(sensors) // 2, scenario))
    return setDeadHitOptions(process, DEFAULT_DEAD_HIT_OPTIONS)

# ---- scenario entry points (runScenario.sh --lstdeadhits)
def customiseLSTDeadHitsDeadPSensorsTBPS2(process): return _deadHits(process, "DeadPSensorsTBPS2")
def customiseLSTDeadHitsDeadSSensorsTBPS2(process): return _deadHits(process, "DeadSSensorsTBPS2")
def customiseLSTDeadHitsDeadSensors10Pct(process):  return _deadHits(process, "DeadSensors10Pct")
def customiseLSTDeadHitsDeadLayerTBPS1(process):   return _deadStacks(process, "DeadLayerTBPS1")
def customiseLSTDeadHitsDeadLayerTBPS2(process):   return _deadStacks(process, "DeadLayerTBPS2")
def customiseLSTDeadHitsDeadModules10Pct(process): return _deadStacks(process, "DeadModules10Pct")
def customiseLSTDeadHitsDeadPhiSector(process):    return _deadStacks(process, "DeadPhiSector")

def customiseLSTDeadHitsAllSensorsDeadPSensorsTBPS2(process):
    return _deadHits(process, "DeadPSensorsTBPS2", macroPixelSensors=True)
def customiseLSTDeadHitsAllSensorsDeadSSensorsTBPS2(process):
    return _deadHits(process, "DeadSSensorsTBPS2", macroPixelSensors=True)
def customiseLSTDeadHitsAllSensorsDeadSensors10Pct(process):
    return _deadHits(process, "DeadSensors10Pct", macroPixelSensors=True)
