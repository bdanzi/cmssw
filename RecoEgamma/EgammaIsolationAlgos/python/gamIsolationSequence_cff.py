import FWCore.ParameterSet.Config as cms

from RecoEgamma.EgammaIsolationAlgos.gamIsoDeposits_cff import *
from RecoEgamma.EgammaIsolationAlgos.gamIsoFromDeposits_cff import *

#Standard reco sequence with photons
gamIsolationTask = cms.Task(
    gamIsoDepositsTask,  
    gamIsoFromDepositsTask
)
gamIsolationSequence = cms.Sequence(gamIsolationTask)
