// Dumps, for each iteration's pre-selection track collection, the 29 TrackTfClassifier inputs,
// originalAlgo, the current DNN score and the truth label from the by-hits associator, plus hit-level
// features: clusters shared with other tracks of the same iteration, pixel/strip cluster charge and size.
#include <string>
#include <vector>

#include "CommonTools/UtilAlgos/interface/TFileService.h"
#include "DataFormats/BeamSpot/interface/BeamSpot.h"
#include "DataFormats/TrackReco/interface/Track.h"
#include "DataFormats/TrackerRecHit2D/interface/BaseTrackerRecHit.h"
#include "DataFormats/TrackerRecHit2D/interface/SiStripMatchedRecHit2D.h"
#include "DataFormats/TrackerRecHit2D/interface/trackerHitRTTI.h"
#include <algorithm>
#include <unordered_map>
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/Framework/interface/one/EDAnalyzer.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/ServiceRegistry/interface/Service.h"
#include "RecoTracker/FinalTrackSelectors/interface/getBestVertex.h"
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
  float x_[29];
  static constexpr int kNH = 10;
  float h_[kNH];
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
  for (size_t i = 0; i < tracks.size(); ++i)
    iters_.push_back({int(i),
                      consumes<edm::View<reco::Track>>(edm::InputTag(tracks[i])),
                      consumes<std::vector<float>>(edm::InputTag(classifiers[i], "MVAValues"))});

  edm::Service<TFileService> fs;
  tree_ = fs->make<TTree>("tracks", "pre-selection tracks with DNN inputs");
  tree_->Branch("x", x_, "x[29]/F");
  tree_->Branch("h", h_, "h[10]/F");
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

namespace {
  void clusterRefs(const TrackingRecHit& h, std::vector<OmniClusterRef>& out) {
    if (!h.isValid() || !trackerHitRTTI::isFromDet(h))
      return;
    if (trackerHitRTTI::isMatched(h)) {
      const auto& m = static_cast<const SiStripMatchedRecHit2D&>(h);
      out.push_back(m.monoClusterRef());
      out.push_back(m.stereoClusterRef());
    } else {
      out.push_back(static_cast<const BaseTrackerRecHit&>(h).firstClusterRef());
    }
  }
}  // namespace

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
    iter_ = it.index;
    // clusters of every track of this iteration, and cluster -> tracks
    std::vector<std::vector<OmniClusterRef>> trkClus(tracks->size());
    std::unordered_map<unsigned int, std::vector<unsigned int>> clus2trk;
    for (size_t i = 0; i < tracks->size(); ++i) {
      for (const auto* hit : (*tracks)[i].recHits())
        clusterRefs(*hit, trkClus[i]);
      for (const auto& c : trkClus[i])
        clus2trk[c.rawIndex()].push_back(i);
    }
    for (size_t i = 0; i < tracks->size(); ++i) {
      const auto& trk = (*tracks)[i];
      {
        // h: 0 pixel clusters shared, 1 strip clusters shared, 2 max clusters shared with a single other track,
        // 3 mean / 4 max pixel charge (ke), 5 mean pixel sizeX, 6 mean / 7 max pixel sizeY,
        // 8 mean strip charge (ADC sum), 9 mean strip width
        std::fill(h_, h_ + kNH, 0.f);
        std::unordered_map<unsigned int, int> shareWith;
        int nPix = 0, nStr = 0;
        for (const auto& c : trkClus[i]) {
          const auto& owners = clus2trk[c.rawIndex()];
          const bool shared = owners.size() > 1;
          for (auto o : owners)
            if (o != i)
              shareWith[o]++;
          if (c.isPixel()) {
            const auto& pc = *c.cluster_pixel();
            ++nPix;
            h_[0] += shared;
            h_[3] += pc.charge() / 1000.f;
            h_[4] = std::max(h_[4], pc.charge() / 1000.f);
            h_[5] += pc.sizeX();
            h_[6] += pc.sizeY();
            h_[7] = std::max(h_[7], float(pc.sizeY()));
          } else if (c.isStrip()) {
            const auto& sc = *c.cluster_strip();
            ++nStr;
            h_[1] += shared;
            h_[8] += sc.charge();
            h_[9] += sc.size();
          }
        }
        for (const auto& [o, n] : shareWith)
          h_[2] = std::max(h_[2], float(n));
        if (nPix) {
          h_[3] /= nPix;
          h_[5] /= nPix;
          h_[6] /= nPix;
        }
        if (nStr) {
          h_[8] /= nStr;
          h_[9] /= nStr;
        }
      }
      const auto& bestVertex = getBestVertex(trk, vertices);
      x_[0] = trk.pt();
      x_[1] = trk.innerMomentum().x();
      x_[2] = trk.innerMomentum().y();
      x_[3] = trk.innerMomentum().z();
      x_[4] = trk.innerMomentum().rho();
      x_[5] = trk.outerMomentum().x();
      x_[6] = trk.outerMomentum().y();
      x_[7] = trk.outerMomentum().z();
      x_[8] = trk.outerMomentum().rho();
      x_[9] = trk.ptError();
      x_[10] = trk.dxy(bestVertex);
      x_[11] = trk.dz(bestVertex);
      x_[12] = trk.dxy(beamSpot.position());
      x_[13] = trk.dz(beamSpot.position());
      x_[14] = trk.dxyError();
      x_[15] = trk.dzError();
      x_[16] = trk.normalizedChi2();
      x_[17] = trk.eta();
      x_[18] = trk.phi();
      x_[19] = trk.etaError();
      x_[20] = trk.phiError();
      x_[21] = trk.hitPattern().numberOfValidPixelHits();
      x_[22] = trk.hitPattern().numberOfValidStripHits();
      x_[23] = trk.ndof();
      x_[24] = trk.hitPattern().numberOfLostTrackerHits(reco::HitPattern::MISSING_INNER_HITS);
      x_[25] = trk.hitPattern().numberOfLostTrackerHits(reco::HitPattern::MISSING_OUTER_HITS);
      x_[26] = trk.hitPattern().trackerLayersTotallyOffOrBad(reco::HitPattern::MISSING_INNER_HITS);
      x_[27] = trk.hitPattern().trackerLayersTotallyOffOrBad(reco::HitPattern::MISSING_OUTER_HITS);
      x_[28] = trk.hitPattern().trackerLayersWithoutMeasurement(reco::HitPattern::TRACK_HITS);
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
