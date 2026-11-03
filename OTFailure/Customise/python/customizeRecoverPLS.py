import FWCore.ParameterSet.Config as cms
#
# Recover LST pixel seeds (pLS) whose CA-OT (or ITACA) track was lost (e.g. dead OT layer): run in addition a pixel-only
# CA (Inner Tracker layers only, quadruplets), merge its tracks with the default pixel tracks with shared-hit cleaning
# (a pixel-only quad contained in a CA-OT track is dropped), and seed LST/mkFit from the merged collection.
# Pixel vertices and everything else keep using hltPhase2PixelTracks.
#
# The pixel-only CA is the configuration of _hltPhase2PixelTracksSoANonCAExtended of CMSSW_20_1_0_pre3 (the CA of the
# Legacy + Patatrack-quads chain), rebuilt here from the layer and layer-pair tables of hltPhase2PixelTracksSoA_cfi so
# that it also works in releases where that module was removed (CMSSW_20_1_0_pre4 + ITACA).
#
OT_LAYERS = (28, 29, 30)   # first OT barrel layers used by the CA extension
N_IT_LAYERS = 28           # layers 0-27: Inner Tracker barrel and disks


def _pixelOnlyCA():
    from HLTrigger.Configuration.HLT_75e33.modules import hltPhase2PixelTracksSoA_cfi as soa
    layers = soa.layers[:N_IT_LAYERS]
    pairs = [lp for lp in soa.layerPairs if lp[0] not in OT_LAYERS and lp[1] not in OT_LAYERS]
    startingPairs = [i for i, lp in enumerate(pairs) if lp[2]]
    return cms.EDProducer("CAHitNtupletAlpakaPhase2@alpaka",
        pixelRecHitSrc = cms.InputTag("hltPhase2SiPixelRecHitsSoA"),
        ptmin = cms.double(0.9),
        hardCurvCut = cms.double(0.01425),   # 800 MeV in 3.8 T
        earlyFishbone = cms.bool(True),
        lateFishbone = cms.bool(False),
        fillStatistics = cms.bool(False),
        minHitsPerNtuplet = cms.uint32(4),
        maxNumberOfDoublets = cms.string(str(6 * 512 * 1024)),
        maxNumberOfTuples = cms.string(str(60 * 1024)),
        cellZ0Cut = cms.double(12.5),
        minYsizeB1 = cms.int32(20),
        minYsizeB2 = cms.int32(18),
        maxDYsize12 = cms.int32(12),
        maxDYsize = cms.int32(10),
        maxDYPred = cms.int32(24),
        avgHitsPerTrack = cms.double(7.0),
        avgCellsPerHit = cms.double(12),
        avgCellsPerCell = cms.double(0.151),
        avgTracksPerCell = cms.double(0.040),
        minHitsForSharingCut = cms.uint32(10),
        fitNas4 = cms.bool(False),
        useRiemannFit = cms.bool(False),
        doSharedHitCut = cms.bool(True),
        dupPassThrough = cms.bool(False),
        useSimpleTripletCleaner = cms.bool(True),
        doTripletCleaner = cms.bool(True),
        doFastDuplicateRemover = cms.bool(True),
        doEarlyDuplicateRemover = cms.bool(True),
        trackQualityCuts = cms.PSet(
            maxChi2TripletsOrQuadruplets = cms.double(5.0),
            maxChi2Quintuplets = cms.double(5.0),
            maxChi2 = cms.double(5.0),
            minPt = cms.double(0.9),
            maxTip = cms.double(0.3),
            maxZip = cms.double(12),
        ),
        geometry = cms.PSet(
            caDCACuts = cms.vdouble([l[2] for l in layers]),
            caThetaCuts = cms.vdouble([l[3] for l in layers]),
            startingPairs = cms.vuint32(startingPairs),
            startMaxInnerR = cms.vdouble([l[4] for l in layers]),
            maxDCurv = cms.vdouble([l[5] for l in layers]),
            floorDCurv = cms.vdouble([l[6] for l in layers]),
            fishboneCuts = cms.vdouble([l[7] for l in layers]),
            pairGraph = cms.vuint32(sum([[lp[0], lp[1]] for lp in pairs], [])),
            skipsLayers = cms.vuint32([int(lp[3]) for lp in pairs]),
            phiCuts = cms.vint32([lp[4] for lp in pairs]),
            minInner = cms.vdouble([lp[5] for lp in pairs]),
            maxInner = cms.vdouble([lp[6] for lp in pairs]),
            minOuter = cms.vdouble([lp[7] for lp in pairs]),
            maxOuter = cms.vdouble([lp[8] for lp in pairs]),
            maxDR = cms.vdouble([lp[9] for lp in pairs]),
            minDZ = cms.vdouble([lp[10] for lp in pairs]),
            maxDZ = cms.vdouble([lp[11] for lp in pairs]),
            ptCuts = cms.vdouble([lp[12] for lp in pairs]),
        ),
        alpaka = cms.untracked.PSet(backend = cms.untracked.string("")),
    )


def customiseRecoverPixelOnlySeeds(process):
    process.hltPhase2PixelTracksSoAPixOnly = _pixelOnlyCA()
    process.hltPhase2PixelTracksPixOnly = cms.EDProducer("PixelTrackProducerFromSoAAlpaka",
        beamSpot = cms.InputTag("hltOnlineBeamSpot"),
        minNumberOfHits = cms.int32(0),
        minQuality = cms.string("tight"),
        pixelRecHitLegacySrc = cms.InputTag("hltSiPixelRecHits"),
        trackSrc = cms.InputTag("hltPhase2PixelTracksSoAPixOnly"),
        outerTrackerRecHitSrc = cms.InputTag(""),
        useOTExtension = cms.bool(False),
        requireQuadsFromConsecutiveLayers = cms.bool(True),
    )
    process.hltPhase2PixelTracksForLST = cms.EDProducer("TrackListMerger",
        Epsilon = cms.double(-0.001),
        FoundHitBonus = cms.double(5.0),
        LostHitPenalty = cms.double(5.0),
        MaxNormalizedChisq = cms.double(1000.0),
        MinFound = cms.int32(3),
        MinPT = cms.double(0.0),
        ShareFrac = cms.double(0.19),
        TrackProducers = cms.VInputTag("hltPhase2PixelTracks", "hltPhase2PixelTracksPixOnly"),
        allowFirstHitShare = cms.bool(True),
        copyExtras = cms.untracked.bool(True),
        copyMVA = cms.bool(False),
        hasSelector = cms.vint32(0, 0),
        indivShareFrac = cms.vdouble(1.0, 1.0),
        makeReKeyedSeeds = cms.untracked.bool(False),
        newQuality = cms.string("confirmed"),
        selectedTrackQuals = cms.VInputTag("hltPhase2PixelTracks", "hltPhase2PixelTracksPixOnly"),
        setsToMerge = cms.VPSet(cms.PSet(pQual = cms.bool(False), tLists = cms.vint32(0, 1))),
        trackAlgoPriorityOrder = cms.string("trackAlgoPriorityOrder"),
        writeOnlyTrkQuals = cms.bool(False),
    )
    process.hltInitialStepSeeds.InputCollection = "hltPhase2PixelTracksForLST"
    process.HLTInitialStepSequence.replace(process.hltInitialStepSeeds,
        process.hltPhase2PixelTracksSoAPixOnly + process.hltPhase2PixelTracksPixOnly + process.hltPhase2PixelTracksForLST
        + process.hltInitialStepSeeds)
    print("# RecoverPLS: pixel-only CA (%d layer pairs) merged with the default pixel tracks as LST/mkFit seeds"
          % (len(process.hltPhase2PixelTracksSoAPixOnly.geometry.pairGraph) // 2))
    return process
