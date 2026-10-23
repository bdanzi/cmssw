# Phase-2 tracker failure scenarios (tracker side only)

Branch `TrackerFailureScenarios_20_1_0_pre4_TrackerOnly`, on top of vanilla `CMSSW_20_1_0_pre4`.

It simulates tracker failures in the DIGI step only: dead strips and macro-pixels, dead OT and IT modules from
bad-module payloads, and random hit loss. The HLT reconstruction is the standard one and is **not aware** of the
failures. Fixes on the reconstruction side (reco-aware CKF/mkFit, CA-OT skip pairs, LST dead-aware map, seed
recovery) and ITACA are in the other branches (`TrackerFailureScenarios_20_1_0_pre3`, `_pre4`, `_pre4_LSTupdate`).

## Setup

```bash
cmsrel CMSSW_20_1_0_pre4
cd CMSSW_20_1_0_pre4/src
cmsenv
git cms-init
git cms-checkout-topic -u bdanzi:TrackerFailureScenarios_20_1_0_pre4_TrackerOnly
git cms-checkdeps -a -A     # the payload records add headers in CondFormats/DataRecord
scram b -j 16
```

Nothing changes by default: the digitizer kills nothing unless a scenario customisation asks for it.

## What the commits add

| Commit | Package(s) | Content |
|---|---|---|
| Digitizer: kill modules from payloads | CondCore, CondFormats, CondTools, SimTracker/SiPhase2Digitizer | `SiPhase2OuterTrackerBadModuleRcd` / `SiPhase2InnerTrackerBadModuleRcd`, `SiPhase2BadModuleByHandBuilder` and `KillModules` / `DeadModules_DB` in all Phase-2 digitizer algorithms (cms-sw/cmssw#52130 + stefduponcheel:DigitizerExtensionForBadModules) |
| Dead channels | CalibTracker/SiPhase2TrackerESProducers, SimTracker/SiPhase2Digitizer | fake bad-strip ESSource: `deadDetIds` (whole sensors) and killing of PS-p macro-pixels |
| Hit loss | SimTracker/SiPhase2Digitizer | untracked `HitLossProbability`, `HitLossBPIX1Factor`, `HitLossSeed`: SimHits are dropped before digitization, deterministically |
| OTFailure/Customise | new package | scenario customisations, payloads, module lists, dumpers, `test/runScenario.sh` |

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
| `Private{DeadModules{1,5,10}Pct,DeadPhiSector,DeadLayerTBPS1}` | `customizeOTFailureScenarios.customise<Scenario>` | v3/v5 holes: whole sensors made dead through the fake bad-strip ESSource |
| `HitLoss{1,3,5}PctBPIX1x{1,3}` | `customizeHitLoss.customiseHitLoss<P>PctBPIX1x<F>` | each SimHit lost with probability p (p × F in BPIX L1), IT and OT |

The payload scenarios read `data/payloads/<Scenario>.db`. These files were built with `test/buildBadModulePayload_cfg.py` from `data/badModuleLists/`. To try a new list, build its payload with that cfg and point `OTFAILURE_DATA_DIR` to a directory with the same layout (`payloads/`, `badModuleLists/`); no rebuild is needed.

`customizeOTFailureScenarios.setChunk(process, chunk, nev)` selects events `[chunk·nev, (chunk+1)·nev)` and fixes all random seeds from the chunk index. Every scenario then sees the same signal and pileup, so results can be compared event by event.

`--biasrail off` switches off the PS-p bias-rail inefficiency in the DIGI step (as in the v2/v3 results).

## Running a scenario

`test/runScenario.sh` runs DIGI with the failure, the standard HLT tracking (`--chain Default` = CA-OT → LST → mkFit,
or `--chain Legacy`), MTV and harvesting:

```bash
mkdir run && cd run
SIG=$(dasgoclient -query "file dataset=/RelValTTbar_14TeV/CMSSW_20_0_0_pre1-PU_150X_mcRun4_realistic_v1_STD_D121_RegeneratedGS_PU-v1/GEN-SIM-DIGI-RAW" | head -1)
dasgoclient -query "file dataset=/RelValMinBias_14TeV/CMSSW_20_0_0_pre1-150X_mcRun4_realistic_v1_STD_RegeneratedGS_D121_noPU-v1/GEN-SIM" \
  | sed 's#^#root://cms-xrd-global.cern.ch/#' > minbias.txt

# 10% dead PS-p macro-pixels, events 0-9
$CMSSW_BASE/src/OTFailure/Customise/test/runScenario.sh --failure PSide10Pct \
  --input root://cms-xrd-global.cern.ch/$SIG --pileup-list minbias.txt --chunk 0 --nev 10

# same digis, Legacy chain
$CMSSW_BASE/src/OTFailure/Customise/test/runScenario.sh --failure PSide10Pct --chain Legacy --digi step2_PSide10Pct.root --chunk 0
```

The study always uses 100 events: run chunks 0-9 with `--steps digi,hlt,val`, then harvest the 10 DQM files together:

```bash
cmsDriver.py HARVEST -s HARVESTING:@trackingOnlyValidation+@trackingOnlyDQM+postProcessorHLTtrackingSequence \
  --filein $(ls DQM_PSide10Pct_*_chunk*.root | sed 's#^#file:#' | paste -sd,) \
  --scenario pp --filetype DQM --conditions auto:phase2_realistic_T35 --mc -n -1
```

The DIGI step with PU200 takes several GB of memory: run only a few chunks in parallel.

## Tools

- `plugins/OTModuleDumper`, `plugins/OTBadChannelDumper` with `test/dumpOTModules_cfg.py`, `test/dumpOTBadChannels_cfg.py`: dump the D121 module list (`data/OTModules_D121.txt`) and the dead channels of a configuration.
- `test/buildBadModulePayload_cfg.py`: `cmsRun buildBadModulePayload_cfg.py <ot_list|none> <it_list|none> <out.db>`.
