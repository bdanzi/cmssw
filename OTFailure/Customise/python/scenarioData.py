import os
#
# Locate the data files of the failure scenarios shipped in OTFailure/Customise/data:
#   payloads/<Scenario>.db               SiPixelQuality-style bad-module payloads (cms-sw/cmssw#52130 format)
#   badModuleLists/bad_modules_<S>.txt   dead OT module detIds used to build them (also read by the LST dead-module map)
#   OTModules_D121.txt, ITModules_D121.txt
# The environment variable OTFAILURE_DATA_DIR, if set, is searched first (e.g. to test new payloads without rebuilding).
#
PACKAGE_DATA = "OTFailure/Customise/data"

def dataFile(relPath):
    dirs = []
    if os.environ.get("OTFAILURE_DATA_DIR"):
        dirs.append(os.environ["OTFAILURE_DATA_DIR"])
    for d in os.environ.get("CMSSW_SEARCH_PATH", "").split(":"):
        if d:
            dirs.append(os.path.join(d, PACKAGE_DATA))
    if os.environ.get("CMSSW_BASE"):
        dirs.append(os.path.join(os.environ["CMSSW_BASE"], "src", PACKAGE_DATA))
    for d in dirs:
        candidate = os.path.join(d, relPath)
        if os.path.exists(candidate):
            return candidate
    raise RuntimeError("%s not found in %s" % (relPath, dirs))

def payloadConnect(scenario):
    return "sqlite_file:" + dataFile("payloads/%s.db" % scenario)

def badModuleList(scenario):
    return [int(line) for line in open(dataFile("badModuleLists/bad_modules_%s.txt" % scenario)) if line.strip()]
