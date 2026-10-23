#!/bin/bash
# Run one tracker-failure scenario through DIGI (with the failure), the standard HLT tracking and MTV.
# Tracker side only: the reconstruction is not told about the dead channels, modules or lost hits.
# Run from an empty directory inside a cmsenv'ed area of this branch.
#
#   runScenario.sh --failure <name> [--chain Default|Legacy] [--chunk N] [--nev N]
#                  [--input file.root] [--pileup-list minbias.txt] [--digi file.root] [--steps digi,hlt,val,harvest]
#
#   --failure      see the README: Baseline, SSide<P>Pct, PSide<P>Pct, DeadModules<P>Pct, DeadPhiSector,
#                  DeadLayerTBPS1, DeadLayerTBPS2, DeadITModules<P>Pct, StefanExample, HitLoss<P>PctBPIX1x<F>,
#                  Private{DeadModules<P>Pct,DeadPhiSector,DeadLayerTBPS1} (v3/v5 holes from the fake ESSource)
#   --biasrail     on (default) or off: PS-p bias-rail inefficiency in the DIGI step (off = v2/v3)
#   --chain        Default = CA-OT -> LST -> mkFit (default), Legacy = hltPhase2LegacyTracking
#   --prompt       validate prompt TrackingParticles only (dxy < 0.1 cm) instead of all
#   --chunk/--nev  events [chunk*nev, (chunk+1)*nev) of the input, with seeds fixed by the chunk (default 0 / 10)
#   --input        GEN-SIM(-DIGI-RAW) signal file for the DIGI step
#   --pileup-list  text file with the MinBias GEN-SIM files for PU200
#   --digi         skip the DIGI step and run the HLT on this file (e.g. the samples_v6 files on xrootd)
#   --steps        subset of digi,hlt,val,harvest (default: all; digi is skipped when --digi is given).
#                  To merge chunks, run without harvest and harvest all DQM_*.root files together (see the README)
#   --check        only build the configurations and load them with edmConfigDump (no cmsRun)
set -e

FAILURE=""; CHAIN=Default; CHUNK=0; NEV=10; INPUT=""; PULIST=""; DIGI=""; STEPS=digi,hlt,val,harvest; CHECK=""; BIASRAIL=on; PROMPT=""
while [ $# -gt 0 ]; do
  case $1 in
    --failure)     FAILURE=$2; shift 2 ;;
    --chain)       CHAIN=$2; shift 2 ;;
    --chunk)       CHUNK=$2; shift 2 ;;
    --nev)         NEV=$2; shift 2 ;;
    --input)       INPUT=$2; shift 2 ;;
    --pileup-list) PULIST=$2; shift 2 ;;
    --digi)        DIGI=$2; STEPS=${STEPS/digi,/}; shift 2 ;;
    --steps)       STEPS=$2; shift 2 ;;
    --check)       CHECK=1; shift ;;
    --biasrail)    BIASRAIL=$2; shift 2 ;;
    --prompt)      PROMPT=1; shift ;;
    *) echo "unknown option $1"; exit 2 ;;
  esac
done
[ -n "$FAILURE" ] || { echo "--failure is required"; exit 2; }
[ -n "$CMSSW_BASE" ] || { echo "run cmsenv first"; exit 2; }
has_step() { [[ ",$STEPS," == *",$1,"* ]]; }
# run_cfg <cfg> <log>: cmsRun, or with --check only load the configuration
run_cfg() {
  if [ -n "$CHECK" ]; then
    edmConfigDump $1 > ${1%.py}_dump.py 2> $2 || { cat $2; exit 1; }
    echo "CHECKOK $1"
  else
    cmsRun $1 > $2 2>&1
  fi
}

CU=OTFailure/Customise
COMMON="--conditions auto:phase2_realistic_T35 --geometry ExtendedRun4D121 --era Phase2C22I13M9 --nThreads 1"

# ---- DIGI customisation for the failure
# the private dead-channel and hole customisations switch the bias rail off; restore it unless --biasrail off
RESTORE=",$CU/customizeOTFailureScenarios.customiseRestoreBiasRail"
[ $BIASRAIL = off ] && RESTORE=""
case $FAILURE in
  Baseline)
    if [ $BIASRAIL = off ]; then DIGI_CUST="--customise $CU/customizeOTFailureScenarios.customiseBaseline"; else DIGI_CUST=""; fi ;;
  SSide*Pct|PSide*Pct)         DIGI_CUST="--customise $CU/customizeOTFailureScenarios.customise$FAILURE$RESTORE" ;;
  PrivateDeadModules*Pct|PrivateDeadPhiSector|PrivateDeadLayerTBPS1)
                               DIGI_CUST="--customise $CU/customizeOTFailureScenarios.customise${FAILURE#Private}$RESTORE" ;;
  DeadModules*Pct|DeadPhiSector|DeadLayerTBPS1|DeadLayerTBPS2|DeadITModules*Pct|StefanExample)
                               DIGI_CUST="--customise $CU/customizeOTFailureScenarios.customisePayload$FAILURE" ;;
  HitLoss*)                    DIGI_CUST="--customise $CU/customizeHitLoss.customise$FAILURE" ;;
  *) echo "unknown failure $FAILURE"; exit 2 ;;
esac

# ---- HLT chain (no reconstruction-side customisation: the HLT does not know about the failure)
case $CHAIN in
  Default) PM="" ;;
  Legacy)  PM="--procModifiers hltPhase2LegacyTracking" ;;
  *) echo "unknown chain $CHAIN"; exit 2 ;;
esac
HLT_CUST="SLHCUpgradeSimulations/Configuration/aging.customise_aging_1000"

VAL_CUST=""
[ -n "$PROMPT" ] && VAL_CUST="--customise $CU/customizeHitLoss.customisePromptValidation"
BR_SUFFIX=""
[ $BIASRAIL = off ] && BR_SUFFIX=_BRoff
PROMPT_SUFFIX=""
[ -n "$PROMPT" ] && PROMPT_SUFFIX=_prompt
DIGINAME=${FAILURE}${BR_SUFFIX}
TAG=${DIGINAME}_${CHAIN}${PROMPT_SUFFIX}_chunk$CHUNK

if has_step digi; then
  [ -n "$INPUT" ] && [ -n "$PULIST" ] || { echo "the DIGI step needs --input and --pileup-list"; exit 2; }
  cmsDriver.py step2 -s DIGI:pdigi_valid,L1TrackTrigger,L1,DIGI2RAW --datatier GEN-SIM-DIGI-RAW --eventcontent FEVTDEBUGHLT \
    $COMMON -n $NEV --pileup AVE_200_BX_25ns --pileup_input filelist:$PULIST $DIGI_CUST \
    --customise_commands "from OTFailure.Customise.customizeOTFailureScenarios import setChunk; process = setChunk(process, $CHUNK, $NEV)" \
    --processName DIGIOT --inputCommands "keep *,drop *_*_*_HLT" \
    --filein file:$INPUT --fileout file:step2_$DIGINAME.root --python_filename step2_${DIGINAME}_cfg.py --no_exec
  run_cfg step2_${DIGINAME}_cfg.py step2_$DIGINAME.log
  DIGI=file:step2_$DIGINAME.root
fi

if has_step hlt; then
  [ -n "$DIGI" ] || { echo "no DIGI input: run the digi step or give --digi"; exit 2; }
  [[ $DIGI == *:* ]] || DIGI=file:$DIGI
  cmsDriver.py Phase2 -s L1P2GT,HLT:75e33_trackingOnly --processName=HLTX $COMMON --eventcontent FEVTDEBUGHLT $PM \
    --customise $HLT_CUST --mc -n -1 \
    --filein $DIGI --fileout file:step3_$TAG.root --python_filename step3_${TAG}_cfg.py --no_exec
  run_cfg step3_${TAG}_cfg.py step3_$TAG.log
fi

if has_step val; then
  cmsDriver.py DQM -s VALIDATION:hltMultiTrackValidation $COMMON --datatier DQMIO --eventcontent DQM $PM $VAL_CUST \
    --filein file:step3_$TAG.root --hltProcess HLTX --fileout file:DQM_$TAG.root -n -1 \
    --python_filename step4_${TAG}_cfg.py --no_exec
  run_cfg step4_${TAG}_cfg.py step4_$TAG.log
fi

if has_step harvest; then
  cmsDriver.py HARVEST -s HARVESTING:@trackingOnlyValidation+@trackingOnlyDQM+postProcessorHLTtrackingSequence \
    --filein file:DQM_$TAG.root --scenario pp --filetype DQM --conditions auto:phase2_realistic_T35 --mc -n -1 \
    --python_filename harvest_${TAG}_cfg.py --no_exec
  run_cfg harvest_${TAG}_cfg.py harvest_$TAG.log
  if [ -z "$CHECK" ]; then
    mv DQM_V0001_R000000001__Global__CMSSW_X_Y_Z__RECO.root MTV_$TAG.root
    echo "MTV histograms: MTV_$TAG.root (plots: makeTrackValidationPlots.py --png MTV_$TAG.root)"
  fi
fi
