#include "FWCore/Framework/interface/ModuleFactory.h"
#include "FWCore/Framework/interface/ESProducer.h"

#include "RecoTracker/Record/interface/TrackerRecoGeometryRecord.h"

#include "RecoTracker/MkFit/interface/MkFitGeometry.h"

// mkFit includes
#include "RecoTracker/MkFitCore/interface/IterationConfig.h"

class MkFitIterationConfigESProducer : public edm::ESProducer {
public:
  MkFitIterationConfigESProducer(const edm::ParameterSet &iConfig);

  static void fillDescriptions(edm::ConfigurationDescriptions &descriptions);

  std::unique_ptr<mkfit::IterationConfig> produce(const TrackerRecoGeometryRecord &iRecord);

private:
  const edm::ESGetToken<MkFitGeometry, TrackerRecoGeometryRecord> geomToken_;
  const std::string configFile_;
  const float minPtCut_;
  const unsigned int maxClusterSize_;
  const float dc_fracSharedHits_central_;
  const float dc_fracSharedHits_obarrel_;
  const float dc_fracSharedHits_forward_;
  const float dc_drth_central_;
  const float dc_drth_obarrel_;
  const float dc_drth_forward_;
};

MkFitIterationConfigESProducer::MkFitIterationConfigESProducer(const edm::ParameterSet &iConfig)
    : geomToken_{setWhatProduced(this, iConfig.getParameter<std::string>("ComponentName")).consumes()},
      configFile_{iConfig.getParameter<edm::FileInPath>("config").fullPath()},
      minPtCut_{(float)iConfig.getParameter<double>("minPt")},
      maxClusterSize_{iConfig.getParameter<unsigned int>("maxClusterSize")},
      dc_fracSharedHits_central_{(float)iConfig.getParameter<double>("dc_fracSharedHits_central")},
      dc_fracSharedHits_obarrel_{(float)iConfig.getParameter<double>("dc_fracSharedHits_obarrel")},
      dc_fracSharedHits_forward_{(float)iConfig.getParameter<double>("dc_fracSharedHits_forward")},
      dc_drth_central_{(float)iConfig.getParameter<double>("dc_drth_central")},
      dc_drth_obarrel_{(float)iConfig.getParameter<double>("dc_drth_obarrel")},
      dc_drth_forward_{(float)iConfig.getParameter<double>("dc_drth_forward")} {}

void MkFitIterationConfigESProducer::fillDescriptions(edm::ConfigurationDescriptions &descriptions) {
  edm::ParameterSetDescription desc;
  desc.add<std::string>("ComponentName", "")->setComment("Product label");
  desc.add<edm::FileInPath>("config", edm::FileInPath())
      ->setComment("Path to the JSON file for the mkFit configuration parameters");
  desc.add<double>("minPt", 0.0)->setComment("min pT cut applied during track building");
  desc.add<unsigned int>("maxClusterSize", 8)->setComment("Max cluster size of SiStrip hits");
  desc.add<double>("dc_fracSharedHits_central",0.24)->setComment("Duplicate cleaner fraction of shared Hits");
  desc.add<double>("dc_fracSharedHits_obarrel",0.24)->setComment("Duplicate cleaner fraction of shared Hits");
  desc.add<double>("dc_fracSharedHits_forward",0.24)->setComment("Duplicate cleaner fraction of shared Hits");
  desc.add<double>("dc_drth_central",0.002)->setComment("dR cut used to identify duplicate candidates if std::abs(cotan(theta))<1.99 (abs(eta)<1.44)");
  desc.add<double>("dc_drth_obarrel",0.002)->setComment("dR cut used to identify duplicate candidates if 1.99<std::abs(cotan(theta))<6.05 (1.44<abs(eta)<2.5)");
  desc.add<double>("dc_drth_forward",0.002)->setComment("dR cut used to identify duplicate candidates if std::abs(cotan(theta))>6.05 (abs(eta)>2.5)");
  descriptions.addWithDefaultLabel(desc);
}

std::unique_ptr<mkfit::IterationConfig> MkFitIterationConfigESProducer::produce(
    const TrackerRecoGeometryRecord &iRecord) {
  mkfit::ConfigJson cj;
  auto it_conf = cj.load_File(configFile_);
  it_conf->m_params.minPtCut = minPtCut_;
  it_conf->m_backward_params.minPtCut = minPtCut_;
  it_conf->m_params.maxClusterSize = maxClusterSize_;
  it_conf->m_backward_params.maxClusterSize = maxClusterSize_;
  it_conf->dc_fracSharedHits_central = dc_fracSharedHits_central_;
  it_conf->dc_fracSharedHits_obarrel = dc_fracSharedHits_obarrel_;
  it_conf->dc_fracSharedHits_forward = dc_fracSharedHits_forward_;
  it_conf->dc_drth_central = dc_drth_central_;
  it_conf->dc_drth_obarrel = dc_drth_obarrel_;
  it_conf->dc_drth_forward = dc_drth_forward_;
  it_conf->setupStandardFunctionsFromNames();
  return it_conf;
}

DEFINE_FWK_EVENTSETUP_MODULE(MkFitIterationConfigESProducer);
