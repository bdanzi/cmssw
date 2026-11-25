import FWCore.ParameterSet.Config as cms

# Phase-2 offline tracking baseline: LST+mkFit for initialStep+highPtTripletStep, JetCore with pixel cluster splitting.
# The modifiers below are active by default in Phase-2 offline reconstruction and switched off by the
# trackingPhase2Legacy procModifier; they can still be enabled explicitly with the original procModifiers.
# Only the offline configuration imports them: the HLT keeps using the original procModifiers.
from Configuration.Eras.Modifier_trackingPhase2PU140_cff import trackingPhase2PU140
from Configuration.ProcessModifiers.trackingPhase2Legacy_cff import trackingPhase2Legacy
from Configuration.ProcessModifiers.trackingLST_cff import trackingLST as _trackingLST
from Configuration.ProcessModifiers.seedingLST_cff import seedingLST as _seedingLST
from Configuration.ProcessModifiers.trackingMkFitHighPtTripletStep_cff import trackingMkFitHighPtTripletStep as _trackingMkFitHighPtTripletStep
from Configuration.ProcessModifiers.trackingMkFitInitialStepPreSplitting_cff import trackingMkFitInitialStepPreSplitting as _trackingMkFitInitialStepPreSplitting
from Configuration.ProcessModifiers.jetCoreInPhase2_cff import jetCoreInPhase2 as _jetCoreInPhase2
from Configuration.ProcessModifiers.splitClustersInPhase2Pixel_cff import splitClustersInPhase2Pixel as _splitClustersInPhase2Pixel

_phase2OfflineBaseline = trackingPhase2PU140 & ~trackingPhase2Legacy

trackingLST = _trackingLST | _phase2OfflineBaseline
seedingLST = _seedingLST | _phase2OfflineBaseline
trackingMkFitHighPtTripletStep = _trackingMkFitHighPtTripletStep | _phase2OfflineBaseline
trackingMkFitInitialStepPreSplitting = _trackingMkFitInitialStepPreSplitting | _phase2OfflineBaseline
jetCoreInPhase2 = _jetCoreInPhase2 | _phase2OfflineBaseline
splitClustersInPhase2Pixel = _splitClustersInPhase2Pixel | _phase2OfflineBaseline
