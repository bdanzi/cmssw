#! /usr/bin/env cmsRun
# cmsRun trackingMaterialAnalyser_ForPhaseII_FineGrained.py fromDB=False
#
# Groundwork for a KF-oriented re-grouping study of the Phase-2 tracking
# material: runs TrackingMaterialAnalyser with one group per individually
# named sensor volume (404 groups total (374 unchanged + 30 IT Layer1/Layer2 phi-resolved Flipped/Unflipped splits), see
# SimTracker/TrackerMaterialAnalysis/data/trackingMaterialGroups_ForPhaseII/v4/)
# instead of the production one-group-per-layer/disk scheme. The resulting
# per-volume TrackerRadLength/TrackerXi are the basis for deciding which
# neighboring volumes agree closely enough (~5-10%) to be merged back into
# coarser groups.
#
# Input: material.root, produced by
# SimTracker/TrackerMaterialAnalysis/test/trackingMaterialProducer10GeVNeutrino_ForPhaseII.py
# (unchanged -- already targets the current release-default Phase-2 geometry).

###################################################################
# Set default phase-2 settings
###################################################################
import Configuration.Geometry.defaultPhase2ConditionsEra_cff as _settings
_PH2_GLOBAL_TAG, _PH2_ERA = _settings.get_era_and_conditions(_settings.DEFAULT_VERSION)

import FWCore.ParameterSet.Config as cms
from FWCore.ParameterSet.VarParsing import VarParsing

process = cms.Process("MaterialAnalyser",_PH2_ERA)

options = VarParsing('analysis')

options.register('fromDB',
                 False,
                 VarParsing.multiplicity.singleton,
                 VarParsing.varType.bool,
                 'Read Geometry from DB?',
)

options.parseArguments()

if options.fromDB :
   process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
   from Configuration.AlCa.GlobalTag import GlobalTag
   process.GlobalTag = GlobalTag(process.GlobalTag, _PH2_GLOBAL_TAG, '')
else:
   process.load('Configuration.Geometry.GeometryExtendedRun4DefaultReco_cff')

process.load('FWCore.MessageService.MessageLogger_cfi')
process.MessageLogger.files.LogTrackingMaterialAnalysis = dict(threshold = cms.untracked.string('WARNING'))
process.MessageLogger.TrackingMaterialAnalysis=dict()
process.MessageLogger.cerr.threshold = 'WARNING'

# Add our fine-grained (per-sensor-volume) detector grouping to DDD, on top of
# (not instead of) the production per-layer grouping.
process.XMLIdealGeometryESSource.geomXMLFiles.extend(['SimTracker/TrackerMaterialAnalysis/data/trackingMaterialGroups_ForPhaseII/v4/trackingMaterialGroups_ForPhaseII.xml'])

# Analyze and plot the tracking material, using the fine-grained Groups list
process.load("SimTracker.TrackerMaterialAnalysis.trackingMaterialAnalyser_ForPhaseII_FineGrained_v4_cfi")
process.trackingMaterialAnalyser.SplitMode         = "NearestLayer"
process.trackingMaterialAnalyser.SaveParameters    = True
process.trackingMaterialAnalyser.SaveXML           = True
process.trackingMaterialAnalyser.SaveDetailedPlots = True

process.source = cms.Source("PoolSource",
    fileNames = cms.untracked.vstring('file:material.root')
)

process.path = cms.Path(process.trackingMaterialAnalyser)
