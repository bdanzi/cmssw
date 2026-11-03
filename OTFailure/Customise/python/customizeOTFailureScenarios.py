import FWCore.ParameterSet.Config as cms
#
# Phase-2 OT failure scenarios, all with bias-rail inefficiency OFF (BiasRailInefficiencyFlag = 0).
#   Baseline     : no dead channels
#   SSide<N>Pct  : N% random dead strips in PS-s and SS sensors (same as release customizeSiPhase2OTInefficiency*)
#   PSide<N>Pct  : N% random dead macro-pixels in PS-p sensors (needs the patched PSPDigitizerAlgorithm::channel_killing_DB
#                  and SiPhase2BadStripConfigurableFakeESSource with badComponentsFractionPSP)
# The dead-channel map is reproducible: process.SiPhase2OTFakeBadStripsESSource.seed (default 1).
#
def _digiPSets(process):
    out = []
    if hasattr(process, "mix") and hasattr(process.mix, "digitizers") and hasattr(process.mix.digitizers, "pixel"):
        out.append(process.mix.digitizers.pixel)
    if hasattr(process, "mixData") and hasattr(process.mixData, "workers") and hasattr(process.mixData.workers, "pixel"):
        out.append(process.mixData.workers.pixel)
    return out

def _noBiasRail(process):
    for p in _digiPSets(process):
        p.PSPDigitizerAlgorithm.BiasRailInefficiencyFlag = cms.int32(0)
    print("# OTFailure: bias rail inefficiency OFF")
    return process

def _kill(process, algos):
    # dead channels from SiPhase2OuterTrackerBadStripRcd (the fake ESSource below): channel_killing_DB of each algorithm
    for p in _digiPSets(process):
        for a in algos:
            getattr(p, a).KillChannels_DB = cms.untracked.bool(True)

def _fractions(process, s, p):
    es = process.SiPhase2OTFakeBadStripsESSource
    es.badComponentsFraction = cms.double(s)
    es.badComponentsFractionPSP = cms.double(p)
    print("# OTFailure: dead S-side strips %.3f, dead P-side macro-pixels %.3f, seed %d" % (s, p, es.seed.value()))

def _sside(process, f):
    _noBiasRail(process); _kill(process, ["PSSDigitizerAlgorithm", "SSDigitizerAlgorithm"]); _fractions(process, f, 0.)
    return process

def _pside(process, f):
    _noBiasRail(process); _kill(process, ["PSPDigitizerAlgorithm"]); _fractions(process, 0., f)
    return process

def customiseBaseline(process):    return _noBiasRail(process)
def customiseSSide1Pct(process):   return _sside(process, 0.01)
def customiseSSide5Pct(process):   return _sside(process, 0.05)
def customiseSSide10Pct(process):  return _sside(process, 0.10)
def customisePSide1Pct(process):   return _pside(process, 0.01)
def customisePSide5Pct(process):   return _pside(process, 0.05)
def customisePSide10Pct(process):  return _pside(process, 0.10)

# ---------------------------------------------------------------------------------------------
# "Brutal" random channels
def customiseSSide25Pct(process):  return _sside(process, 0.25)
def customiseSSide50Pct(process):  return _sside(process, 0.50)
def customisePSide25Pct(process):  return _pside(process, 0.25)
def customisePSide50Pct(process):  return _pside(process, 0.50)

# ---------------------------------------------------------------------------------------------
# Holes: whole sensors/modules dead, via SiPhase2OTFakeBadStripsESSource.deadDetIds
# Module list: OTFailure/Customise/data/OTModules_D121.txt (rawId type subdet layer side stackId r phi z),
# dumped with OTFailure/Customise/test/dumpOTModules_cfg.py
import os, math, random
HOLE_SEED = 1   # fixed seed for the random choice of dead modules

def _otModules():
    from OTFailure.Customise.scenarioData import dataFile
    mods = []
    for l in open(dataFile("OTModules_D121.txt")):
        if l.startswith("#"): continue
        r = l.split()
        mods.append(dict(rawId=int(r[0]), type=r[1], subdet=r[2], layer=int(r[3]), side=int(r[4]),
                         stack=int(r[5]), r=float(r[6]), phi=float(r[7]), z=float(r[8])))
    return mods

def _dead(process, detids, what):
    _noBiasRail(process)
    _kill(process, ["PSPDigitizerAlgorithm", "PSSDigitizerAlgorithm", "SSDigitizerAlgorithm"])
    _fractions(process, 0., 0.)
    process.SiPhase2OTFakeBadStripsESSource.deadDetIds = cms.vuint32(sorted(detids))
    print("# OTFailure: %s -> %d dead sensors" % (what, len(detids)))
    return process

def _deadModules(process, f):
    mods = _otModules()
    stacks = sorted(set(m["stack"] for m in mods))
    dead = set(random.Random(HOLE_SEED).sample(stacks, int(round(f * len(stacks)))))
    return _dead(process, [m["rawId"] for m in mods if m["stack"] in dead],
                 "%.0f%% random dead OT modules (%d/%d modules, seed %d)" % (100 * f, len(dead), len(stacks), HOLE_SEED))

def customiseDeadModules1Pct(process):  return _deadModules(process, 0.01)
def customiseDeadModules5Pct(process):  return _deadModules(process, 0.05)
def customiseDeadModules10Pct(process): return _deadModules(process, 0.10)

def customiseDeadPhiSector(process):
    # one 40 deg phi wedge (0 <= phi < 2pi/9) on the z>0 side, all OT layers/disks
    mods = _otModules()
    return _dead(process, [m["rawId"] for m in mods if m["z"] > 0 and 0. <= m["phi"] < 2 * math.pi / 9],
                 "dead phi sector 0-40deg, z>0")

def customiseDeadLayerTBPS1(process):
    # first OT barrel layer (TBPS L1, PS modules) fully dead
    mods = _otModules()
    return _dead(process, [m["rawId"] for m in mods if m["subdet"] == "TOB" and m["layer"] == 1], "dead TBPS layer 1")

# ---------------------------------------------------------------------------------------------
# Single dead sensors: one sensor of the stack is dead, its partner is alive (test case of the LST dead-hit option).
# P = PS macro-pixel sensor (PSP), S = PS strip sensor (PSS).
SINGLE_SENSOR_SCENARIOS = {
    "DeadPSensorsTBPS2": "TBPS layer 2, PS macro-pixel sensors dead",
    "DeadSSensorsTBPS2": "TBPS layer 2, PS strip sensors dead",
    "DeadSensors10Pct": "10% random OT modules with one random sensor dead",
}

def deadSensors(scenario):
    """detIds of the dead sensors of a single-sensor scenario."""
    mods = _otModules()
    if scenario == "DeadPSensorsTBPS2":
        return [m["rawId"] for m in mods if m["subdet"] == "TOB" and m["layer"] == 2 and m["type"] == "PSP"]
    if scenario == "DeadSSensorsTBPS2":
        return [m["rawId"] for m in mods if m["subdet"] == "TOB" and m["layer"] == 2 and m["type"] == "PSS"]
    if scenario == "DeadSensors10Pct":
        rng = random.Random(HOLE_SEED)
        stacks = sorted(set(m["stack"] for m in mods))
        dead_stacks = rng.sample(stacks, int(round(0.10 * len(stacks))))
        sensors_of = {}
        for m in mods:
            sensors_of.setdefault(m["stack"], []).append(m["rawId"])
        return [rng.choice(sorted(sensors_of[s])) for s in dead_stacks]
    raise ValueError("unknown single-sensor scenario %s" % scenario)

def customiseDeadPSensorsTBPS2(process):
    return _dead(process, deadSensors("DeadPSensorsTBPS2"), SINGLE_SENSOR_SCENARIOS["DeadPSensorsTBPS2"])
def customiseDeadSSensorsTBPS2(process):
    return _dead(process, deadSensors("DeadSSensorsTBPS2"), SINGLE_SENSOR_SCENARIOS["DeadSSensorsTBPS2"])
def customiseDeadSensors10Pct(process):
    return _dead(process, deadSensors("DeadSensors10Pct"), SINGLE_SENSOR_SCENARIOS["DeadSensors10Pct"])

# ---------------------------------------------------------------------------------------------
# Batch splitting with reproducible, scenario-independent random seeds.
# Job <chunk> processes input events [chunk*nev, (chunk+1)*nev). Every engine of the
# RandomNumberGeneratorService gets seed = f(engine name, chunk) -> identical signal digitization noise
# and PU overlay for a given chunk in all scenarios (paired comparison), and bit-identical reruns
# when run single-threaded (nThreads=1).
import zlib
def setChunk(process, chunk, nev):
    process.source.skipEvents = cms.untracked.uint32(chunk * nev)
    process.maxEvents.input = cms.untracked.int32(nev)
    rng = process.RandomNumberGeneratorService
    for name in rng.parameterNames_():
        p = getattr(rng, name)
        if isinstance(p, cms.PSet) and hasattr(p, "initialSeed"):
            p.initialSeed = cms.untracked.uint32((zlib.crc32(name.encode()) + 7919 * (chunk + 1)) % 900000000 + 1)
    print("# OTFailure: chunk %d, events [%d,%d), deterministic seeds" % (chunk, chunk * nev, (chunk + 1) * nev))
    return process

# ---------------------------------------------------------------------------------------------
# Restore the default PS-p bias-rail inefficiency (BiasRailInefficiencyFlag = 1, release default) after a scenario
# customise. Use as the LAST customise: --customise ...customise<Scenario>,...customiseRestoreBiasRail
def customiseRestoreBiasRail(process):
    for p in _digiPSets(process):
        p.PSPDigitizerAlgorithm.BiasRailInefficiencyFlag = cms.int32(1)
    print("# OTFailure: bias rail inefficiency restored to default (ON)")
    return process

# ---------------------------------------------------------------------------------------------
# v6: dead modules from SiPixelQuality payloads (cms-sw/cmssw#52130 + stefduponcheel:DigitizerExtensionForBadModules).
# Payloads built with SiPhase2BadModuleByHandBuilder from data/badModuleLists (see test/buildBadModulePayload_cfg.py),
# shipped in data/payloads. Bias rail is left at its default (ON).
from OTFailure.Customise.scenarioData import payloadConnect

def _payload(process, name, ot, it):
    toGet = []
    for p in _digiPSets(process):
        if ot:
            for a in ("PSPDigitizerAlgorithm", "PSSDigitizerAlgorithm", "SSDigitizerAlgorithm"):
                getattr(p, a).KillModules = cms.bool(True); getattr(p, a).DeadModules_DB = cms.bool(True)
        if it:
            for a in ("PixelDigitizerAlgorithm", "Pixel3DDigitizerAlgorithm"):
                if hasattr(p, a):
                    getattr(p, a).KillModules = cms.bool(True); getattr(p, a).DeadModules_DB = cms.bool(True)
    if ot: toGet.append(cms.PSet(record = cms.string("SiPhase2OuterTrackerBadModuleRcd"), tag = cms.string("OTBadModules")))
    if it: toGet.append(cms.PSet(record = cms.string("SiPhase2InnerTrackerBadModuleRcd"), tag = cms.string("ITBadModules")))
    process.badModulesPayload = cms.ESSource("PoolDBESSource", connect = cms.string(payloadConnect(name)),
                                             toGet = cms.VPSet(*toGet))
    process.es_prefer_badModulesPayload = cms.ESPrefer("PoolDBESSource", "badModulesPayload")
    print("# OTFailure v6: dead modules from payload %s (OT %s, IT %s)" % (payloadConnect(name), ot, it))
    return process

def customisePayloadBaseline(process):           return process
def customisePayloadStefanExample(process):      return _payload(process, "StefanExample", True, True)
def customisePayloadDeadModules1Pct(process):    return _payload(process, "DeadModules1Pct", True, False)
def customisePayloadDeadModules5Pct(process):    return _payload(process, "DeadModules5Pct", True, False)
def customisePayloadDeadModules10Pct(process):   return _payload(process, "DeadModules10Pct", True, False)
def customisePayloadDeadPhiSector(process):      return _payload(process, "DeadPhiSector", True, False)
def customisePayloadDeadLayerTBPS1(process):     return _payload(process, "DeadLayerTBPS1", True, False)
def customisePayloadDeadLayerTBPS2(process):     return _payload(process, "DeadLayerTBPS2", True, False)
def customisePayloadDeadITModules1Pct(process):  return _payload(process, "DeadITModules1Pct", False, True)
def customisePayloadDeadITModules5Pct(process):  return _payload(process, "DeadITModules5Pct", False, True)
