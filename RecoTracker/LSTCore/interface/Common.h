#ifndef RecoTracker_LSTCore_interface_Common_h
#define RecoTracker_LSTCore_interface_Common_h

#include "DataFormats/Common/interface/StdArray.h"
#include "HeterogeneousCore/AlpakaInterface/interface/config.h"

#include "RecoTracker/LSTGeometry/interface/Common.h"

#if defined(FP16_Base)
#if defined ALPAKA_ACC_GPU_CUDA_ENABLED
#include <cuda_fp16.h>
#elif defined ALPAKA_ACC_GPU_HIP_ENABLED
#include <hip/hip_fp16.h>
#endif
#endif

namespace lst {

  // Named constants for pixelTypes
  enum PixelType : int8_t { kInvalid = -1, kHighPt = 0, kLowPtPosCurv = 1, kLowPtNegCurv = 2 };

  // Named types for LST objects
  enum LSTObjType : int8_t { T5 = 4, pT3 = 5, pT5 = 7, pLS = 8, T4 = 9 };

  // Packed per-triplet flags, non-overlapping bits.
  enum T3Flag : uint8_t { kT3LoosePointing = 0b0001 };

  enum class HitType : int { Pixel = 0, Invalid = 3, Phase2OT = 4 };  // as in TrackingNtuple.cc

  constexpr unsigned int kPixelModuleId = 1;

  constexpr unsigned int kMaxPLSHitsInHitsSoA = 4;
  constexpr unsigned int kMaxPLSHitBitsInHitsSoA = 8;

  constexpr unsigned int max_blocks = 80;
  constexpr unsigned int max_connected_modules = 40;

  constexpr unsigned int n_max_pixel_segments_per_module = 500000;

  constexpr unsigned int n_max_pixel_md_per_modules = 2 * n_max_pixel_segments_per_module;

  constexpr unsigned int n_max_pixel_triplets = 5000;
  constexpr unsigned int n_max_pixel_quintuplets = 15000;

  constexpr unsigned int n_max_pixel_track_candidates = 300000;
  constexpr unsigned int n_max_nonpixel_track_candidates = 10000;

  constexpr unsigned int size_superbins = 45000;

  constexpr uint16_t kTCEmptyLowerModule = 0xFFFF;     // Sentinel for empty lowerModule index
  constexpr unsigned int kTCEmptyHitIdx = 0xFFFFFFFF;  // Sentinel for empty hit slots
  constexpr unsigned int kInvalidU32Idx = 0xFFFFFFFF;  // Sentinel for invalid uint32 idx

  // Dead-hit option: placeholder hit at the centre of a dead OT sensor (LSTInputProducer deadHitDetIds), flagged by
  // this cluster size. It pairs with every hit of the live partner sensor into a minidoublet (see MiniDoublet.h).
  constexpr uint16_t kDeadHitClustSize = 0;
  // Which hit of a minidoublet is a placeholder (derived from the cluster sizes of its hits, see DeadHitPlacement.h)
  constexpr uint8_t kDeadHitAnchor = 1;
  constexpr uint8_t kDeadHitOuter = 2;
  // Dead stack: both sensors of the module are dead, the minidoublet is made of two placeholders (fully fake)
  constexpr uint8_t kDeadStack = kDeadHitAnchor | kDeadHitOuter;
  // Dead-hit options (LSTInputProducer deadHitOptions, bit mask), see src/alpaka/DeadHitPlacement.h. They only act on
  // placeholder minidoublets, so they change nothing without dead hits.
  namespace deadhit {
    constexpr uint32_t kBeamSpot = 1 << 0;                 // project and point from the beam spot, not the origin
    constexpr uint32_t kSegmentCircle = 1 << 1;            // segments place half-fake minidoublets on a circle
    constexpr uint32_t kSegmentTwoHalfFake = 1 << 2;       // segments of two half-fake minidoublets
    constexpr uint32_t kSegmentHalfAndFullyFake = 1 << 3;  // segments of a half-fake and a fully fake minidoublet
    constexpr uint32_t kT5StripErrors = 1 << 4;            // T5 chi2: strip-size errors for placeholder positions
    // Unused (no-op): it dropped the T5 tightCutFlag with a placeholder, and the retrained T5 DNN has no such flag.
    // The bit stays defined so that the option values of the earlier studies keep their meaning.
    constexpr uint32_t kNoTightFlagWithPlaceholder = 1 << 5;
    constexpr uint32_t kOnePlaceholderPerT3 = 1 << 6;  // at most one placeholder minidoublet per triplet
    constexpr uint32_t kAll = (1 << 7) - 1;            // all the options above
    // Set by LSTInputProducer (not an option) when the event has placeholder hits: without it every dead-hit check
    // is skipped and LST runs the nominal algorithm.
    constexpr uint32_t kPlaceholders = 1u << 31;
  }  // namespace deadhit

  constexpr float kB = lstgeometry::kB;
  constexpr float kC = lstgeometry::kC;

// Half precision wrapper functions.
#if defined(FP16_Base)
#define __F2H __float2half
#define __H2F __half2float
  typedef __half FPX;
#else
#define __F2H
#define __H2F
  typedef float FPX;
#endif

  // Defining the constant host device variables right up here
  // Currently pixel tracks treated as LSs with 2 double layers (IT layers 1+2 and 3+4) and 4 hits. To be potentially handled better in the future.
  struct Params_Modules {
    using ArrayU16xMaxConnected = edm::StdArray<uint16_t, max_connected_modules>;
  };
  struct Params_pLS {
    static constexpr int kLayers = 2, kHits = 4;
    static constexpr int kEmbed = 6;
    using ArrayUxHits = edm::StdArray<unsigned int, kHits>;
    using ArrayFxEmbed = edm::StdArray<float, kEmbed>;
  };
  struct Params_LS {
    static constexpr int kLayers = 2, kHits = 4;
    using ArrayUxLayers = edm::StdArray<unsigned int, kLayers>;
  };
  struct Params_T3 {
    static constexpr int kLayers = 3, kHits = 6;
    using ArrayU8xLayers = edm::StdArray<uint8_t, kLayers>;
    using ArrayU16xLayers = edm::StdArray<uint16_t, kLayers>;
    using ArrayUxHits = edm::StdArray<unsigned int, kHits>;
  };
  struct Params_pT3 {
    static constexpr int kLayers = 5, kHits = 10;
    using ArrayU8xLayers = edm::StdArray<uint8_t, kLayers>;
    using ArrayU16xLayers = edm::StdArray<uint16_t, kLayers>;
    using ArrayUxHits = edm::StdArray<unsigned int, kHits>;
  };
  struct Params_T4 {
    static constexpr int kLayers = 4, kHits = 8;
    using ArrayU8xLayers = edm::StdArray<uint8_t, kLayers>;
    using ArrayU16xLayers = edm::StdArray<uint16_t, kLayers>;
    using ArrayUxHits = edm::StdArray<unsigned int, kHits>;
  };
  struct Params_T5 {
    static constexpr int kLayers = 7, kHits = 14;  // 5 base + max 2 extensions
    static constexpr int kBaseLayers = 5;
    static constexpr int kEmbed = 6;
    using ArrayU8xLayers = edm::StdArray<uint8_t, kLayers>;
    using ArrayU16xLayers = edm::StdArray<uint16_t, kLayers>;
    using ArrayUxHits = edm::StdArray<unsigned int, kHits>;
    using ArrayFxEmbed = edm::StdArray<float, kEmbed>;
  };
  struct Params_pT5 {
    static constexpr int kLayers = 9, kHits = 18;  // 2 pixel + 7 OT (= T5::kLayers after extension)
    static constexpr int kBaseLayers = 7;
    using ArrayU8xLayers = edm::StdArray<uint8_t, kLayers>;
    using ArrayU16xLayers = edm::StdArray<uint16_t, kLayers>;
    using ArrayUxHits = edm::StdArray<unsigned int, kHits>;
  };
  struct Params_TC {
    static constexpr int kLayers = 13;
    static constexpr int kHitsPerLayer = 2;
    // Number of layers resevered for pixel hits.
    static constexpr int kPixelLayerSlots = 2;
    static constexpr int kHits = kLayers * kHitsPerLayer;
    using ArrayU8xLayers = edm::StdArray<uint8_t, kLayers>;
    using ArrayU16xLayers = edm::StdArray<uint16_t, kLayers>;
    using ArrayUHitsPerLayer = edm::StdArray<unsigned int, kHitsPerLayer>;
    using ArrayUxHits = edm::StdArray<ArrayUHitsPerLayer, kLayers>;
  };

  using ArrayIx2 = edm::StdArray<int, 2>;
  using ArrayUx2 = edm::StdArray<unsigned int, 2>;

}  //namespace lst

#endif
