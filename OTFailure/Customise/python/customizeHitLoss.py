import FWCore.ParameterSet.Config as cms
#
# Random hit loss for HLT tracking robustness studies (needs the patched Phase2TrackerDigitizerAlgorithm in
# CMSSW_20_1_0_pre4_ITACA: untracked HitLossProbability / HitLossBPIX1Factor / HitLossSeed).
# Every SimHit (IT and OT, signal and pileup) is dropped before digitization with probability p,
# p x BPIX1factor in the innermost pixel barrel layer. Independent per sensor: for stacked OT modules the
# P and S (or the two 2S) sensors lose hits independently. Deterministic (hash of the SimHit, seed HitLossSeed).
# Bias rail stays at its default.
#
_ALGOS = ("PixelDigitizerAlgorithm", "Pixel3DDigitizerAlgorithm", "PSPDigitizerAlgorithm", "PSSDigitizerAlgorithm", "SSDigitizerAlgorithm")

def _hitLoss(process, p, bpix1):
    for owner in ("mix", "mixData"):
        if not hasattr(process, owner): continue
        o = getattr(process, owner)
        pix = o.digitizers.pixel if owner == "mix" and hasattr(o, "digitizers") else (o.workers.pixel if hasattr(o, "workers") else None)
        if pix is None: continue
        for a in _ALGOS:
            if hasattr(pix, a):
                ps = getattr(pix, a)
                ps.HitLossProbability = cms.untracked.double(p)
                ps.HitLossBPIX1Factor = cms.untracked.double(bpix1)
                ps.HitLossSeed = cms.untracked.uint32(1)
    print("# HitLoss: p = %.3f (BPIX1: %.3f), independent per sensor, seed 1" % (p, p * bpix1))
    return process

def customiseHitLossNone(process):          return process
def customiseHitLoss1PctBPIX1x1(process):   return _hitLoss(process, 0.01, 1.)
def customiseHitLoss1PctBPIX1x3(process):   return _hitLoss(process, 0.01, 3.)
def customiseHitLoss3PctBPIX1x1(process):   return _hitLoss(process, 0.03, 1.)
def customiseHitLoss3PctBPIX1x3(process):   return _hitLoss(process, 0.03, 3.)
def customiseHitLoss5PctBPIX1x1(process):   return _hitLoss(process, 0.05, 1.)
def customiseHitLoss5PctBPIX1x3(process):   return _hitLoss(process, 0.05, 3.)

def customisePromptValidation(process):
    # HLT MTV restricted to prompt TrackingParticles (transverse impact parameter < 1 mm)
    process.hltTrackValidator.tipTP = cms.double(0.1)
    print("# Prompt validation: tipTP = 0.1 cm")
    return process
