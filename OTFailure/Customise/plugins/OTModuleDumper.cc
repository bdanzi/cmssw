// Dump all Phase-2 Outer Tracker sensors (DetUnits): rawId type subdet layer side stackId r phi z
#include <fstream>
#include "FWCore/Framework/interface/one/EDAnalyzer.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/Framework/interface/EventSetup.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "Geometry/TrackerGeometryBuilder/interface/TrackerGeometry.h"
#include "Geometry/Records/interface/TrackerDigiGeometryRecord.h"
#include "Geometry/Records/interface/TrackerTopologyRcd.h"
#include "DataFormats/TrackerCommon/interface/TrackerTopology.h"
#include "DataFormats/SiStripDetId/interface/StripSubdetector.h"

class OTModuleDumper : public edm::one::EDAnalyzer<> {
public:
  explicit OTModuleDumper(const edm::ParameterSet& p)
      : out_(p.getParameter<std::string>("output")),
        dumpIT_(p.getUntrackedParameter<bool>("dumpIT", false)),
        geomToken_(esConsumes()),
        topoToken_(esConsumes()) {}
  void analyze(const edm::Event&, const edm::EventSetup& es) override {
    if (done_)
      return;
    const auto& geom = es.getData(geomToken_);
    const auto& topo = es.getData(topoToken_);
    std::ofstream f(out_);
    f << "# rawId type subdet layer side stackId r phi z\n";
    for (auto const* du : geom.detUnits()) {
      DetId id = du->geographicalId();
      int sub = id.subdetId();
      const bool isIT = (sub == 1 || sub == 2);  // PixelBarrel, PixelEndcap
      if (dumpIT_ != isIT)
        continue;
      if (!isIT && sub != StripSubdetector::TOB && sub != StripSubdetector::TID)
        continue;
      auto t = geom.getDetectorType(id);
      const char* ts = t == TrackerGeometry::ModuleType::Ph2PSP     ? "PSP"
                       : t == TrackerGeometry::ModuleType::Ph2PSS   ? "PSS"
                       : t == TrackerGeometry::ModuleType::Ph2SS    ? "SS"
                       : t == TrackerGeometry::ModuleType::Ph2PXB   ? "PXB"
                       : t == TrackerGeometry::ModuleType::Ph2PXF   ? "PXF"
                       : t == TrackerGeometry::ModuleType::Ph2PXB3D ? "PXB3D"
                       : t == TrackerGeometry::ModuleType::Ph2PXF3D ? "PXF3D"
                                                                    : "OTHER";
      auto pos = du->surface().position();
      f << id.rawId() << " " << ts << " "
        << (sub == 1                       ? "PXB"
            : sub == 2                     ? "PXF"
            : sub == StripSubdetector::TOB ? "TOB"
                                           : "TID")
        << " " << topo.layer(id) << " " << topo.side(id) << " " << (isIT ? id.rawId() : topo.stack(id)) << " "
        << pos.perp() << " " << pos.phi() << " " << pos.z() << "\n";
    }
    done_ = true;
  }

private:
  std::string out_;
  bool dumpIT_;
  bool done_ = false;
  edm::ESGetToken<TrackerGeometry, TrackerDigiGeometryRecord> geomToken_;
  edm::ESGetToken<TrackerTopology, TrackerTopologyRcd> topoToken_;
};
DEFINE_FWK_MODULE(OTModuleDumper);
