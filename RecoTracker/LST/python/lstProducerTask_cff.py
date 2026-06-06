import FWCore.ParameterSet.Config as cms

from RecoTracker.LST.lstProducer_cfi import lstProducer

from RecoTracker.LST.lstModulesDevESProducer_cfi import lstModulesDevESProducer

from Configuration.ProcessModifiers.seedingLST_cff import seedingLST
from Configuration.ProcessModifiers.trackingLST_cff import trackingLST
from Configuration.ProcessModifiers.trackingMkFitHighPtTripletStep_cff import trackingMkFitHighPtTripletStep
from Configuration.Eras.Modifier_trackingPhase2PU140_cff import trackingPhase2PU140

(trackingPhase2PU140 & trackingMkFitHighPtTripletStep & seedingLST & trackingLST).toModify(lstProducer,
    ptCut = cms.double(0.6),
    ptCutLabel = cms.string('0.6'),
    nopLSDupClean = cms.bool(True),
    tcpLSTriplets = cms.bool(True)
)
(trackingPhase2PU140 & trackingMkFitHighPtTripletStep & seedingLST & trackingLST).toModify(lstModulesDevESProducer,
    ptCutLabel = cms.string('0.6')
)

lstProducerTask = cms.Task(lstModulesDevESProducer, lstProducer)
