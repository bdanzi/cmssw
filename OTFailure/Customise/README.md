# Phase-2 HLT tracking with tracker failures: scenarios and fixes

This package and the commits under it contain everything needed to rerun the tracker-failure study:
- inject a failure (dead channels, dead modules or layers, random hit loss) in the digitization;
- run the Phase-2 HLT tracking (CA-OT → LST → mkFit, ITACA → LST → mkFit, or Legacy), with or without the fixes;
- validate the result with the HLT MultiTrackValidator.

Results and slides: http://uaf-3.t2.ucsd.edu/~bdanzi/plots_OTFailureScenarios_HLT_pre3_v3/ (main page, links to all result sets v2–v12).

## Branches

The same commits exist on three bases:

| Branch | Base | Use |
|---|---|---|
| `TrackerFailureScenarios_20_1_0_pre4` | `CMSSW_20_1_0_pre4` + ITACA (cms-sw/cmssw#51915) + ITACA data | everything, ITACA included (main branch) |
| `TrackerFailureScenarios_20_1_0_pre4_LSTupdate` | as above + cms-sw/cmssw#52011 (LST T5/T4 DNN retraining) + #52015 (mkFit/LST step fixes) | same, with the LST/mkFit updates merged in master after pre4 |
| `TrackerFailureScenarios_20_1_0_pre3` | `CMSSW_20_1_0_pre3` | reproduces the published pre3 numbers exactly; no ITACA |

Most results of the study were produced in pre3. In pre4 the CA-OT chain loses slightly less with a dead layer: TBPS L1 −6.3% instead of −7.6%, TBPS L2 −5.1% instead of −5.8%.

In the LSTupdate branch the T5 DNN runs after the r-z check and there is no T5 tight flag any more, so the DNN bypass only skips the DNN rejection of gap T5s. The new T4 DNN is not bypassed.

## Setup

```bash
cmsrel CMSSW_20_1_0_pre4            # CMSSW_20_1_0_pre3 for the pre3 branch
cd CMSSW_20_1_0_pre4/src
cmsenv
git cms-init
git cms-checkout-topic -u bdanzi:TrackerFailureScenarios_20_1_0_pre4   # or _pre4_LSTupdate, _pre3
scram b -j 16
```

The default reconstruction does not change, because every addition is switched off by default:
- the digitizer kills nothing unless a scenario customisation asks for it;
- `MeasurementTrackerEventProducer` and `MkFitEventOfHitsProducer` read the payload only when `phase2OTBadModulesFromDB` / `usePhase2OTBadModuleDB` are set;
- the LST `deadModules` list is empty, so the module map has no skip connections, and the T3 and DNN gap code paths cannot be reached.

## What the commits add

| Commit | Package(s) | Content |
|---|---|---|
| ITACA merge | RecoTracker/PixelSeeding and others | Parsifal-2045:itaca_prompt (cms-sw/cmssw#51915) merged on pre4; RecoTracker/PixelSeeding taken from itaca_prompt in the 2 conflicts |
| ITACA data (temporary) | RecoTracker/FinalTrackSelectors/data, RecoTracker/PixelSeeding/data | files of cms-data/RecoTracker-FinalTrackSelectors#16 and RecoTracker-PixelSeeding#1; drop this commit once the externals have them |
| Digitizer: kill modules from payloads | CondCore, CondFormats, CondTools, SimTracker/SiPhase2Digitizer | `SiPhase2OuterTrackerBadModuleRcd` / `SiPhase2InnerTrackerBadModuleRcd`, `SiPhase2BadModuleByHandBuilder` and `KillModules` / `DeadModules_DB` in all Phase-2 digitizer algorithms (cms-sw/cmssw#52130 + stefduponcheel:DigitizerExtensionForBadModules) |
| Dead channels | CalibTracker/SiPhase2TrackerESProducers, SimTracker/SiPhase2Digitizer | fake bad-strip ESSource: `deadDetIds` (whole sensors) and killing of PS-p macro-pixels |
| Hit loss | SimTracker/SiPhase2Digitizer | untracked `HitLossProbability`, `HitLossBPIX1Factor`, `HitLossSeed`: SimHits are dropped before digitization, deterministically |
| Reco aware | RecoTracker/MeasurementDet, RecoTracker/MkFit | dead OT modules from the payload: inactive in the CKF, dead regions in mkFit |
| LST dead-aware map | RecoTracker/LST, RecoTracker/LSTCore | `LSTModulesDevESProducer.deadModules`: skip connections across dead OT sensors |
| LST T3 gap | RecoTracker/LSTCore | r-z cuts for barrel triplets with a layer gap |
| LST gap switches | RecoTracker/LST, RecoTracker/LSTCore | `gapT3RZ`, `gapDNNBypass` parameters of `LSTModulesDevESProducer` (default True), stored as `gapFlags` in the modules SoA |
| LST DNN gap bypass | RecoTracker/LSTCore | T3/T5 with a gap skip the DNN and get the tight flag (in pre4 placed after the T5 r-z check, which moved after the dBeta cuts) |
| OTFailure/Customise | new package | customisations, payloads, module lists, dumpers, `test/runScenario.sh` |

## Failure scenarios (DIGI step)

| `--failure` | Customisation | What is dead |
|---|---|---|
| `Baseline` | none | nothing |
| `SSide{1,5,10,25,50}Pct` | `customizeOTFailureScenarios.customiseSSide<P>Pct` (+ `customiseRestoreBiasRail`) | random strips of PS-s and 2S sensors |
| `PSide{1,5,10,25,50}Pct` | `customizeOTFailureScenarios.customisePSide<P>Pct` (+ `customiseRestoreBiasRail`) | random PS-p macro-pixels |
| `DeadModules{1,5,10}Pct` | `customizeOTFailureScenarios.customisePayloadDeadModules<P>Pct` | 132 / 660 / 1320 random OT modules |
| `DeadPhiSector` | `customisePayloadDeadPhiSector` | 696 OT modules, 0 ≤ φ < 40°, z > 0 |
| `DeadLayerTBPS1`, `DeadLayerTBPS2` | `customisePayloadDeadLayerTBPS1/2` | the first / second OT barrel layer (558 / 910 modules) |
| `DeadITModules{1,5}Pct` | `customisePayloadDeadITModules<P>Pct` | 39 / 195 random IT modules |
| `StefanExample` | `customisePayloadStefanExample` | 2 OT + 3 IT modules (cms-data/CondTools-SiPhase2Tracker#4 lists) |
| `HitLoss{1,3,5}PctBPIX1x{1,3}` | `customizeHitLoss.customiseHitLoss<P>PctBPIX1x<F>` | each SimHit lost with probability p (p × F in BPIX L1), IT and OT |

The payload scenarios read `data/payloads/<Scenario>.db`. These files were built with `test/buildBadModulePayload_cfg.py` from `data/badModuleLists/`. To try a new list, build its payload with that cfg and point `OTFAILURE_DATA_DIR` to a directory with the same layout (`payloads/`, `badModuleLists/`); no rebuild is needed.

`customizeOTFailureScenarios.setChunk(process, chunk, nev)` selects events `[chunk·nev, (chunk+1)·nev)` and fixes all random seeds from the chunk index. Every scenario then sees the same signal and pileup, so results can be compared event by event.

## Fixes (HLT step)

| `--fixes` | Customisation | Effect | Result in the study (100 events, hltGeneral) |
|---|---|---|---|
| `aware` | `customizeRecoAware.customiseRecoAware<Scenario>` | CKF and mkFit read the dead OT modules (IT: `SiPixelQualityRcd`) | Legacy, TBPS L1 dead: −7.2% → −0.8% |
| `caotskip` | `customizeCAOTSkip.customiseCAOTSkipTBPS1/2`; with `--chain ITACA`: `customiseITACASkipTBPS1/2` | layer pairs that skip the dead layer, with cuts scaled by the lever arm | CA-OT (pre3): TBPS1 −7.6% → −4.4%, TBPS2 −5.8% → −3.0%; ITACA (pre4): −4.7% → −2.5%, −4.0% → −2.7% |
| `recpls` | `customizeRecoverPLS.customiseRecoverPixelOnlySeeds` | pixel-only CA tracks merged with the CA-OT (or ITACA) tracks as LST/mkFit seeds | CA-OT (pre3) with `caotskip`: TBPS1 −2.8%, TBPS2 −1.6%; fakes +0.5 points |
| `lstmap` | `customizeLSTDeadModules.customiseLSTDeadModules<Scenario>` | LST dead-aware module map + T3 r-z fix + DNN bypass for objects with a gap | no gain: TBPS2 with `caotskip` −3.0% → −4.0% |
| `lstmapt3` | + `customiseLSTGapT3Only` (`gapDNNBypass = False`) | map + T3 r-z fix only | TBPS2 with `caotskip`: −3.4% |
| `lstmaponly` | + `customiseLSTGapMapOnly` (`gapT3RZ = gapDNNBypass = False`) | map only: gap triplets are still rejected by the r-z cuts | TBPS2 with `caotskip`: −3.3% |
| `caotskipdisks`, `caotskipfull` | `customiseCAOTSkipTBPS1Disks`, `customiseCAOTSkipTBPS1Full` | v10: + pairs from disks 4–5, + BPIX L3 → TBPS2 | see summary_v10.txt |

Other customisations in the package:
- `customizeOTFailureScenarios.customiseDeadModules<P>Pct` etc.: dead modules via the private `deadDetIds`, the v3 reference before the payloads existed.
- `customizeHitLoss.customisePromptValidation`: MTV restricted to prompt TrackingParticles (dxy < 0.1 cm).

## Every configuration of the study

All the configurations of the published result sets can be run with `test/runScenario.sh`. Options not listed take their default: `--chain Default`, no fixes, bias rail on, all TPs. Every set used 100 events (10 chunks), and from v7 on each was validated both inclusive and with `--prompt`.

| Set | Configurations | `runScenario.sh` options |
|---|---|---|
| v2 | S/P dead channels 1, 5, 10%, bias rail off; bias rail on vs off | `--failure {SSide,PSide}{1,5,10}Pct --biasrail off`; `--failure Baseline [--biasrail off]` |
| v3 | S/P 10, 25, 50%; private holes OT 1/5/10%, φ sector, TBPS1; bias rail off | `--failure {SSide,PSide}{10,25,50}Pct --biasrail off`; `--failure Private{DeadModules{1,5,10}Pct,DeadPhiSector,DeadLayerTBPS1} --biasrail off` |
| v5 | same as v3 with the bias rail on; Default and Legacy | as v3 without `--biasrail off`, `--chain Default` / `Legacy` |
| v6 | payload dead modules: OT 1/5/10%, φ sector, TBPS1, IT 1/5%, StefanExample; Default and Legacy | `--failure {DeadModules{1,5,10}Pct,DeadPhiSector,DeadLayerTBPS1,DeadITModules{1,5}Pct,StefanExample} [--chain Legacy]` |
| v7 | hit loss 1/3/5%, BPIX1 ×1/×3; Default, ITACA, Legacy | `--failure HitLoss{1,3,5}PctBPIX1x{1,3} --chain {Default,ITACA,Legacy}` (ITACA standalone = `hltPhase2Pixel` of the ITACA run) |
| v8 | v6 scenarios with reco aware; LST map on 10% and φ sector | `--fixes aware [--chain Legacy]`; `--failure {DeadModules10Pct,DeadPhiSector} --fixes lstmaponly` |
| v9 | CA-OT skip pairs, TBPS1 and baseline | `--failure {DeadLayerTBPS1,Baseline} --fixes aware,caotskip` |
| v10 | CA-OT skip variants | `--fixes aware,caotskipdisks`, `--fixes aware,caotskipfull` |
| v11 | TBPS2: unaware/aware for every chain, CA-OT and ITACA skip pairs, LST map, map + T3 | `--failure DeadLayerTBPS2 [--chain {ITACA,Legacy}] [--fixes aware]`; `--fixes aware,caotskip`; `--chain ITACA --fixes caotskip`; `--fixes lstmaponly[,caotskip]`; `--fixes lstmapt3[,caotskip]` (also on 10% and Baseline) |
| v12 | LST DNN bypass, pixel-only seed recovery, combinations | `--fixes lstmap[,caotskip]`; `--fixes aware,recpls`; `--fixes aware,caotskip,recpls`; `--fixes caotskip,recpls,lstmap` (v12 "Best2") |

v4 (LST skip with private holes) was never completed and has no results. The CPU/GPU timing (v9, v10) uses the configurations above, with the FastTimerService scripts of the study repository (`scripts/local/timing_v9.sh`, `timing_v10_gpu.sh`).

## Running a scenario

`test/runScenario.sh` runs DIGI with the failure, then the HLT with the chain and fixes, then MTV and harvesting:

```bash
mkdir run && cd run
SIG=$(dasgoclient -query "file dataset=/RelValTTbar_14TeV/CMSSW_20_0_0_pre1-PU_150X_mcRun4_realistic_v1_STD_D121_RegeneratedGS_PU-v1/GEN-SIM-DIGI-RAW" | head -1)
dasgoclient -query "file dataset=/RelValMinBias_14TeV/CMSSW_20_0_0_pre1-150X_mcRun4_realistic_v1_STD_RegeneratedGS_D121_noPU-v1/GEN-SIM" \
  | sed 's#^#root://cms-xrd-global.cern.ch/#' > minbias.txt

# dead TBPS L2, best LST + mkFit configuration, events 0-9
$CMSSW_BASE/src/OTFailure/Customise/test/runScenario.sh --failure DeadLayerTBPS2 --fixes aware,caotskip,recpls \
  --input root://cms-xrd-global.cern.ch/$SIG --pileup-list minbias.txt --chunk 0 --nev 10

# same digis, ITACA with its skip pairs and the seed recovery
$CMSSW_BASE/src/OTFailure/Customise/test/runScenario.sh --failure DeadLayerTBPS2 --chain ITACA --fixes caotskip,recpls \
  --digi step2_DeadLayerTBPS2.root --chunk 0

# same digis, Legacy chain
$CMSSW_BASE/src/OTFailure/Customise/test/runScenario.sh --failure DeadLayerTBPS2 --chain Legacy --fixes aware \
  --digi step2_DeadLayerTBPS2.root --chunk 0
```

Already digitized samples exist for the payload scenarios: `Baseline`, `StefanExample`, `DeadModules{1,5,10}Pct`, `DeadPhiSector`, `DeadLayerTBPS1`, `DeadLayerTBPS2`, `DeadITModules{1,5}Pct`. Each has 10 chunks of 10 events, TTbar PU200, and they contain the same events as above. Start from the HLT with them:

```bash
X=root://redirector.t2.ucsd.edu:1095//store/user/bdanzi/OTFailureScenarios_pre3/samples_v6
$CMSSW_BASE/src/OTFailure/Customise/test/runScenario.sh --failure DeadLayerTBPS1 --fixes aware,caotskip,recpls \
  --digi $X/DeadLayerTBPS1/DeadLayerTBPS1_TTbar14TeV_D121_PU200_chunk0.root --chunk 0
```

The study always uses all 100 events: 10 chunks, then one harvesting of the 10 DQM files. Statistical errors on the global efficiency are about 0.1–0.2%.

```bash
for c in 0 1 2 3 4 5 6 7 8 9; do
  $CMSSW_BASE/src/OTFailure/Customise/test/runScenario.sh --failure DeadLayerTBPS1 --fixes aware,caotskip,recpls \
    --digi $X/DeadLayerTBPS1/DeadLayerTBPS1_TTbar14TeV_D121_PU200_chunk$c.root --chunk $c --steps hlt,val &
done; wait
cmsDriver.py HARVEST -s HARVESTING:@trackingOnlyValidation+@trackingOnlyDQM+postProcessorHLTtrackingSequence \
  --filein $(ls DQM_DeadLayerTBPS1_*_chunk*.root | sed 's#^#file:#' | paste -sd,) \
  --scenario pp --filetype DQM --conditions auto:phase2_realistic_T35 --mc -n -1
```

Each job takes about 2 GB of memory; the DIGI step with PU200 takes more, so run at most a few in parallel.

## ITACA

`--chain ITACA` runs `--procModifiers phase2CAStubs`: ITACA builds the pixel and OT-stub tracks that seed LST → mkFit. With ITACA, `caotskip` adds the ITACA skip pairs (`customiseITACASkipTBPS1/2`). `recpls` works in the same way as for CA-OT: the pixel-only CA is rebuilt from the layer tables of the release, so it no longer depends on the pre3 module `_hltPhase2PixelTracksSoANonCAExtended`.

The samples above were digitized in pre3. The study ran ITACA and the pre4 CA-OT chain on these same samples (result sets v9–v11), so they can be used as HLT input in this branch as well.

## Tools

- `plugins/OTModuleDumper`, `plugins/OTBadChannelDumper` with `test/dumpOTModules_cfg.py`, `test/dumpOTBadChannels_cfg.py`: dump the D121 module list (`data/OTModules_D121.txt`) and the dead channels of a configuration.
- `test/buildBadModulePayload_cfg.py`: `cmsRun buildBadModulePayload_cfg.py <ot_list|none> <it_list|none> <out.db>`.
