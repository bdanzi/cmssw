#include "DataFormats/BeamSpot/interface/BeamSpotPOD.h"
#include "DataFormats/BeamSpot/interface/alpaka/BeamSpotDeviceProduct.h"
#include "DataFormats/SiPixelClusterSoA/interface/SiPixelClustersDevice.h"
#include "DataFormats/SiPixelClusterSoA/interface/alpaka/SiPixelClustersCollection.h"
#include "DataFormats/SiPixelDigiSoA/interface/SiPixelDigisDevice.h"
#include "DataFormats/SiPixelDigiSoA/interface/alpaka/SiPixelDigisCollection.h"
#include "DataFormats/TrackingRecHitSoA/interface/TrackingRecHitSoADevice.h"
#include "DataFormats/TrackingRecHitSoA/interface/alpaka/TrackingRecHitSoACollection.h"
#include "FWCore/ParameterSet/interface/ConfigurationDescriptions.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/ParameterSet/interface/ParameterSetDescription.h"
#include "FWCore/Utilities/interface/InputTag.h"
#include "Geometry/CommonTopologies/interface/SimplePixelTopology.h"
#include "Geometry/Records/interface/TrackerDigiGeometryRecord.h"
#include "Geometry/TrackerGeometryBuilder/interface/TrackerGeometry.h"
#include "HeterogeneousCore/AlpakaCore/interface/alpaka/Event.h"
#include "HeterogeneousCore/AlpakaCore/interface/alpaka/EventSetup.h"
#include "HeterogeneousCore/AlpakaCore/interface/alpaka/global/EDProducer.h"
#include "HeterogeneousCore/AlpakaInterface/interface/config.h"
#include "HeterogeneousCore/AlpakaInterface/interface/memory.h"

#include "FWCore/ParameterSet/interface/ConfigurationDescriptions.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/ParameterSet/interface/ParameterSetDescription.h"
#include "FWCore/Utilities/interface/InputTag.h"
#include "Geometry/Records/interface/TrackerDigiGeometryRecord.h"
#include "Geometry/TrackerGeometryBuilder/interface/TrackerGeometry.h"
#include "RecoLocalTracker/Records/interface/PixelCPEFastParamsRecord.h"

#include "RecoLocalTracker/SiPixelRecHits/interface/PixelCPEBase.h"
#include "RecoLocalTracker/SiPixelRecHits/interface/pixelCPEforDevice.h"
#include "RecoLocalTracker/SiPixelRecHits/interface/alpaka/PixelCPEFastParamsCollection.h"

#include "PixelRecHitGPUKernel.h"

namespace ALPAKA_ACCELERATOR_NAMESPACE {
  template <typename TrackerTraits>
  class SiPixelRecHitAlpaka : public global::EDProducer<> {
  public:
    explicit SiPixelRecHitAlpaka(const edm::ParameterSet& iConfig);
    ~SiPixelRecHitAlpaka() override = default;

    static void fillDescriptions(edm::ConfigurationDescriptions& descriptions);

    using ParamsOnGPU = pixelCPEforDevice::ParamsOnDeviceT<TrackerTraits>;

  private:
    void produce(edm::StreamID streamID, device::Event& iEvent, const device::EventSetup& iSetup) const override;

    const device::ESGetToken<PixelCPEFastParams<TrackerTraits>, PixelCPEFastParamsRecord> cpeToken_;
    const device::EDGetToken<BeamSpotDeviceProduct> tBeamSpot;
    const device::EDGetToken<SiPixelClustersCollection> tokenClusters_;
    const device::EDGetToken<SiPixelDigisCollection> tokenDigi_;
    const device::EDPutToken<TrackingRecHitAlpakaCollection<TrackerTraits>> tokenHit_;

    const pixelgpudetails::PixelRecHitGPUKernel<TrackerTraits> gpuAlgo_;
  };

  template <typename TrackerTraits>
  SiPixelRecHitAlpaka<TrackerTraits>::SiPixelRecHitAlpaka(const edm::ParameterSet& iConfig)
      : cpeToken_(esConsumes(edm::ESInputTag("", iConfig.getParameter<std::string>("CPE")))),
        tBeamSpot(consumes(iConfig.getParameter<edm::InputTag>("beamSpot"))),
        tokenClusters_(consumes(iConfig.getParameter<edm::InputTag>("src"))),
        tokenDigi_(consumes(iConfig.getParameter<edm::InputTag>("src"))),
        tokenHit_(produces()) {}

  template <typename TrackerTraits>
  void SiPixelRecHitAlpaka<TrackerTraits>::fillDescriptions(edm::ConfigurationDescriptions& descriptions) {
    edm::ParameterSetDescription desc;

    desc.add<edm::InputTag>("beamSpot", edm::InputTag("offlineBeamSpotDevice"));
    desc.add<edm::InputTag>("src", edm::InputTag("siPixelClustersPreSplittingAlpaka"));

    std::string cpe = "PixelCPEFastParams";
    cpe += TrackerTraits::nameModifier;
    desc.add<std::string>("CPE", cpe);

    descriptions.addWithDefaultLabel(desc);
  }

  template <typename TrackerTraits>
  void SiPixelRecHitAlpaka<TrackerTraits>::produce(edm::StreamID streamID,
                                                   device::Event& iEvent,
                                                   const device::EventSetup& es) const {
    auto& fcpe = es.getData(cpeToken_);

    auto const& clusters = iEvent.get(tokenClusters_);

    auto const& digis = iEvent.get(tokenDigi_);

    auto const& bs = iEvent.get(tBeamSpot);

    iEvent.emplace(tokenHit_,
                   gpuAlgo_.makeHitsAsync(digis, clusters, bs.data(), fcpe.const_buffer().data(), iEvent.queue()));
  }
  using SiPixelRecHitAlpakaPhase1 = SiPixelRecHitAlpaka<pixelTopology::Phase1>;
  using SiPixelRecHitAlpakaPhase2 = SiPixelRecHitAlpaka<pixelTopology::Phase2>;
  using SiPixelRecHitAlpakaHIonPhase1 = SiPixelRecHitAlpaka<pixelTopology::HIonPhase1>;
}  // namespace ALPAKA_ACCELERATOR_NAMESPACE

#include "HeterogeneousCore/AlpakaCore/interface/alpaka/MakerMacros.h"
DEFINE_FWK_ALPAKA_MODULE(SiPixelRecHitAlpakaPhase1);
DEFINE_FWK_ALPAKA_MODULE(SiPixelRecHitAlpakaPhase2);
DEFINE_FWK_ALPAKA_MODULE(SiPixelRecHitAlpakaHIonPhase1);
