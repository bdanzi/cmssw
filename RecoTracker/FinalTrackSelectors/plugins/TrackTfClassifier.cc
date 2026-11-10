#include "RecoTracker/FinalTrackSelectors/interface/TrackMVAClassifier.h"

#include "FWCore/Framework/interface/EventSetup.h"
#include "FWCore/Framework/interface/global/EDProducer.h"
#include "DataFormats/TrackReco/interface/Track.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "FWCore/Framework/interface/ConsumesCollector.h"
#include "RecoTracker/FinalTrackSelectors/interface/TrackTfFeatures.h"

#include "PhysicsTools/TensorFlow/interface/TfGraphRecord.h"
#include "PhysicsTools/TensorFlow/interface/TensorFlow.h"
#include "PhysicsTools/TensorFlow/interface/TfGraphDefWrapper.h"

#include <algorithm>

namespace {
  class TfDnn {
  public:
    TfDnn(const edm::ParameterSet& cfg, edm::ConsumesCollector iC)
        : tfDnnLabel_(cfg.getParameter<std::string>("tfDnnLabel")),
          tfDnnToken_(iC.esConsumes(edm::ESInputTag("", tfDnnLabel_))),
          session_(nullptr),
          bsize_(cfg.getParameter<int>("batchSize")),
          useClusterFeatures_(cfg.getParameter<bool>("useClusterFeatures"))

    {}

    static const char* name() { return "trackTfClassifierDefault"; }

    static void fillDescriptions(edm::ParameterSetDescription& desc) {
      desc.add<std::string>("tfDnnLabel", "trackSelectionTf");
      desc.add<int>("batchSize", 16);
      desc.add<bool>("useClusterFeatures", false)
          ->setComment("graph with the track inputs followed by the cluster-level inputs of TrackTfFeatures.h");
    }
    void beginStream() {}

    void initEvent(const edm::EventSetup& es) {
      if (session_ == nullptr) {
        session_ = es.getData(tfDnnToken_).getSession();
      }
    }

    std::vector<float> operator()(reco::TrackCollection const& tracks,
                                  reco::BeamSpot const& beamSpot,
                                  reco::VertexCollection const& vertices) const {
      int size_in = (int)tracks.size();
      int nbatches = size_in / bsize_;

      std::vector<float> output;
      output.resize(size_in);

      std::vector<trackTfFeatures::ClusterFeatures> clusterFeatures;
      if (useClusterFeatures_)
        clusterFeatures = trackTfFeatures::computeClusterFeatures(tracks);
      const int nInputs =
          trackTfFeatures::kTrackFeatures + (useClusterFeatures_ ? trackTfFeatures::kClusterFeatures : 0);

      tensorflow::Tensor input1(tensorflow::DT_FLOAT, {bsize_, nInputs});
      tensorflow::Tensor input2(tensorflow::DT_FLOAT, {bsize_, 1});

      for (auto nb = 0; nb < nbatches + 1; nb++) {
        for (auto nt = 0; nt < bsize_; nt++) {
          int itrack = nt + bsize_ * nb;
          if (itrack >= size_in)
            continue;
          const auto& trk = tracks[itrack];

          float* features = &input1.matrix<float>()(nt, 0);
          trackTfFeatures::fillTrackFeatures(trk, beamSpot, vertices, features);
          if (useClusterFeatures_)
            std::copy(clusterFeatures[itrack].begin(),
                      clusterFeatures[itrack].end(),
                      features + trackTfFeatures::kTrackFeatures);

          //Original algo as its own input, it will enter the graph so that it gets one-hot encoded, as is the preferred
          //format for categorical inputs, where the labels do not have any metric amongst them
          input2.matrix<float>()(nt, 0) = trk.originalAlgo();
        }

        //The names for the input tensors get locked when freezing the trained tensorflow model. The NamedTensors must
        //match those names
        tensorflow::NamedTensorList inputs;
        inputs.resize(2);
        inputs[0] = tensorflow::NamedTensor("x", input1);
        inputs[1] = tensorflow::NamedTensor("y", input2);
        std::vector<tensorflow::Tensor> outputs;

        //evaluate the input
        tensorflow::run(session_, inputs, {"Identity"}, &outputs);

        for (auto nt = 0; nt < bsize_; nt++) {
          int itrack = nt + bsize_ * nb;
          if (itrack >= size_in)
            continue;
          float out0 = 2.0 * outputs[0].matrix<float>()(nt, 0) - 1.0;
          output[itrack] = out0;
        }
      }
      return output;
    }

    const std::string tfDnnLabel_;
    const edm::ESGetToken<TfGraphDefWrapper, TfGraphRecord> tfDnnToken_;
    const tensorflow::Session* session_;
    const int bsize_;
    const bool useClusterFeatures_;
  };
}  // namespace

template <>
void trackMVAClassifierImpl::ComputeMVA<void>::operator()(::TfDnn const& mva,
                                                          reco::TrackCollection const& tracks,
                                                          reco::BeamSpot const& beamSpot,
                                                          reco::VertexCollection const& vertices,
                                                          TrackMVAClassifierBase::MVAPairCollection& mvas) {
  const auto& scores = mva(tracks, beamSpot, vertices);
  size_t current = 0;

  for (auto score : scores) {
    std::pair<float, bool> output(score, true);
    mvas[current++] = output;
  }
}

namespace {
  using TrackTfClassifier = TrackMVAClassifier<TfDnn>;
}  // namespace

#include "FWCore/PluginManager/interface/ModuleDef.h"
#include "FWCore/Framework/interface/MakerMacros.h"

DEFINE_FWK_MODULE(TrackTfClassifier);
