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
  const float dc_fracSharedHits_forwbarrel_;
  const float dc_fracSharedHits_forward_;
  const float dc_fracSharedHits_extforward_;
  const float dc_drth_central_;
  const float dc_drth_obarrel_;
  const float dc_drth_forwbarrel_;
  const float dc_drth_forward_;
  const float dc_drth_extforward_;
  const float dc_fracSharedHits_hcentral_;
  const float dc_fracSharedHits_hobarrel_;
  const float dc_fracSharedHits_hforwbarrel_;
  const float dc_fracSharedHits_hforward_;
  const float dc_fracSharedHits_hextforward_;
  const float dc_drth_hcentral_;
  const float dc_drth_hobarrel_;
  const float dc_drth_hforwbarrel_;
  const float dc_drth_hforward_;
  const float dc_drth_hextforward_;
  const float sc_ptthr_hpt_; 
  
  const float sc_dzmax_bh_; 
  const float sc_drmax_bh_; 
  const float sc_dzmax_extbh_; 
  const float sc_drmax_extbh_;
  const float sc_dzmax_fbh_;
  const float sc_drmax_fbh_;
  const float sc_dzmax_eh_; 
  const float sc_drmax_eh_;
  const float sc_dzmax_extfh_;
  const float sc_drmax_extfh_;
  const float sc_dzmax_bl_; 
  const float sc_drmax_bl_; 
  const float sc_dzmax_extbl_; 
  const float sc_drmax_extbl_;
  const float sc_dzmax_fbl_;
  const float sc_drmax_fbl_;
  const float sc_dzmax_el_; 
  const float sc_drmax_el_;
  const float sc_dzmax_extfl_;
  const float sc_drmax_extfl_;
  
};

MkFitIterationConfigESProducer::MkFitIterationConfigESProducer(const edm::ParameterSet &iConfig)
    : geomToken_{setWhatProduced(this, iConfig.getParameter<std::string>("ComponentName")).consumes()},
      configFile_{iConfig.getParameter<edm::FileInPath>("config").fullPath()},
      minPtCut_{(float)iConfig.getParameter<double>("minPt")},
      maxClusterSize_{iConfig.getParameter<unsigned int>("maxClusterSize")},
      dc_fracSharedHits_central_{(float)iConfig.getParameter<double>("dc_fracSharedHits_central")},
      dc_fracSharedHits_obarrel_{(float)iConfig.getParameter<double>("dc_fracSharedHits_obarrel")},
      dc_fracSharedHits_forwbarrel_{(float)iConfig.getParameter<double>("dc_fracSharedHits_forwbarrel")},
      dc_fracSharedHits_forward_{(float)iConfig.getParameter<double>("dc_fracSharedHits_forward")},
      dc_fracSharedHits_extforward_{(float)iConfig.getParameter<double>("dc_fracSharedHits_extforward")},
      dc_drth_central_{(float)iConfig.getParameter<double>("dc_drth_central")},
      dc_drth_obarrel_{(float)iConfig.getParameter<double>("dc_drth_obarrel")},
      dc_drth_forwbarrel_{(float)iConfig.getParameter<double>("dc_drth_forwbarrel")},
      dc_drth_forward_{(float)iConfig.getParameter<double>("dc_drth_forward")},
      dc_drth_extforward_{(float)iConfig.getParameter<double>("dc_drth_extforward")},
      dc_fracSharedHits_hcentral_{(float)iConfig.getParameter<double>("dc_fracSharedHits_hcentral")},
      dc_fracSharedHits_hobarrel_{(float)iConfig.getParameter<double>("dc_fracSharedHits_hobarrel")},
      dc_fracSharedHits_hforwbarrel_{(float)iConfig.getParameter<double>("dc_fracSharedHits_hforwbarrel")},
      dc_fracSharedHits_hforward_{(float)iConfig.getParameter<double>("dc_fracSharedHits_hforward")},
      dc_fracSharedHits_hextforward_{(float)iConfig.getParameter<double>("dc_fracSharedHits_hextforward")},
      dc_drth_hcentral_{(float)iConfig.getParameter<double>("dc_drth_hcentral")},
      dc_drth_hobarrel_{(float)iConfig.getParameter<double>("dc_drth_hobarrel")},
      dc_drth_hforwbarrel_{(float)iConfig.getParameter<double>("dc_drth_hforwbarrel")},
      dc_drth_hforward_{(float)iConfig.getParameter<double>("dc_drth_hforward")},
      dc_drth_hextforward_{(float)iConfig.getParameter<double>("dc_drth_hextforward")},
      sc_ptthr_hpt_{(float)iConfig.getParameter<double>("sc_ptthr_hpt")},
      sc_dzmax_bh_{(float)iConfig.getParameter<double>("sc_dzmax_bh")},
      sc_drmax_bh_{(float)iConfig.getParameter<double>("sc_drmax_bh")},
      sc_dzmax_extbh_{(float)iConfig.getParameter<double>("sc_dzmax_extbh")},
      sc_drmax_extbh_{(float)iConfig.getParameter<double>("sc_drmax_extbh")},
      sc_dzmax_fbh_{(float)iConfig.getParameter<double>("sc_dzmax_fbh")},
      sc_drmax_fbh_{(float)iConfig.getParameter<double>("sc_drmax_fbh")},
      sc_dzmax_eh_{(float)iConfig.getParameter<double>("sc_dzmax_eh")},
      sc_drmax_eh_{(float)iConfig.getParameter<double>("sc_drmax_eh")},
      sc_dzmax_extfh_{(float)iConfig.getParameter<double>("sc_dzmax_extfh")},
      sc_drmax_extfh_{(float)iConfig.getParameter<double>("sc_drmax_extfh")},
      sc_dzmax_bl_{(float)iConfig.getParameter<double>("sc_dzmax_bl")},
      sc_drmax_bl_{(float)iConfig.getParameter<double>("sc_drmax_bl")},
      sc_dzmax_extbl_{(float)iConfig.getParameter<double>("sc_dzmax_extbl")},
      sc_drmax_extbl_{(float)iConfig.getParameter<double>("sc_drmax_extbl")},
      sc_dzmax_fbl_{(float)iConfig.getParameter<double>("sc_dzmax_fbl")},
      sc_drmax_fbl_{(float)iConfig.getParameter<double>("sc_drmax_fbl")},
      sc_dzmax_el_{(float)iConfig.getParameter<double>("sc_dzmax_el")},
      sc_drmax_el_{(float)iConfig.getParameter<double>("sc_drmax_el")},
      sc_dzmax_extfl_{(float)iConfig.getParameter<double>("sc_dzmax_extfl")},
      sc_drmax_extfl_{(float)iConfig.getParameter<double>("sc_drmax_extfl")}{}


void MkFitIterationConfigESProducer::fillDescriptions(edm::ConfigurationDescriptions &descriptions) {
  edm::ParameterSetDescription desc;
  desc.add<std::string>("ComponentName", "")->setComment("Product label");
  desc.add<edm::FileInPath>("config", edm::FileInPath())
      ->setComment("Path to the JSON file for the mkFit configuration parameters");
  desc.add<double>("minPt", 0.0)->setComment("min pT cut applied during track building");
  desc.add<unsigned int>("maxClusterSize", 8)->setComment("Max cluster size of SiStrip hits");
  desc.add<double>("dc_fracSharedHits_central",0.24)->setComment("Duplicate cleaner fraction of shared Hits");
  desc.add<double>("dc_fracSharedHits_obarrel",0.24)->setComment("Duplicate cleaner fraction of shared Hits");
  desc.add<double>("dc_fracSharedHits_forwbarrel",0.24)->setComment("Duplicate cleaner fraction of shared Hits");
  desc.add<double>("dc_fracSharedHits_forward",0.24)->setComment("Duplicate cleaner fraction of shared Hits");
  desc.add<double>("dc_fracSharedHits_extforward",0.24)->setComment("Duplicate cleaner fraction of shared Hits");
  desc.add<double>("dc_drth_central",0.002)->setComment("dR cut used to identify duplicate candidates if std::abs(cotan(theta))<1.99 (abs(eta)<1.44)");
  desc.add<double>("dc_drth_obarrel",0.002)->setComment("dR cut used to identify duplicate candidates if 1.99<std::abs(cotan(theta))<6.05 (1.44<abs(eta)<2.5)");
  desc.add<double>("dc_drth_forwbarrel",0.002)->setComment("dR cut used to identify duplicate candidates if std::abs(cotan(theta))>6.05 (abs(eta)>2.5)");
  desc.add<double>("dc_drth_forward",0.002)->setComment("dR cut used to identify duplicate candidates if std::abs(cotan(theta))>6.05 (abs(eta)>2.5)");
  desc.add<double>("dc_drth_extforward",0.002)->setComment("dR cut used to identify duplicate candidates if std::abs(cotan(theta))>6.05 (abs(eta)>2.5)");
  desc.add<double>("dc_fracSharedHits_hcentral",0.24)->setComment("Duplicate cleaner fraction of shared Hits");
  desc.add<double>("dc_fracSharedHits_hobarrel",0.24)->setComment("Duplicate cleaner fraction of shared Hits");
  desc.add<double>("dc_fracSharedHits_hforwbarrel",0.24)->setComment("Duplicate cleaner fraction of shared Hits");
  desc.add<double>("dc_fracSharedHits_hforward",0.24)->setComment("Duplicate cleaner fraction of shared Hits");
  desc.add<double>("dc_fracSharedHits_hextforward",0.24)->setComment("Duplicate cleaner fraction of shared Hits");
  desc.add<double>("dc_drth_hcentral",0.002)->setComment("dR cut used to identify duplicate candidates if std::abs(cotan(theta))<1.99 (abs(eta)<1.44)");
  desc.add<double>("dc_drth_hobarrel",0.002)->setComment("dR cut used to identify duplicate candidates if 1.99<std::abs(cotan(theta))<6.05 (1.44<abs(eta)<2.5)");
  desc.add<double>("dc_drth_hforwbarrel",0.002)->setComment("dR cut used to identify duplicate candidates if std::abs(cotan(theta))>6.05 (abs(eta)>2.5)");
  desc.add<double>("dc_drth_hforward",0.002)->setComment("dR cut used to identify duplicate candidates if std::abs(cotan(theta))>6.05 (abs(eta)>2.5)");
  desc.add<double>("dc_drth_hextforward",0.002)->setComment("dR cut used to identify duplicate candidates if std::abs(cotan(theta))>6.05 (abs(eta)>2.5)");
  desc.add<double>("sc_ptthr_hpt", 2.0)->setComment("pT threshold applied for high-pT candidates");
  desc.add<double>("sc_drmax_bh", 0.01)->setComment("Maximum dR matching window for barrel high-pT candidates");
  desc.add<double>("sc_dzmax_bh", 0.005)->setComment("Maximum dZ matching window for barrel high-pT candidates");
  desc.add<double>("sc_drmax_extbh", 0.01)->setComment("Maximum dR matching window for outer barrel high-pT candidates");
  desc.add<double>("sc_dzmax_extbh", 0.005)->setComment("Maximum dZ matching window for outer barrel high-pT candidates");
  desc.add<double>("sc_drmax_fbh", 0.01)->setComment("Maximum dR matching window for outer barrel high-pT candidates");
  desc.add<double>("sc_dzmax_fbh", 0.005)->setComment("Maximum dZ matching window for outer barrel high-pT candidates");
  desc.add<double>("sc_drmax_eh", 0.02)->setComment("Maximum dR matching window for endcap high-pT candidates");
  desc.add<double>("sc_dzmax_eh", 0.02)->setComment("Maximum dZ matching window for endcap high-pT candidates");
  desc.add<double>("sc_drmax_extfh", 0.02)->setComment("Maximum dR matching window for endcap high-pT candidates");
  desc.add<double>("sc_dzmax_extfh", 0.02)->setComment("Maximum dZ matching window for endcap high-pT candidates");
  desc.add<double>("sc_drmax_bl", 0.01)->setComment("Maximum dR matching window for barrel low-pT candidates");
  desc.add<double>("sc_dzmax_bl", 0.005)->setComment("Maximum dZ matching window for barrel low-pT candidates");
  desc.add<double>("sc_drmax_fbl", 0.01)->setComment("Maximum dR matching window for outer barrel low-pT candidates");
  desc.add<double>("sc_dzmax_fbl", 0.005)->setComment("Maximum dZ matching window for outer barrel low-pT candidates");
  desc.add<double>("sc_drmax_extbl", 0.01)->setComment("Maximum dR matching window for outer barrel low-pT candidates");
  desc.add<double>("sc_dzmax_extbl", 0.005)->setComment("Maximum dZ matching window for outer barrel low-pT candidates");
  desc.add<double>("sc_drmax_el", 0.03)->setComment("Maximum dR matching window for endcap low-pT candidates");
  desc.add<double>("sc_dzmax_el", 0.03)->setComment("Maximum dZ matching window for endcap low-pT candidates");
  desc.add<double>("sc_drmax_extfl", 0.03)->setComment("Maximum dR matching window for endcap low-pT candidates");
  desc.add<double>("sc_dzmax_extfl", 0.03)->setComment("Maximum dZ matching window for endcap low-pT candidates");


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
  it_conf->dc_fracSharedHits_forwbarrel = dc_fracSharedHits_forwbarrel_;
  it_conf->dc_fracSharedHits_extforward = dc_fracSharedHits_extforward_;
  it_conf->dc_drth_central = dc_drth_central_;
  it_conf->dc_drth_obarrel = dc_drth_obarrel_;
  it_conf->dc_drth_forwbarrel = dc_drth_forwbarrel_;
  it_conf->dc_drth_forward = dc_drth_forward_;
  it_conf->dc_drth_extforward = dc_drth_extforward_;
  it_conf->dc_fracSharedHits_hcentral = dc_fracSharedHits_hcentral_;
  it_conf->dc_fracSharedHits_hobarrel = dc_fracSharedHits_hobarrel_;
  it_conf->dc_fracSharedHits_hforward = dc_fracSharedHits_hforward_;
  it_conf->dc_fracSharedHits_hforwbarrel = dc_fracSharedHits_hforwbarrel_;
  it_conf->dc_fracSharedHits_hextforward = dc_fracSharedHits_hextforward_;
  it_conf->dc_drth_hcentral = dc_drth_hcentral_;
  it_conf->dc_drth_hobarrel = dc_drth_hobarrel_;
  it_conf->dc_drth_hforwbarrel = dc_drth_hforwbarrel_;
  it_conf->dc_drth_hforward = dc_drth_hforward_;
  it_conf->dc_drth_hextforward = dc_drth_hextforward_;
  it_conf->sc_ptthr_hpt = sc_ptthr_hpt_;
  it_conf->sc_dzmax_bh = sc_dzmax_bh_;
  it_conf->sc_drmax_bh =  sc_drmax_bh_;
  it_conf->sc_dzmax_extbh =  sc_dzmax_extbh_;
  it_conf->sc_drmax_extbh =  sc_drmax_extbh_;
  it_conf->sc_dzmax_fbh =  sc_dzmax_fbh_;
  it_conf->sc_drmax_fbh =  sc_drmax_fbh_;
  it_conf->sc_dzmax_eh =  sc_dzmax_eh_;
  it_conf->sc_drmax_eh =  sc_drmax_eh_;
  it_conf->sc_dzmax_extfh =  sc_dzmax_extfh_;
  it_conf->sc_drmax_extfh =  sc_drmax_extfh_;
  it_conf->sc_dzmax_bl =  sc_dzmax_bl_;
  it_conf->sc_drmax_bl =  sc_drmax_bl_;
  it_conf->sc_dzmax_extbl =  sc_dzmax_extbl_;
  it_conf->sc_drmax_extbl = sc_drmax_extbl_;
  it_conf->sc_dzmax_fbl =  sc_dzmax_fbl_;
  it_conf->sc_drmax_fbl = sc_drmax_fbl_;
  it_conf->sc_dzmax_el =  sc_dzmax_el_;
  it_conf->sc_drmax_el =  sc_drmax_el_;
  it_conf->sc_dzmax_extfl =  sc_dzmax_extfl_;
  it_conf->sc_drmax_extfl =  sc_drmax_extfl_;

  it_conf->setupStandardFunctionsFromNames();
  return it_conf;
}

DEFINE_FWK_EVENTSETUP_MODULE(MkFitIterationConfigESProducer);
