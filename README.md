# Instructions for Setting Up CMSSW Project with mkFit, LST, and Other Packages

These instructions guide you on how to set up the CMSSW environment with the required modifications for **mkFit** and **LST**.

### 1. Create a New CMSSW Environment with requirements from https://cmshltupgrade.docs.cern.ch/RunningInstructions/
```bash
cmsrel CMSSW_15_1_0_pre1
cd CMSSW_15_1_0_pre1/src
cmsenv
git cms-init
# Apply central requirements suggested in the HLT upgrade documentation
git cherry-pick 46e6df9e008eaa1a8580cef75e09492ba65b124c ab16f49a140d7561ce7f1b9242ac7e1e94055b97 bafa98a8f6b8b9cfff885b27e2aab329d9fd795d # Adding #47550
git cherry-pick 17341dd78cce17b2f1fa1e425ddda5436f3bfc22 db9128cd78896462f3b1897e2e99f34e17ff2105 # Adding #47616
git cms-addpkg RecoHGCal/TICL
cd RecoHGCal/TICL
git clone -b PFN_models https://github.com/Moanwar/RecoHGCal-TICL.git data # Adding TICLv5 ML models
cd ../..
git-cms-addpkg RecoTracker/MkFit
git-cms-addpkg RecoTracker/MkFitCore
git-cms-addpkg RecoTracker/MkFitCMS
git-cms-addpkg HLTrigger/Configuration
git clone https://github.com/cms-data/RecoTracker-MkFit.git RecoTracker/MkFit/data
git-cms-addpkg RecoTracker/LST
git cms-remote add bdanzi
git cherry-pick -m 1 b8415a9ea0552f16f98d95481332324a5abeb387
git cherry-pick ea18903cbc83d27778d600ec5d9c141d7623b733
scram build -j 12
```

### 2. mkFit json changes needed needed:
```bash
# "m_requires_seed_hit_sorting": true in RecoTracker/MkFit/data/mkfit-phase2-initialStep.json
emacs -nw RecoTracker/MkFit/data/mkfit-phase2-initialStep.json 
```

### 3. HLT step
```bash
# Larger dataset (TTBar PU 500 events) in /home/users/bdanzi/Phase2/CMSSW_15_1_0_pre1/src/output_Phase2_L1T.root
cmsDriver.py Phase2 -s L1P2GT,HLT:75e33 --processName=HLTX \
--conditions auto:phase2_realistic_T33 \
--geometry ExtendedRun4D110 \
--era Phase2C17I13M9 \
--eventcontent FEVTDEBUGHLT \
--customise SLHCUpgradeSimulations/Configuration/aging.customise_aging_1000,HLTrigger/Configuration/customizePhase2HLTTracking_Alpaka_SingleIteration_LST.customizePhase2HLTMkFitInitialStepTracks \
--filein file:/home/users/evourlio/LSTDevelopmentAreas/CMSSW_15_1_0_pre1/src/output_Phase2_L1T.root \
--fileout file:output_Phase2_L1T_LSTSeeds_Mkfit.root \
--inputCommands='keep *, drop *_hlt*_*_HLT, drop triggerTriggerFilterObjectWithRefs_l1t*_*_HLT' \
--procModifiers alpaka,singleIterPatatrack,trackingLST,seedingLST \
-n 100 --nThreads 8\
```

### 4. DQM and VALIDATION step
```bash
cmsDriver.py DQM -s VALIDATION:hltMultiTrackValidation \
--conditions auto:phase2_realistic_T33 \
--geometry ExtendedRun4D110 \
--era Phase2C17I13M9 \
--datatier DQMIO \
--eventcontent DQM \
--filein file:output_Phase2_L1T_LSTSeeds_Mkfit.root \
--hltProcess HLTX \
--fileout DQM.root \
-n 100 --nThreads 8 \
--procModifiers alpaka,singleIterPatatrack,trackingLST,seedingLST
```

### 5. HARVEST step
```bash
cmsDriver.py HARVEST -s HARVESTING:@trackingOnlyValidation+@trackingOnlyDQM+postProcessorHLTtrackingSequence \
--filein file:DQM.root \
--scenario pp \
--filetype DQM \
--conditions auto:phase2_realistic_T33 \
--mc -n 100
```

