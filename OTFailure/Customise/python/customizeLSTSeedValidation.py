import FWCore.ParameterSet.Config as cms
#
# Diagnostics: validate the LST output itself (before mkFit), to see whether a loss of hltGeneralTracks comes from
# LST or from the mkFit building and fit on its seeds, and from which LST track candidate type.
#   - all LST seeds (hltInitialStepTrajectorySeedsLST) as tracks with TrackFromSeedProducer
#     (hltInitialStepTrajectorySeedsLSTTracks, already in the menu for the GPU vs CPU comparison);
#   - the LST track candidates of each type (T4+T5, pT3+pT5, pLS; LSTOutputConverter instance labels), fitted with the
#     hltInitialStepTracks fitter (hltLSTDiag*Tracks).
# Each collection gets its own MultiTrackValidator folder.
#
#   HLT step:        --customise OTFailure/Customise/customizeLSTSeedValidation.customiseHLTLSTSeedTracks
#   validation step: --customise OTFailure/Customise/customizeLSTSeedValidation.customiseValidationLSTSeedTracks
#   (runScenario.sh --lstseedval)
#
SEEDS = "hltInitialStepTrajectorySeedsLST"
SEED_TRACKS = "hltInitialStepTrajectorySeedsLSTTracks"
FITTED_TRACKS = "hltInitialStepTracks"
TYPE_CANDIDATES = "hltLSTDiagTrackCandidates"
# fitted track collection -> LSTOutputConverter instance label of the candidates
TYPE_TRACKS = {
    "hltLSTDiagT5Tracks": "t4t5TCsLST",
    "hltLSTDiagPTTracks": "pTTCsLST",
    "hltLSTDiagPLSTracks": "pLSTCsLST",
}

def _insertAfter(process, module, newModules):
    """Put newModules (a sequence expression) right after module in every sequence that has it."""
    replaced = False
    for sequence in process.sequences_().values():
        if sequence.contains(module):
            replaced = sequence.replace(module, module + newModules) or replaced
    if not replaced:
        raise RuntimeError("customizeLSTSeedValidation: %s is in no sequence" % module.label())

def customiseHLTLSTSeedTracks(process):
    """Produce the LST seed tracks and the fitted LST candidates of each type, and keep them in the HLT output."""
    _insertAfter(process, getattr(process, SEEDS), getattr(process, SEED_TRACKS))

    setattr(process, TYPE_CANDIDATES, getattr(process, SEEDS).clone(produceTrackCandidates = True))
    typeModules = getattr(process, TYPE_CANDIDATES)
    for tracks, instance in TYPE_TRACKS.items():
        setattr(process, tracks, getattr(process, FITTED_TRACKS).clone(src = (TYPE_CANDIDATES, instance)))
        typeModules = typeModules + getattr(process, tracks)
    # after the hltInitialStepTracks fit: everything the fit needs has run
    _insertAfter(process, getattr(process, FITTED_TRACKS), typeModules)

    for output in process.outputModules_().values():
        for label in [SEED_TRACKS] + list(TYPE_TRACKS):
            output.outputCommands.append("keep *_%s_*_*" % label)
    print("# OTFailure: LST seed tracks %s and LST candidates by type %s produced and kept"
          % (SEED_TRACKS, ", ".join(TYPE_TRACKS)))
    return process

def customiseValidationLSTSeedTracks(process):
    """Validate the LST seed tracks and the LST candidates by type with the HLT MultiTrackValidator."""
    for label in [SEED_TRACKS] + list(TYPE_TRACKS):
        process.hltTrackValidator.label.append(cms.InputTag(label))
    print("# OTFailure: MTV of the LST seed tracks and LST candidates by type")
    return process
