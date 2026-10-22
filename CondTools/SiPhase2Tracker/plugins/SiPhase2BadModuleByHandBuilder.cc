// -*- C++ -*-
//
// Package:    CondTools/SiPhase2BadModuleByHandBuilder
// Class:      SiPhase2BadModuleByHandBuilder
//
/**\class SiPhase2BadModuleByHandBuilder SiPhase2BadModuleByHandBuilder.cc CondTools/SiPhase2Tracker/plugins/SiPhase2BadModuleByHandBuilder.cc

 Description: Translates a hand-specified text list of representative Phase-2 dead-module DetIds into a SiPixelQuality payload and writes it to sqlite under one target record. OT and IT are handled by separate job instances that share the same list.

 Implementation:
     Each DetId is expanded to its full physical module: OT stacks to both sensors via StackGeomDet, IT Ph2PXB3D pairs to the partner DetId by parity. Entries that belong to the other subsystem are skipped based on targetRecord.
*/
//
// Original Author:  Stef Duponcheel
//         Created:  Wed, 30 Sep 2026 12:05:11 GMT
//
//

// system include files
#include <vector>
#include <memory>
#include <map>
#include <set>
#include <fstream>

// user include files
#include "CommonTools/ConditionDBWriter/interface/ConditionDBWriter.h"
#include "CondFormats/SiPixelObjects/interface/SiPixelQuality.h"

#include "DataFormats/DetId/interface/DetId.h"

#include "FWCore/MessageLogger/interface/MessageLogger.h"
#include "FWCore/ParameterSet/interface/ConfigurationDescriptions.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/ParameterSet/interface/ParameterSetDescription.h"
#include "FWCore/ServiceRegistry/interface/Service.h"
#include "FWCore/Utilities/interface/Exception.h"

#include "Geometry/Records/interface/TrackerDigiGeometryRecord.h"
#include "Geometry/TrackerGeometryBuilder/interface/TrackerGeometry.h"
#include "Geometry/CommonTopologies/interface/StackGeomDet.h"

//
// class declaration
//

class SiPhase2BadModuleByHandBuilder : public ConditionDBWriter<SiPixelQuality> {
public:
  explicit SiPhase2BadModuleByHandBuilder(const edm::ParameterSet&);
  ~SiPhase2BadModuleByHandBuilder() override;

  static void fillDescriptions(edm::ConfigurationDescriptions& descriptions);

private:
  std::unique_ptr<SiPixelQuality> getNewObject() override;
  std::vector<uint32_t> expandToFullModule(uint32_t id) const;

  void algoBeginRun(const edm::Run& run, const edm::EventSetup& es) override {
    if (!tkGeom_) {
      tkGeom_ = &es.getData(geomToken_);
      for (auto const* det : tkGeom_->dets()) {
        if (const auto* stack = dynamic_cast<const StackGeomDet*>(det)) {
          sensorToStack_[stack->lowerDet()->geographicalId().rawId()] = stack;
          sensorToStack_[stack->upperDet()->geographicalId().rawId()] = stack;
        }
      }
    }
  };

private:
  const bool printdebug_;
  const TrackerGeometry* tkGeom_;
  edm::ESGetToken<TrackerGeometry, TrackerDigiGeometryRecord> geomToken_;
  const std::string badModuleListFile_;
  const std::string targetRecord_;
  std::map<uint32_t, const StackGeomDet*> sensorToStack_;
};
//
// constructor
//
SiPhase2BadModuleByHandBuilder::SiPhase2BadModuleByHandBuilder(const edm::ParameterSet& iConfig)
    : ConditionDBWriter<SiPixelQuality>(iConfig),
      printdebug_(iConfig.getUntrackedParameter<bool>("printDebug", true)),
      tkGeom_(nullptr),
      geomToken_(esConsumes<edm::Transition::BeginRun>()),
      badModuleListFile_(iConfig.getUntrackedParameter<std::string>("badModuleListFile")),
      targetRecord_(iConfig.getUntrackedParameter<std::string>("targetRecord", "")) {}
//
// member functions
//
SiPhase2BadModuleByHandBuilder::~SiPhase2BadModuleByHandBuilder() = default;

std::vector<uint32_t> SiPhase2BadModuleByHandBuilder::expandToFullModule(uint32_t id) const {
  const GeomDet* det = tkGeom_->idToDet(DetId(id));
  if (!det) {
    throw cms::Exception("SiPhase2BadModuleByHandBuilder") << "DetId " << id << " does not exist in the geometry";
  }
  const StackGeomDet* stack = dynamic_cast<const StackGeomDet*>(det);
  if (!stack) {
    // a sensor of an OT stack: idToDet returns the sensor, not the stack
    if (auto it = sensorToStack_.find(id); it != sensorToStack_.end()) {
      stack = it->second;
    }
  }
  bool isOTModule = stack != nullptr;
  bool isOTRecord = (targetRecord_ == "SiPhase2OuterTrackerBadModuleRcd");
  if (isOTModule != isOTRecord) {
    return {};  // wrong subsystem for this job instance, skip
  }

  if (isOTModule) {
    // OT stack: both sensors make up one physical module
    return {stack->lowerDet()->geographicalId().rawId(), stack->upperDet()->geographicalId().rawId()};
  }

  if (tkGeom_->getDetectorType(DetId(id)) == TrackerGeometry::ModuleType::Ph2PXB3D) {
    // IT 3D sensor pair: partner is id+1 if id is odd, id-1 if even
    uint32_t partnerId = (id % 2 == 1) ? (id + 1) : (id - 1);
    if (!tkGeom_->idToDet(DetId(partnerId))) {
      throw cms::Exception("SiPhase2BadModuleByHandBuilder")
          << "DetId " << id << " claims to be Ph2PXB3D but its expected partner " << partnerId
          << " doesn't exist in the geometry.";
    }
    return {id, partnerId};
  }

  return {id};  // Ph2PXB or Ph2PXF: single-sensor module, nothing to expand
}

std::unique_ptr<SiPixelQuality> SiPhase2BadModuleByHandBuilder::getNewObject() {
  auto obj = std::make_unique<SiPixelQuality>();
  std::set<uint32_t> badDetIds;
  std::ifstream infile(badModuleListFile_);
  if (!infile.is_open()) {
    throw cms::Exception("SiPhase2BadModuleByHandBuilder")
        << "Could not open badModuleListFile: " << badModuleListFile_;
  }
  uint32_t id;
  while (infile >> id) {
    for (uint32_t detId : expandToFullModule(id)) {
      badDetIds.insert(detId);
    }
  }

  for (uint32_t detId : badDetIds) {
    SiPixelQuality::disabledModuleType badModule;
    badModule.DetID = detId;
    badModule.errorType = 0;
    badModule.BadRocs = 65535;
    obj->addDisabledModule(badModule);
    if (printdebug_) {
      edm::LogInfo("SiPhase2BadModuleByHandBuilder") << "Added dead module DetId " << detId;
    }
  }

  edm::Service<cond::service::PoolDBOutputService> mydbservice;
  if (mydbservice.isAvailable()) {
    if (mydbservice->isNewTagRequest(targetRecord_)) {
      mydbservice->createOneIOV<SiPixelQuality>(*obj, mydbservice->beginOfTime(), targetRecord_);
    } else {
      mydbservice->appendOneIOV<SiPixelQuality>(*obj, mydbservice->currentTime(), targetRecord_);
    }
  } else {
    edm::LogError("SiPhase2BadModuleByHandBuilder") << "PoolDBOutputService not available";
  }

  return obj;
}

// ------------ method fills 'descriptions' with the allowed parameters for the module  ------------
void SiPhase2BadModuleByHandBuilder::fillDescriptions(edm::ConfigurationDescriptions& descriptions) {
  edm::ParameterSetDescription desc;
  desc.setComment("Builds a SiPixelQuality payload from a hand-specified list of Phase-2 module DetIds.");
  ConditionDBWriter::fillPSetDescription(desc);
  desc.addUntracked<bool>("printDebug", true);
  desc.addUntracked<std::string>("badModuleListFile")
      ->setComment("Path to a plain text file, one representative bad-module DetId per line");
  desc.addUntracked<std::string>("targetRecord")
      ->setComment(
          "Record to write this payload under, e.g. SiPhase2OuterTrackerBadModuleRcd or "
          "SiPhase2InnerTrackerBadModuleRcd");
  descriptions.addWithDefaultLabel(desc);
}

//define this as a plug-in
#include "FWCore/PluginManager/interface/ModuleDef.h"
#include "FWCore/Framework/interface/MakerMacros.h"
DEFINE_FWK_MODULE(SiPhase2BadModuleByHandBuilder);
