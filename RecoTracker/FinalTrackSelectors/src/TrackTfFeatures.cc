#include "RecoTracker/FinalTrackSelectors/interface/TrackTfFeatures.h"

#include <algorithm>
#include <unordered_map>

#include "DataFormats/TrackerRecHit2D/interface/BaseTrackerRecHit.h"
#include "DataFormats/TrackerRecHit2D/interface/SiStripMatchedRecHit2D.h"
#include "DataFormats/TrackerRecHit2D/interface/trackerHitRTTI.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "RecoTracker/FinalTrackSelectors/interface/getBestVertex.h"

namespace {
  void appendClusterRefs(const TrackingRecHit& hit, std::vector<OmniClusterRef>& clusters) {
    if (!hit.isValid() || !trackerHitRTTI::isFromDet(hit))
      return;
    if (trackerHitRTTI::isMatched(hit)) {
      const auto& matched = static_cast<const SiStripMatchedRecHit2D&>(hit);
      clusters.push_back(matched.monoClusterRef());
      clusters.push_back(matched.stereoClusterRef());
    } else {
      clusters.push_back(static_cast<const BaseTrackerRecHit&>(hit).firstClusterRef());
    }
  }
}  // namespace

void trackTfFeatures::fillTrackFeatures(reco::Track const& trk,
                                        reco::BeamSpot const& beamSpot,
                                        reco::VertexCollection const& vertices,
                                        float* features) {
  const auto& bestVertex = getBestVertex(trk, vertices);

  features[0] = trk.pt();
  features[1] = trk.innerMomentum().x();
  features[2] = trk.innerMomentum().y();
  features[3] = trk.innerMomentum().z();
  features[4] = trk.innerMomentum().rho();
  features[5] = trk.outerMomentum().x();
  features[6] = trk.outerMomentum().y();
  features[7] = trk.outerMomentum().z();
  features[8] = trk.outerMomentum().rho();
  features[9] = trk.ptError();
  features[10] = trk.dxy(bestVertex);
  features[11] = trk.dz(bestVertex);
  features[12] = trk.dxy(beamSpot.position());
  features[13] = trk.dz(beamSpot.position());
  features[14] = trk.dxyError();
  features[15] = trk.dzError();
  features[16] = trk.normalizedChi2();
  features[17] = trk.eta();
  features[18] = trk.phi();
  features[19] = trk.etaError();
  features[20] = trk.phiError();
  features[21] = trk.hitPattern().numberOfValidPixelHits();
  features[22] = trk.hitPattern().numberOfValidStripHits();
  features[23] = trk.ndof();
  features[24] = trk.hitPattern().numberOfLostTrackerHits(reco::HitPattern::MISSING_INNER_HITS);
  features[25] = trk.hitPattern().numberOfLostTrackerHits(reco::HitPattern::MISSING_OUTER_HITS);
  features[26] = trk.hitPattern().trackerLayersTotallyOffOrBad(reco::HitPattern::MISSING_INNER_HITS);
  features[27] = trk.hitPattern().trackerLayersTotallyOffOrBad(reco::HitPattern::MISSING_OUTER_HITS);
  features[28] = trk.hitPattern().trackerLayersWithoutMeasurement(reco::HitPattern::TRACK_HITS);
}

std::vector<trackTfFeatures::ClusterFeatures> trackTfFeatures::computeClusterFeatures(
    std::vector<reco::Track const*> const& tracks) {
  const int nTracks = tracks.size();
  std::vector<std::vector<OmniClusterRef>> trackClusters(nTracks);
  std::unordered_map<unsigned int, std::vector<int>> clusterTracks;
  for (int i = 0; i < nTracks; ++i) {
    for (const auto* hit : tracks[i]->recHits())
      appendClusterRefs(*hit, trackClusters[i]);
    for (const auto& cluster : trackClusters[i])
      clusterTracks[cluster.rawIndex()].push_back(i);
  }

  std::vector<ClusterFeatures> features(nTracks);
  for (int i = 0; i < nTracks; ++i) {
    auto& f = features[i];
    f.fill(0.f);
    std::unordered_map<int, int> sharedWith;
    int nPixel = 0, nStrip = 0;
    for (const auto& cluster : trackClusters[i]) {
      const auto& owners = clusterTracks[cluster.rawIndex()];
      const bool shared = owners.size() > 1;
      for (auto owner : owners)
        if (owner != i)
          ++sharedWith[owner];
      if (cluster.isPixel()) {
        const auto& pixel = *cluster.cluster_pixel();
        ++nPixel;
        f[0] += shared;
        f[3] += pixel.charge() / 1000.f;
        f[4] = std::max(f[4], pixel.charge() / 1000.f);
        f[5] += pixel.sizeX();
        f[6] += pixel.sizeY();
        f[7] = std::max(f[7], float(pixel.sizeY()));
      } else if (cluster.isStrip()) {
        const auto& strip = *cluster.cluster_strip();
        ++nStrip;
        f[1] += shared;
        f[8] += strip.charge();
        f[9] += strip.size();
      }
    }
    for (const auto& [owner, n] : sharedWith)
      f[2] = std::max(f[2], float(n));
    if (nPixel) {
      f[3] /= nPixel;
      f[5] /= nPixel;
      f[6] /= nPixel;
    }
    if (nStrip) {
      f[8] /= nStrip;
      f[9] /= nStrip;
    }
  }
  return features;
}
