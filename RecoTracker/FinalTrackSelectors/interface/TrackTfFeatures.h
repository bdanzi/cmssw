#ifndef RecoTracker_FinalTrackSelectors_TrackTfFeatures_h
#define RecoTracker_FinalTrackSelectors_TrackTfFeatures_h

// Inputs of the TrackTfClassifier DNNs, shared by the classifier and by the dumper of the training inputs
// (RecoTracker/FinalTrackSelectors/test/HitFeatDumper.cc)

#include <array>
#include <vector>

#include "DataFormats/BeamSpot/interface/BeamSpot.h"
#include "DataFormats/TrackReco/interface/Track.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"

namespace trackTfFeatures {
  constexpr int kTrackFeatures = 29;
  constexpr int kClusterFeatures = 10;
  using ClusterFeatures = std::array<float, kClusterFeatures>;

  // the kTrackFeatures track-level inputs, written to features[0 .. kTrackFeatures - 1]
  void fillTrackFeatures(reco::Track const& track,
                         reco::BeamSpot const& beamSpot,
                         reco::VertexCollection const& vertices,
                         float* features);

  // cluster-level inputs (useClusterFeatures) of each track of a collection,
  // from the clusters of its valid hits (mono and stereo clusters for a matched strip hit):
  // 0, 1: pixel / strip clusters shared with another track of the collection
  // 2: maximum number of clusters shared with a single other track
  // 3, 4: mean / maximum pixel cluster charge (ke); 5, 6, 7: mean pixel sizeX, mean / maximum pixel sizeY
  // 8, 9: mean strip cluster charge (ADC), mean strip cluster width
  std::vector<ClusterFeatures> computeClusterFeatures(std::vector<reco::Track const*> const& tracks);

  // same, for any container of reco::Track (reco::TrackCollection, edm::View<reco::Track>)
  template <typename Tracks>
  std::vector<ClusterFeatures> computeClusterFeatures(Tracks const& tracks) {
    std::vector<reco::Track const*> pointers;
    pointers.reserve(tracks.size());
    for (auto const& track : tracks)
      pointers.push_back(&track);
    return computeClusterFeatures(pointers);
  }
}  // namespace trackTfFeatures

#endif
