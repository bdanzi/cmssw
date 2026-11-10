import FWCore.ParameterSet.Config as cms

# Run 3 low-pT and displaced tracking, e.g. for a re-reconstruction. Every iteration keeps its default
# algorithm (mkFit or CKF); it changes:
#  - the track selection: TrackTfClassifier with useClusterFeatures, the track inputs plus 10 cluster-level inputs
#    (RecoTracker/FinalTrackSelectors/python/trackSelectionTfHit_cff.py)
#  - the seeding regions of lowPtQuad, lowPtTriplet, pixelPair, detachedQuad, detachedTriplet, mixedTriplet,
#    pixelLess and tobTec steps (lower pT, larger origin radius for displaced tracks)
#  - one more hole per candidate in the mkFit pixelLessStep
trackingLowPtRun3 = cms.Modifier()
