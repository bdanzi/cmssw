import FWCore.ParameterSet.Config as cms
#
# CA extended into the OT (CAHitNtupletAlpakaPhase2OT): add layer pairs that skip the first OT barrel layer
# (layer 28 = TBPS1) and land on TBPS2 (layer 29). In the release these pairs exist only as commented-out lines of
# hltPhase2PixelTracksSoA_cfi.py, so with TBPS1 dead the CA cannot continue into the OT at all.
# Cuts are the ones of the corresponding pair into layer 28, with the outer-z window and the dz window scaled by the
# ratio of the lever arms (TBPS2 at r ~ 36 cm, TBPS1 at r ~ 25.6 cm) and a wider phi window.
#
# pair: i, o, start, skip, phiCut, minIn, maxIn, minOut, maxOut, maxDR, minDZ, maxDZ, ptCut
_SKIP_PAIRS = [
    [ 3, 29, False, True, 1500,  -20.0,   20.0,  -65.0,   65.0, 10000, -44.0,  44.0, 0.85],   # pixel barrel L4 -> TBPS2
    [ 4, 29, False, True, 1500,   11.6,  10000,   42.0,   83.0,  24.0,   7.0,  52.0, 0.85],   # forward disks -> TBPS2, z>0
    [ 5, 29, False, True, 1500,   11.6,  10000,   57.0,  115.0,  24.0, -16.0,  80.0, 0.85],
    [ 6, 29, False, True, 1500,   11.6,  10000,   79.0,  137.0,  24.0,   7.0,  80.0, 0.85],
    [16, 29, False, True, 1500,   11.6,  10000,  -83.0,  -42.0,  24.0, -52.0,  -7.0, 0.85],   # same, z<0
    [17, 29, False, True, 1500,   11.6,  10000, -115.0,  -57.0,  24.0, -80.0,  16.0, 0.85],
    [18, 29, False, True, 1500,   11.6,  10000, -137.0,  -79.0,  24.0, -80.0,  -7.0, 0.85],
]
# v10: the pairs into TBPS1 from disks 4 and 5 (layers 7, 8 and 19, 20), skipping TBPS1 into TBPS2, same scaling
_SKIP_PAIRS_DISKS = [
    [ 7, 29, False, True, 1500,   11.8,  10000,   99.0,  155.0,  24.0,  21.0, 112.0, 0.85],   # disks 4, 5 -> TBPS2, z>0
    [ 8, 29, False, True, 1300,      0,  10000,  113.0,  10000,  21.0,  35.0, 112.0, 0.85],
    [19, 29, False, True, 1500,   11.8,  10000, -155.0,  -99.0,  24.0,-112.0, -21.0, 0.85],   # same, z<0
    [20, 29, False, True, 1300,      0,  10000, -10000, -113.0,  21.0,-112.0, -35.0, 0.85],
]
# v10: pixel barrel L3 -> TBPS2, for tracks at |eta| ~ 1-1.4 that miss barrel L4 (|z| > 20 cm) and have TBPS1 as next layer
_SKIP_PAIRS_BPIX3 = [
    [ 2, 29, False, True, 1500,  -20.0,   20.0,  -71.0,   71.0, 10000, -50.0,  50.0, 0.85],
]
# v11: dead TBPS2 -> TBPS1 to TBPS3 (layer 28 -> 30), the commented-out release pair with the dz window of 28->29 / 29->30 widened
_SKIP_PAIRS_TBPS2 = [
    [28, 30, False, True, 2000,  -1200,   1200,  -10000,  10000, 10000, -60.0,  60.0, 0.85],
]
_FIELDS = ["skipsLayers", "phiCuts", "minInner", "maxInner", "minOuter", "maxOuter", "maxDR", "minDZ", "maxDZ", "ptCuts"]

def _addPairs(process, extra):
    for label, mod in process.producers_().items():
        if not mod.type_().startswith("CAHitNtupletAlpakaPhase2OT"):
            continue
        g = mod.geometry
        n = len(g.pairGraph) // 2
        pairs = [[g.pairGraph[2 * i], g.pairGraph[2 * i + 1]] + [getattr(g, f)[i] for f in _FIELDS] for i in range(n)]
        start = set(g.startingPairs)
        rows = [(p, i in start) for i, p in enumerate(pairs)]
        for sp in extra:
            row = [sp[0], sp[1], int(sp[3])] + sp[4:]
            # keep the pairs grouped by inner layer: insert after the last pair with the same inner layer
            pos = max([k for k, (p, s) in enumerate(rows) if p[0] == sp[0]], default=len(rows) - 1) + 1
            rows.insert(pos, (row, sp[2]))
        g.pairGraph = cms.vuint32(sum([[p[0], p[1]] for p, s in rows], []))
        g.startingPairs = cms.vuint32([k for k, (p, s) in enumerate(rows) if s])
        for j, f in enumerate(_FIELDS):
            old = getattr(g, f)
            setattr(g, f, type(old)([p[2 + j] for p, s in rows]))
        print("# CAOTSkip: %s: %d -> %d layer pairs (%d skip pairs added)" % (label, n, len(rows), len(extra)))
    return process

def customiseCAOTSkipTBPS1(process):
    return _addPairs(process, _SKIP_PAIRS)

def customiseCAOTSkipTBPS1Disks(process):
    return _addPairs(process, _SKIP_PAIRS + _SKIP_PAIRS_DISKS)

def customiseCAOTSkipTBPS1Full(process):
    return _addPairs(process, _SKIP_PAIRS + _SKIP_PAIRS_DISKS + _SKIP_PAIRS_BPIX3)

def customiseCAOTSkipTBPS2(process):
    return _addPairs(process, _SKIP_PAIRS_TBPS2)

# ---------------------------------------------------------------------------------------------
# Generic version for any CA with a layer-pair geometry (ITACA = CAHitNtupletAlpakaPhase2OTStubs, ~20 per-pair columns):
# every pair (i, oldOuter) [or exactly (inner, oldOuter)] is copied to (i, newOuter) with skipsLayers = 1 and its outer-z,
# dz, dr and phi windows scaled by the lever-arm ratio. All other per-pair columns (stub cuts, caTheta, caDCA, ...) are copied.
def _copySkipPairs(process, typePrefix, oldOuter, newOuter, scaleZ, scaleDZ, scaleDR, scalePhi, inners=None):
    BIG = 9999.
    for label, mod in process.producers_().items():
        if not mod.type_().startswith(typePrefix):
            continue
        g = mod.geometry
        n = len(g.pairGraph) // 2
        fields = [f for f in g.parameterNames_() if f not in ("pairGraph", "startingPairs")
                  and hasattr(getattr(g, f), "__len__") and not isinstance(getattr(g, f), str) and len(getattr(g, f)) == n]
        rows = [dict(i=g.pairGraph[2 * k], o=g.pairGraph[2 * k + 1], start=k in set(g.startingPairs), **{f: getattr(g, f)[k] for f in fields})
                for k in range(n)]
        new = []
        for r in rows:
            if r["o"] != oldOuter or (inners is not None and r["i"] not in inners): continue
            c = dict(r); c["o"] = newOuter; c["start"] = False; c["skipsLayers"] = 1
            for f, s in (("minOuter", scaleZ), ("maxOuter", scaleZ), ("minDZ", scaleDZ), ("maxDZ", scaleDZ), ("maxDR", scaleDR)):
                if f in c and abs(c[f]) < BIG: c[f] = c[f] * s
            if "phiCuts" in c: c["phiCuts"] = int(round(c["phiCuts"] * scalePhi))
            new.append(c)
        for c in new:
            pos = max([k for k, r in enumerate(rows) if r["i"] == c["i"]], default=len(rows) - 1) + 1
            rows.insert(pos, c)
        g.pairGraph = cms.vuint32(sum([[r["i"], r["o"]] for r in rows], []))
        g.startingPairs = cms.vuint32([k for k, r in enumerate(rows) if r["start"]])
        for f in fields:
            setattr(g, f, type(getattr(g, f))([r[f] for r in rows]))
        print("# CAOTSkip: %s (%s): %d -> %d layer pairs (%d copied %d->%d with skip)" % (label, mod.type_(), n, len(rows), len(new), oldOuter, newOuter))
    return process

def customiseITACASkipTBPS1(process):
    # all pairs into TBPS1 (28) also land on TBPS2 (29): lever arm 36/25.6 = 1.41
    return _copySkipPairs(process, "CAHitNtupletAlpakaPhase2OTStubs", 28, 29, 1.41, 1.6, 1.5, 1.5)

def customiseITACASkipTBPS2(process):
    # TBPS1 -> TBPS3 (28 -> 30) copied from 28 -> 29
    return _copyFromPair(process, "CAHitNtupletAlpakaPhase2OTStubs", (28, 29), (28, 30), 1.2, 1.5)

def _copyFromPair(process, typePrefix, src, dst, scaleDZ, scalePhi):
    BIG = 9999.
    for label, mod in process.producers_().items():
        if not mod.type_().startswith(typePrefix):
            continue
        g = mod.geometry
        n = len(g.pairGraph) // 2
        fields = [f for f in g.parameterNames_() if f not in ("pairGraph", "startingPairs")
                  and hasattr(getattr(g, f), "__len__") and not isinstance(getattr(g, f), str) and len(getattr(g, f)) == n]
        rows = [dict(i=g.pairGraph[2 * k], o=g.pairGraph[2 * k + 1], start=k in set(g.startingPairs), **{f: getattr(g, f)[k] for f in fields})
                for k in range(n)]
        tmpl = [r for r in rows if (r["i"], r["o"]) == tuple(src)]
        for t in tmpl:
            c = dict(t); c["i"], c["o"] = dst; c["start"] = False; c["skipsLayers"] = 1
            for f in ("minDZ", "maxDZ"):
                if f in c and abs(c[f]) < BIG: c[f] = c[f] * scaleDZ
            if "phiCuts" in c: c["phiCuts"] = int(round(c["phiCuts"] * scalePhi))
            pos = max([k for k, r in enumerate(rows) if r["i"] == c["i"]], default=len(rows) - 1) + 1
            rows.insert(pos, c)
        g.pairGraph = cms.vuint32(sum([[r["i"], r["o"]] for r in rows], []))
        g.startingPairs = cms.vuint32([k for k, r in enumerate(rows) if r["start"]])
        for f in fields:
            setattr(g, f, type(getattr(g, f))([r[f] for r in rows]))
        print("# CAOTSkip: %s (%s): %d -> %d layer pairs (%s copied to %s with skip)" % (label, mod.type_(), n, len(rows), src, dst))
    return process
