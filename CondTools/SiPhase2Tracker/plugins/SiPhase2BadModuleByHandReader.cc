// -*- C++ -*-
//
// Package:    CondTools/SiPhase2BadModuleByHandReader
// Class:      SiPhase2BadModuleByHandReader
//
/**\class SiPhase2BadModuleByHandReader SiPhase2BadModuleByHandReader.cc CondTools/SiPhase2Tracker/plugins/SiPhase2BadModuleByHandReader.cc

 Description: Reads back a SiPixelQuality dead-module payload from the EventSetup and prints each DetId with its module type and any paired sensor. Templated over the record type; OT and IT instances are provided.

 Implementation:
     Verification tool for the builder output. The OT pairing uses a sibling map built from StackGeomDet, and IT Ph2PXB3D pairs use DetId parity.
*/
//
// Original Author:  Stef Duponcheel
//         Created:  Wed, 30 Sep 2026 12:05:11 GMT
//
//

#include <map>
#include <set>
#include <string>

#include "CondFormats/SiPixelObjects/interface/SiPixelQuality.h"
#include "CondFormats/DataRecord/interface/SiPhase2OuterTrackerCondDataRecords.h"
#include "CondFormats/DataRecord/interface/SiPhase2InnerTrackerCondDataRecords.h"

#include "DataFormats/DetId/interface/DetId.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/EventSetup.h"
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/global/EDAnalyzer.h"
#include "FWCore/MessageLogger/interface/MessageLogger.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/ParameterSet/interface/ParameterSetDescription.h"
#include "FWCore/ParameterSet/interface/ConfigurationDescriptions.h"

#include "Geometry/Records/interface/TrackerDigiGeometryRecord.h"
#include "Geometry/TrackerGeometryBuilder/interface/TrackerGeometry.h"
#include "Geometry/CommonTopologies/interface/StackGeomDet.h"

//
// class declaration
//
template <typename RecordT>
class SiPhase2BadModuleByHandReader : public edm::global::EDAnalyzer<> {
public:
  explicit SiPhase2BadModuleByHandReader(const edm::ParameterSet& iConfig)
      : printdebug_(iConfig.getUntrackedParameter<bool>("printDebug", true)),
        geomToken_(esConsumes()),
        badModuleToken_(esConsumes(edm::ESInputTag{"", iConfig.getUntrackedParameter<std::string>("label", "")})) {}

  ~SiPhase2BadModuleByHandReader() override = default;
  void analyze(edm::StreamID, edm::Event const&, edm::EventSetup const&) const override;
  static void fillDescriptions(edm::ConfigurationDescriptions& descriptions);

private:
  static std::string moduleTypeToString(TrackerGeometry::ModuleType type);

  const bool printdebug_;
  const edm::ESGetToken<TrackerGeometry, TrackerDigiGeometryRecord> geomToken_;
  const edm::ESGetToken<SiPixelQuality, RecordT> badModuleToken_;
};

template <typename RecordT>
std::string SiPhase2BadModuleByHandReader<RecordT>::moduleTypeToString(TrackerGeometry::ModuleType type) {
  switch (type) {
    case TrackerGeometry::ModuleType::Ph2SS:
      return "Ph2SS";
    case TrackerGeometry::ModuleType::Ph2PSP:
      return "Ph2PSP";
    case TrackerGeometry::ModuleType::Ph2PSS:
      return "Ph2PSS";
    case TrackerGeometry::ModuleType::Ph2PXB:
      return "Ph2PXB";
    case TrackerGeometry::ModuleType::Ph2PXF:
      return "Ph2PXF";
    case TrackerGeometry::ModuleType::Ph2PXB3D:
      return "Ph2PXB3D";
    default:
      return "unknown";
  }
}

template <typename RecordT>
void SiPhase2BadModuleByHandReader<RecordT>::analyze(edm::StreamID,
                                                     edm::Event const&,
                                                     edm::EventSetup const& iSetup) const {
  const auto& tkGeom = iSetup.getData(geomToken_);
  const auto& payload = iSetup.getData(badModuleToken_);

  // Find the ID's in the OT stack
  std::map<uint32_t, uint32_t> otSiblingOf;
  for (auto const* det : tkGeom.dets()) {
    if (const StackGeomDet* stack = dynamic_cast<const StackGeomDet*>(det)) {
      uint32_t lowerId = stack->lowerDet()->geographicalId().rawId();
      uint32_t upperId = stack->upperDet()->geographicalId().rawId();
      otSiblingOf[lowerId] = upperId;
      otSiblingOf[upperId] = lowerId;
    }
  }

  std::set<uint32_t> allDetIds;
  for (const auto& bc : payload.getBadComponentList()) {
    allDetIds.insert(bc.DetID);
  }

  if (!printdebug_) {
    return;
  }

  for (const auto& bc : payload.getBadComponentList()) {
    uint32_t id = bc.DetID;
    TrackerGeometry::ModuleType type = tkGeom.getDetectorType(DetId(id));
    std::string pairInfo;

    if (type == TrackerGeometry::ModuleType::Ph2PXB3D) {
      uint32_t partner = (id % 2 == 1) ? (id + 1) : (id - 1);
      if (allDetIds.count(partner)) {
        pairInfo = ", paired with " + std::to_string(partner);
      }
    } else {
      auto it = otSiblingOf.find(id);
      if (it != otSiblingOf.end() && allDetIds.count(it->second)) {
        pairInfo = ", paired with " + std::to_string(it->second);
      }
    }

    edm::LogInfo("SiPhase2BadModuleByHandReader")
        << "Dead module DetId " << id << " (type: " << moduleTypeToString(type) << ")" << pairInfo;
  }
}

template <typename RecordT>
void SiPhase2BadModuleByHandReader<RecordT>::fillDescriptions(edm::ConfigurationDescriptions& descriptions) {
  edm::ParameterSetDescription desc;
  desc.addUntracked<bool>("printDebug", true);
  desc.addUntracked<std::string>("label", "");
  descriptions.addWithDefaultLabel(desc);
}

using SiPhase2OTBadModuleReader = SiPhase2BadModuleByHandReader<SiPhase2OuterTrackerBadModuleRcd>;
using SiPhase2ITBadModuleReader = SiPhase2BadModuleByHandReader<SiPhase2InnerTrackerBadModuleRcd>;

#include "FWCore/PluginManager/interface/ModuleDef.h"
#include "FWCore/Framework/interface/MakerMacros.h"

DEFINE_FWK_MODULE(SiPhase2OTBadModuleReader);
DEFINE_FWK_MODULE(SiPhase2ITBadModuleReader);
