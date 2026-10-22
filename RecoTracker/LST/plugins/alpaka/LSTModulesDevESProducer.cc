// LST includes
#include "RecoTracker/LSTCore/interface/alpaka/LST.h"
#include "RecoTracker/LSTGeometry/interface/Common.h"
#include "RecoTracker/LSTGeometry/interface/Geometry.h"

#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/MessageLogger/interface/MessageLogger.h"
#include <unordered_set>

#include "HeterogeneousCore/AlpakaCore/interface/alpaka/ESProducer.h"
#include "HeterogeneousCore/AlpakaCore/interface/alpaka/ModuleFactory.h"
#include "HeterogeneousCore/AlpakaInterface/interface/config.h"
#include "HeterogeneousCore/AlpakaInterface/interface/memory.h"

#include "RecoTracker/Record/interface/TrackerRecoGeometryRecord.h"

namespace ALPAKA_ACCELERATOR_NAMESPACE {

  class LSTModulesDevESProducer : public ESProducer {
  private:
    double ptCut_;
    // dead OT sensors: connections into a dead module are extended with that module's own connections
    // (layer skipping across up to maxDeadSkips_ consecutive dead modules). Empty = nominal map.
    std::vector<unsigned int> deadModules_;
    unsigned int maxDeadSkips_;
    edm::ESGetToken<lstgeometry::Geometry, TrackerRecoGeometryRecord> lstGeoToken_;

  public:
    LSTModulesDevESProducer(edm::ParameterSet const& iConfig)
        : ESProducer(iConfig),
          ptCut_(iConfig.getParameter<double>("ptCut")),
          deadModules_(iConfig.getParameter<std::vector<unsigned int>>("deadModules")),
          maxDeadSkips_(iConfig.getParameter<unsigned int>("maxDeadSkips")) {
      std::string ptCutStr = lst::floatToStr(ptCut_, 1);

      auto cc = setWhatProduced(this, ptCutStr);
      lstGeoToken_ = cc.consumes<lstgeometry::Geometry>(edm::ESInputTag("", ptCutStr));
    }

    static void fillDescriptions(edm::ConfigurationDescriptions& descriptions) {
      edm::ParameterSetDescription desc;
      desc.add<double>("ptCut", 0.8);
      desc.add<std::vector<unsigned int>>("deadModules", {})
          ->setComment("dead OT sensor detIds: add skip connections across them");
      desc.add<unsigned int>("maxDeadSkips", 2)->setComment("max number of consecutive dead modules to skip");
      descriptions.addWithDefaultLabel(desc);
    }

    std::unique_ptr<lst::LSTESData<DevHost>> produce(TrackerRecoGeometryRecord const& iRecord) {
      const auto& lstg = iRecord.get(lstGeoToken_);
      if (deadModules_.empty())
        return lst::fillESDataHost(lstg);
      // dead-aware module map: keep the nominal connections first, then append skip connections
      lstgeometry::ModuleMap moduleMap = lstg.module_map;
      const std::unordered_set<unsigned int> dead(deadModules_.begin(), deadModules_.end());
      const auto& nominal = lstg.module_map;
      unsigned int nAdded = 0, nModules = 0;
      for (auto& [detId, conns] : moduleMap) {
        if (dead.count(detId))
          continue;
        std::unordered_set<unsigned int> have(conns.begin(), conns.end());
        std::vector<unsigned int> frontier;
        for (auto c : conns)
          if (dead.count(c))
            frontier.push_back(c);
        const unsigned int before = conns.size();
        for (unsigned int depth = 0; depth < maxDeadSkips_ && !frontier.empty(); ++depth) {
          std::vector<unsigned int> next;
          for (auto d : frontier) {
            auto it = nominal.find(d);
            if (it == nominal.end())
              continue;
            for (auto c2 : it->second) {
              if (dead.count(c2))
                next.push_back(c2);
              else if (have.insert(c2).second)
                conns.push_back(c2);
            }
          }
          frontier.swap(next);
        }
        if (conns.size() > before) {
          nAdded += conns.size() - before;
          ++nModules;
        }
      }
      edm::LogPrint("LSTModulesDevESProducer") << "dead-aware LST module map: " << dead.size() << " dead sensors, "
                                               << nAdded << " skip connections added to " << nModules << " modules";
      return lst::fillESDataHost(lstg, &moduleMap);
    }
  };

}  // namespace ALPAKA_ACCELERATOR_NAMESPACE

DEFINE_FWK_EVENTSETUP_ALPAKA_MODULE(LSTModulesDevESProducer);
