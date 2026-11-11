// Dumps, for each iteration's pre-selection track collection, the TrackTfClassifier inputs (TrackTfFeatures.h:
// track-level and cluster-level), originalAlgo, the current DNN score and the truth label from the by-hits associator.
#include <string>
#include <vector>

#include "CommonTools/UtilAlgos/interface/TFileService.h"
#include "DataFormats/BeamSpot/interface/BeamSpot.h"
#include "DataFormats/TrackReco/interface/Track.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/Framework/interface/one/EDAnalyzer.h"
#include "FWCore/Utilities/interface/Exception.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/ServiceRegistry/interface/Service.h"
#include "RecoTracker/FinalTrackSelectors/interface/TrackTfFeatures.h"
#include "SimDataFormats/Associations/interface/TrackToTrackingParticleAssociator.h"
#include "SimDataFormats/TrackingAnalysis/interface/TrackingParticle.h"
#include "TTree.h"

class HitFeatDumper : public edm::one::EDAnalyzer<edm::one::SharedResources> {
public:
  explicit HitFeatDumper(const edm::ParameterSet&);
  void analyze(const edm::Event&, const edm::EventSetup&) override;

private:
  struct Iter {
    int index;
    edm::EDGetTokenT<edm::View<reco::Track>> tracks;
    edm::EDGetTokenT<std::vector<float>> mva;
  };
  std::vector<Iter> iters_;
  const edm::EDGetTokenT<reco::BeamSpot> bsToken_;
  const edm::EDGetTokenT<reco::VertexCollection> vtxToken_;
  const edm::EDGetTokenT<TrackingParticleCollection> tpToken_;
  const edm::EDGetTokenT<reco::TrackToTrackingParticleAssociator> assocToken_;

  TTree* tree_;
  float x_[trackTfFeatures::kTrackFeatures];
  trackTfFeatures::ClusterFeatures h_;
  float algo_, mva_, tpPt_, tpEta_, tpDxy_, quality_;
  int label_, iter_, tpSignal_, tpPdg_;
  unsigned long long event_;
};

HitFeatDumper::HitFeatDumper(const edm::ParameterSet& cfg)
    : bsToken_(consumes<reco::BeamSpot>(cfg.getParameter<edm::InputTag>("beamspot"))),
      vtxToken_(consumes<reco::VertexCollection>(cfg.getParameter<edm::InputTag>("vertices"))),
      tpToken_(consumes<TrackingParticleCollection>(cfg.getParameter<edm::InputTag>("trackingParticles"))),
      assocToken_(consumes<reco::TrackToTrackingParticleAssociator>(cfg.getParameter<edm::InputTag>("associator"))) {
  usesResource(TFileService::kSharedResource);
  const auto tracks = cfg.getParameter<std::vector<std::string>>("tracks");
  const auto classifiers = cfg.getParameter<std::vector<std::string>>("classifiers");
  if (classifiers.size() != tracks.size())
    throw cms::Exception("Configuration") << "HitFeatDumper: one classifier per track collection is needed";
  for (size_t i = 0; i < tracks.size(); ++i)
    iters_.push_back({int(i),
                      consumes<edm::View<reco::Track>>(edm::InputTag(tracks[i])),
                      consumes<std::vector<float>>(edm::InputTag(classifiers[i], "MVAValues"))});

  edm::Service<TFileService> fs;
  tree_ = fs->make<TTree>("tracks", "pre-selection tracks with DNN inputs");
  tree_->Branch("x", x_, ("x[" + std::to_string(trackTfFeatures::kTrackFeatures) + "]/F").c_str());
  tree_->Branch("h", h_.data(), ("h[" + std::to_string(trackTfFeatures::kClusterFeatures) + "]/F").c_str());
  tree_->Branch("algo", &algo_);
  tree_->Branch("mva", &mva_);
  tree_->Branch("label", &label_);
  tree_->Branch("iter", &iter_);
  tree_->Branch("quality", &quality_);
  tree_->Branch("tpPt", &tpPt_);
  tree_->Branch("tpEta", &tpEta_);
  tree_->Branch("tpDxy", &tpDxy_);
  tree_->Branch("tpPdg", &tpPdg_);
  tree_->Branch("tpSignal", &tpSignal_);
  tree_->Branch("event", &event_);
}

void HitFeatDumper::analyze(const edm::Event& ev, const edm::EventSetup&) {
  const auto& beamSpot = ev.get(bsToken_);
  const auto& vertices = ev.get(vtxToken_);
  const auto& associator = ev.get(assocToken_);
  edm::Handle<TrackingParticleCollection> tps;
  ev.getByToken(tpToken_, tps);
  event_ = ev.id().event();

  for (const auto& it : iters_) {
    edm::Handle<edm::View<reco::Track>> tracks;
    ev.getByToken(it.tracks, tracks);
    const auto& mvas = ev.get(it.mva);
    const reco::RecoToSimCollection recoToSim = associator.associateRecoToSim(tracks, tps);
    const auto clusterFeatures = trackTfFeatures::computeClusterFeatures(*tracks);
    iter_ = it.index;
    for (size_t i = 0; i < tracks->size(); ++i) {
      const auto& trk = (*tracks)[i];
      trackTfFeatures::fillTrackFeatures(trk, beamSpot, vertices, x_);
      h_ = clusterFeatures[i];
      algo_ = trk.originalAlgo();
      mva_ = i < mvas.size() ? mvas[i] : -99.f;

      label_ = 0;
      quality_ = 0.f;
      tpPt_ = tpEta_ = tpDxy_ = -99.f;
      tpPdg_ = 0;
      tpSignal_ = 0;
      auto found = recoToSim.find(tracks->refAt(i));
      if (found != recoToSim.end() && !found->val.empty()) {
        const auto& best = found->val.front();
        const TrackingParticle& tp = *best.first;
        label_ = 1;
        quality_ = best.second;
        tpPt_ = tp.pt();
        tpEta_ = tp.eta();
        tpDxy_ = (-(tp.vx() - beamSpot.x0()) * tp.py() + (tp.vy() - beamSpot.y0()) * tp.px()) / tp.pt();
        tpPdg_ = tp.pdgId();
        tpSignal_ = (tp.eventId().event() == 0 && tp.eventId().bunchCrossing() == 0) ? 1 : 0;
      }
      tree_->Fill();
    }
  }
}

DEFINE_FWK_MODULE(HitFeatDumper);
