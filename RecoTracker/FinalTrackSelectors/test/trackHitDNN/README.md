# Hit-level track-selection DNNs (TrackHitTfClassifier)

Track-selection DNNs with the 29 `TrackTfClassifier` inputs plus 10 hit-level inputs, computed on the
track collection of each iteration:

| index | hit-level feature |
|---|---|
| 0, 1 | pixel / strip clusters shared with another track of the same iteration |
| 2 | maximum number of clusters shared with a single other track |
| 3, 4 | mean / maximum pixel cluster charge (ke) |
| 5, 6, 7 | mean pixel cluster sizeX, mean / maximum sizeY |
| 8, 9 | mean strip cluster charge (ADC), mean strip cluster width |

The graphs (`MkFitHit_Run3_2024.pb`, `CKFHit_Run3_2024.pb`, `MkFitPixelLessOnlyHit_Run3_2024.pb`) are in
cms-data `RecoTracker-FinalTrackSelectors/TrackTfClassifier`; the working points are in
`RecoTracker/Configuration/python/customiseLowPtTracking.py` (`HIT_DNN_CUTS`).

## Reproducing the training

Release CMSSW_15_0_18, `el8_amd64_gcc12`.

### 1. Training sample: 2024 TTbar with pile-up, 48 chunks of 50 events

Pile-up input: `/RelValMinBias_14TeV/CMSSW_14_1_0_pre7-140X_mcRun3_2024_realistic_v21_STD_RegeneratedGS_2024_noPU-v1/GEN-SIM`
(file list in `minbias.txt`). Use a different, fixed seed for each chunk (`SEED=<chunk number + 1>`); `resetSeeds`
sets all the engine seeds of the job from it.

```bash
cmsDriver.py TTbar_14TeV_TuneCP5_cfi -s GEN,SIM -n 50 --conditions auto:phase1_2024_realistic \
  --geometry DB:Extended --era Run3_2024 --beamspot DBrealistic --datatier GEN-SIM --eventcontent FEVTDEBUG \
  --fileout file:step1.root --python_filename step1_cfg.py --nThreads 4 --no_exec \
  --customise_commands "from IOMC.RandomEngine.RandomServiceHelper import RandomNumberServiceHelper; RandomNumberServiceHelper(process.RandomNumberGeneratorService).resetSeeds($SEED)"
cmsRun step1_cfg.py

cmsDriver.py step2 -s DIGI:pdigi_valid,L1,DIGI2RAW,HLT:@relval2024 --conditions auto:phase1_2024_realistic \
  --geometry DB:Extended --era Run3_2024 --datatier GEN-SIM-DIGI-RAW -n -1 --eventcontent FEVTDEBUGHLT \
  --pileup Run3_Flat55To75_PoissonOOTPU --pileup_input filelist:minbias.txt --nThreads 4 \
  --filein file:step1.root --fileout file:step2.root \
  --customise_commands "from IOMC.RandomEngine.RandomServiceHelper import RandomNumberServiceHelper; RandomNumberServiceHelper(process.RandomNumberGeneratorService).resetSeeds($SEED)"
```

### 2. Dump the training inputs

```bash
cmsDriver.py step3 -s RAW2DIGI,RECO:reconstruction_trackingOnly,VALIDATION:@trackingOnlyValidation,DQM:@trackingOnlyDQM \
  --conditions auto:phase1_2024_realistic --geometry DB:Extended --era Run3_2024 --datatier DQMIO -n -1 \
  --eventcontent DQM --pileup Run3_Flat55To75_PoissonOOTPU --pileup_input filelist:minbias.txt --nThreads 4 \
  --filein file:step2.root --fileout file:step3_inDQM.root \
  --customise RecoTracker/FinalTrackSelectors/customiseHitFeatDump.customiseHitFeatDump
```

The same `minbias.txt` must be used in step2 and step3 (classic mixing playback). Each chunk writes
`chunk<N>/hit_dump.root`.

### 3. Train

```bash
python3 RecoTracker/FinalTrackSelectors/test/trackHitDNN/trainTrackHitDNN.py \
  --inputs '/path/to/chunk*/hit_dump.root' --train-chunks 0-39 --val-chunks 40-47 --outdir trained
```

The training is deterministic (fixed seed, TensorFlow op determinism): the same dump files give identical
graphs and working points. The script prints the `HIT_DNN_CUTS` entries to copy into
`customiseLowPtTracking.py`; the working points pass the same number of fake tracks as the production
`TrackTfClassifier` working points on the validation chunks.
