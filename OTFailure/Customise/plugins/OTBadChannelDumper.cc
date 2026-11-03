// Dump the dead OT channels of SiPhase2OuterTrackerBadStripRcd: one line per dead channel "rawId type row col".
// PS-p entries use the row/range/flag=column encoding of the patched SiPhase2BadStripConfigurableFakeESSource;
// PS-s / 2S entries use channel = row | col << 10.
#include <fstream>
#include "FWCore/Framework/interface/one/EDAnalyzer.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/Framework/interface/EventSetup.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "CondFormats/SiStripObjects/interface/SiStripBadStrip.h"
#include "CondFormats/DataRecord/interface/SiPhase2OuterTrackerCondDataRecords.h"
#include "Geometry/TrackerGeometryBuilder/interface/TrackerGeometry.h"
#include "Geometry/Records/interface/TrackerDigiGeometryRecord.h"
#include "DataFormats/Phase2TrackerDigi/interface/Phase2TrackerDigi.h"
class OTBadChannelDumper : public edm::one::EDAnalyzer<> {
public:
  explicit OTBadChannelDumper(const edm::ParameterSet& p)
      : out_(p.getParameter<std::string>("output")), badToken_(esConsumes()), geomToken_(esConsumes()) {}
  void analyze(const edm::Event&, const edm::EventSetup& es) override {
    if (done_)
      return;
    const auto& bad = es.getData(badToken_);
    const auto& geom = es.getData(geomToken_);
    std::ofstream f(out_);
    f << "# rawId type row col\n";
    std::vector<uint32_t> ids;
    bad.getDetIds(ids);
    for (auto id : ids) {
      auto t = geom.getDetectorType(DetId(id));
      const bool psp = (t == TrackerGeometry::ModuleType::Ph2PSP);
      const char* ts = psp ? "PSP" : t == TrackerGeometry::ModuleType::Ph2PSS ? "PSS" : "SS";
      auto range = bad.getRange(id);
      for (auto it = range.first; it != range.second; ++it) {
        auto d = bad.decodePhase2(*it);
        for (int i = 0; i < d.range; ++i) {
          if (psp)
            f << id << " " << ts << " " << d.firstStrip + i << " " << (d.flag & 0x3FF) << "\n";
          else {
            auto rc = Phase2TrackerDigi::channelToPixel(d.firstStrip + i);
            f << id << " " << ts << " " << rc.first << " " << rc.second << "\n";
          }
        }
      }
    }
    done_ = true;
  }

private:
  std::string out_;
  bool done_ = false;
  edm::ESGetToken<SiStripBadStrip, SiPhase2OuterTrackerBadStripRcd> badToken_;
  edm::ESGetToken<TrackerGeometry, TrackerDigiGeometryRecord> geomToken_;
};
DEFINE_FWK_MODULE(OTBadChannelDumper);
