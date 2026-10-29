// TrackTfClassifier with 10 extra hit-level inputs:
// clusters shared with other tracks of the same collection, pixel/strip cluster charge and size.
// Graph inputs: x[39] (29 production features + 10 hit features), y[1] = originalAlgo; output Identity.
#include <algorithm>
#include <array>
#include <unordered_map>

#include "RecoTracker/FinalTrackSelectors/interface/TrackMVAClassifier.h"

#include "DataFormats/TrackReco/interface/Track.h"
#include "DataFormats/TrackerRecHit2D/interface/BaseTrackerRecHit.h"
#include "DataFormats/TrackerRecHit2D/interface/SiStripMatchedRecHit2D.h"
#include "DataFormats/TrackerRecHit2D/interface/trackerHitRTTI.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "FWCore/Framework/interface/ConsumesCollector.h"
#include "FWCore/Framework/interface/EventSetup.h"
#include "FWCore/Framework/interface/global/EDProducer.h"
#include "RecoTracker/FinalTrackSelectors/interface/getBestVertex.h"

#include "PhysicsTools/TensorFlow/interface/TensorFlow.h"
#include "PhysicsTools/TensorFlow/interface/TfGraphDefWrapper.h"
#include "PhysicsTools/TensorFlow/interface/TfGraphRecord.h"

namespace {
  constexpr int kNX = 29, kNH = 10;

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

  class HitTfDnn {
  public:
    HitTfDnn(const edm::ParameterSet& cfg, edm::ConsumesCollector iC)
        : tfDnnLabel_(cfg.getParameter<std::string>("tfDnnLabel")),
          tfDnnToken_(iC.esConsumes(edm::ESInputTag("", tfDnnLabel_))),
          session_(nullptr),
          bsize_(cfg.getParameter<int>("batchSize")) {}

    static const char* name() { return "trackHitTfClassifierDefault"; }

    static void fillDescriptions(edm::ParameterSetDescription& desc) {
      desc.add<std::string>("tfDnnLabel", "trackSelectionTf");
      desc.add<int>("batchSize", 16);
    }
    void beginStream() {}

    void initEvent(const edm::EventSetup& es) {
      if (session_ == nullptr)
        session_ = es.getData(tfDnnToken_).getSession();
    }

    std::vector<float> operator()(reco::TrackCollection const& tracks,
                                  reco::BeamSpot const& beamSpot,
                                  reco::VertexCollection const& vertices) const {
      const int size_in = tracks.size();
      std::vector<float> output(size_in);

      // hit-level features
      std::vector<std::vector<OmniClusterRef>> trkClus(size_in);
      std::unordered_map<unsigned int, std::vector<int>> clus2trk;
      for (int i = 0; i < size_in; ++i) {
        for (const auto* hit : tracks[i].recHits())
          clusterRefs(*hit, trkClus[i]);
        for (const auto& c : trkClus[i])
          clus2trk[c.rawIndex()].push_back(i);
      }
      std::vector<std::array<float, kNH>> hf(size_in);
      for (int i = 0; i < size_in; ++i) {
        auto& h = hf[i];
        h.fill(0.f);
        std::unordered_map<int, int> shareWith;
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
            h[0] += shared;
            h[3] += pc.charge() / 1000.f;
            h[4] = std::max(h[4], pc.charge() / 1000.f);
            h[5] += pc.sizeX();
            h[6] += pc.sizeY();
            h[7] = std::max(h[7], float(pc.sizeY()));
          } else if (c.isStrip()) {
            const auto& sc = *c.cluster_strip();
            ++nStr;
            h[1] += shared;
            h[8] += sc.charge();
            h[9] += sc.size();
          }
        }
        for (const auto& [o, n] : shareWith)
          h[2] = std::max(h[2], float(n));
        if (nPix) {
          h[3] /= nPix;
          h[5] /= nPix;
          h[6] /= nPix;
        }
        if (nStr) {
          h[8] /= nStr;
          h[9] /= nStr;
        }
      }

      tensorflow::Tensor input1(tensorflow::DT_FLOAT, {bsize_, kNX + kNH});
      tensorflow::Tensor input2(tensorflow::DT_FLOAT, {bsize_, 1});
      const int nbatches = size_in / bsize_;
      for (int nb = 0; nb < nbatches + 1; nb++) {
        for (int nt = 0; nt < bsize_; nt++) {
          const int itrack = nt + bsize_ * nb;
          if (itrack >= size_in)
            continue;
          const auto& trk = tracks[itrack];
          const auto& bestVertex = getBestVertex(trk, vertices);
          auto x = input1.matrix<float>();
          x(nt, 0) = trk.pt();
          x(nt, 1) = trk.innerMomentum().x();
          x(nt, 2) = trk.innerMomentum().y();
          x(nt, 3) = trk.innerMomentum().z();
          x(nt, 4) = trk.innerMomentum().rho();
          x(nt, 5) = trk.outerMomentum().x();
          x(nt, 6) = trk.outerMomentum().y();
          x(nt, 7) = trk.outerMomentum().z();
          x(nt, 8) = trk.outerMomentum().rho();
          x(nt, 9) = trk.ptError();
          x(nt, 10) = trk.dxy(bestVertex);
          x(nt, 11) = trk.dz(bestVertex);
          x(nt, 12) = trk.dxy(beamSpot.position());
          x(nt, 13) = trk.dz(beamSpot.position());
          x(nt, 14) = trk.dxyError();
          x(nt, 15) = trk.dzError();
          x(nt, 16) = trk.normalizedChi2();
          x(nt, 17) = trk.eta();
          x(nt, 18) = trk.phi();
          x(nt, 19) = trk.etaError();
          x(nt, 20) = trk.phiError();
          x(nt, 21) = trk.hitPattern().numberOfValidPixelHits();
          x(nt, 22) = trk.hitPattern().numberOfValidStripHits();
          x(nt, 23) = trk.ndof();
          x(nt, 24) = trk.hitPattern().numberOfLostTrackerHits(reco::HitPattern::MISSING_INNER_HITS);
          x(nt, 25) = trk.hitPattern().numberOfLostTrackerHits(reco::HitPattern::MISSING_OUTER_HITS);
          x(nt, 26) = trk.hitPattern().trackerLayersTotallyOffOrBad(reco::HitPattern::MISSING_INNER_HITS);
          x(nt, 27) = trk.hitPattern().trackerLayersTotallyOffOrBad(reco::HitPattern::MISSING_OUTER_HITS);
          x(nt, 28) = trk.hitPattern().trackerLayersWithoutMeasurement(reco::HitPattern::TRACK_HITS);
          for (int k = 0; k < kNH; ++k)
            x(nt, kNX + k) = hf[itrack][k];
          input2.matrix<float>()(nt, 0) = trk.originalAlgo();
        }
        tensorflow::NamedTensorList inputs{{"x", input1}, {"y", input2}};
        std::vector<tensorflow::Tensor> outputs;
        tensorflow::run(session_, inputs, {"Identity"}, &outputs);
        for (int nt = 0; nt < bsize_; nt++) {
          const int itrack = nt + bsize_ * nb;
          if (itrack < size_in)
            output[itrack] = 2.f * outputs[0].matrix<float>()(nt, 0) - 1.f;
        }
      }
      return output;
    }

    const std::string tfDnnLabel_;
    const edm::ESGetToken<TfGraphDefWrapper, TfGraphRecord> tfDnnToken_;
    const tensorflow::Session* session_;
    const int bsize_;
  };
}  // namespace

template <>
void trackMVAClassifierImpl::ComputeMVA<void>::operator()(::HitTfDnn const& mva,
                                                          reco::TrackCollection const& tracks,
                                                          reco::BeamSpot const& beamSpot,
                                                          reco::VertexCollection const& vertices,
                                                          TrackMVAClassifierBase::MVAPairCollection& mvas) {
  const auto& scores = mva(tracks, beamSpot, vertices);
  for (size_t i = 0; i < scores.size(); ++i)
    mvas[i] = std::pair<float, bool>(scores[i], true);
}

namespace {
  using TrackHitTfClassifier = TrackMVAClassifier<HitTfDnn>;
}  // namespace

#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/PluginManager/interface/ModuleDef.h"

DEFINE_FWK_MODULE(TrackHitTfClassifier);
