import FWCore.ParameterSet.Config as cms

# Phase-2 offline tracking as before LST+mkFit+JetCore became the default:
# legacy CA seeding, mkFit building in initialStep, CKF building in the other iterations, no JetCore
trackingPhase2Legacy = cms.Modifier()
