#ifndef RecoTracker_LSTCore_src_alpaka_DeadHitPlacement_h
#define RecoTracker_LSTCore_src_alpaka_DeadHitPlacement_h

#include "HeterogeneousCore/AlpakaMath/interface/deltaPhi.h"

#include "RecoTracker/LSTCore/interface/alpaka/Common.h"
#include "RecoTracker/LSTCore/interface/Circle.h"
#include "RecoTracker/LSTCore/interface/LSTInputSoA.h"
#include "RecoTracker/LSTCore/interface/MiniDoubletsSoA.h"
#include "RecoTracker/LSTCore/interface/ModulesSoA.h"
#include "RecoTracker/LSTCore/interface/SegmentsSoA.h"
#include "RecoTracker/LSTCore/interface/TripletsSoA.h"

// Dead-hit option: one mechanism to update minidoublet positions per object, for dead sensors and dead modules.
//
// LSTInputProducer puts a placeholder hit (cluster size kDeadHitClustSize) at the centre of every listed dead OT sensor
// (deadHitDetIds). Minidoublets:
//   half-fake:  one placeholder and a live hit of the partner sensor (one sensor of the module dead). The placeholder
//               takes the live hit moved along the line from the beam point onto the dead sensor (MiniDoublet.h).
//   fully fake: two placeholders (whole module dead). The anchor stays at the centre of the dead module: it says
//               nothing about the track.
// Which hits of a minidoublet are placeholders is read from the cluster sizes of its hits in the input hits (the
// minidoublets store nothing more). These stored positions are only a starting point. Every object built on a
// placeholder minidoublet (segment, T3, T4, T5, pT3, pT5) updates its position from the object's own real hits, and
// reads all minidoublet positions through PlacedMiniDoublets: the updated position for its placeholder minidoublets,
// the stored one for all others. A minidoublet is shared by many objects, so nothing is written back. The updates:
//   segment (placeSegmentMDs): a half-fake minidoublet next to a real one with its real anchor (the clear case, e.g.
//          P real / S dead) gets the direction of the circle through the three real hits. A placeholder anchor, or two
//          half-fake minidoublets, use the circle through the beam point and the two live hits instead (pointing to
//          the beam spot): the anchor is moved along that circle onto the dead sensor and takes its direction. A fully
//          fake minidoublet is placed on the line from the beam point through the real minidoublet (Segment.h).
//   T3 and longer (placeObjectMDs): from the two nearest minidoublets of the object with a real anchor (the beam point
//          if there is only one): a fully fake minidoublet on the curve through them, a placeholder anchor moved along
//          the strip to their r-z line (PS) and along the circle through them and the live hit.
// The beam point is the beam spot (deadhit::kBeamSpot) or the origin. The input hits carry it, the option bits
// (LSTInputProducer deadHitOptions), the half sizes of the dead sensors (from the tracker geometry) and the tolerance
// on the positions placed on a dead module. LSTInputProducer sets deadhit::kPlaceholders only for events with
// placeholder hits: without it nothing is placed and every object reads the stored positions, identical to the
// nominal algorithm.

namespace ALPAKA_ACCELERATOR_NAMESPACE::lst {

  // At most this many placed minidoublets per object (a quintuplet has five)
  constexpr int kMaxPlacedMDs = Params_T5::kBaseLayers;

  // ---- event switches and flags

  // The event has placeholder hits (set by LSTInputProducer): without it all dead-hit code is skipped.
  ALPAKA_FN_ACC ALPAKA_FN_INLINE bool hasPlaceholderHits(HitsBaseConst hits) {
    return (hits.deadHitOptions() & deadhit::kPlaceholders) != 0;
  }

  ALPAKA_FN_ACC ALPAKA_FN_INLINE bool deadHitOption(HitsBaseConst hits, uint32_t option) {
    return (hits.deadHitOptions() & option) != 0;
  }

  // Which hits of minidoublet mdIndex are placeholders (kDeadHitAnchor, kDeadHitOuter), from their cluster sizes.
  ALPAKA_FN_ACC ALPAKA_FN_INLINE uint8_t deadHitFlags(MiniDoubletsConst mds, HitsBaseConst hits, unsigned int mdIndex) {
    if (not hasPlaceholderHits(hits))
      return 0;
    const bool deadAnchor = (hits.clustsize()[mds.anchorHitIndices()[mdIndex]] == kDeadHitClustSize);
    const bool deadOuter = (hits.clustsize()[mds.outerHitIndices()[mdIndex]] == kDeadHitClustSize);
    return (deadAnchor ? kDeadHitAnchor : 0) | (deadOuter ? kDeadHitOuter : 0);
  }

  // ---- points of the track

  // A point of the track: a minidoublet anchor, or the beam point (rt = 0: on the beam line).
  struct TrackPoint {
    float x, y, z, rt, phi;
  };

  ALPAKA_FN_ACC ALPAKA_FN_INLINE TrackPoint anchorPoint(MiniDoubletsConst mds, unsigned int mdIndex) {
    return {mds.anchorX()[mdIndex],
            mds.anchorY()[mdIndex],
            mds.anchorZ()[mdIndex],
            mds.anchorRt()[mdIndex],
            mds.anchorPhi()[mdIndex]};
  }

  // The beam spot with deadhit::kBeamSpot, else the origin.
  ALPAKA_FN_ACC ALPAKA_FN_INLINE TrackPoint beamPoint(HitsBaseConst hits) {
    if (not deadHitOption(hits, deadhit::kBeamSpot))
      return {0.f, 0.f, 0.f, 0.f, 0.f};
    return {hits.beamSpotX(), hits.beamSpotY(), hits.beamSpotZ(), 0.f, 0.f};
  }

  template <alpaka::concepts::Acc TAcc>
  ALPAKA_FN_ACC ALPAKA_FN_INLINE float etaFromRZ(TAcc const& acc, float rt, float z) {
    return alpaka::math::asinh(acc, z / rt);
  }

  // ---- placed positions

  // Position of a minidoublet as updated for one object. The anchor strip edges are not stored: they are computed
  // from the anchor (modules.edgeDx/edgeDy), so they follow the placed anchor.
  struct MDPlacement {
    unsigned int mdIndex;
    float x, y, z, rt, phi, eta;  // anchor
    float outerX, outerY, outerZ;
    float alpha;  // direction (dphichange), used if hasAlpha
    bool hasAlpha;
  };

  // Minidoublets as seen by one object: the placed position for its placeholder minidoublets, the stored one for all
  // others. Indexed like the MiniDoublets SoA (mds.anchorX()[mdIndex], ...). With no placement (always the case
  // without placeholder hits) it reads exactly the stored values.
  class PlacedMiniDoublets {
  public:
    enum class Column { anchorX, anchorY, anchorZ, anchorRt, anchorPhi, anchorEta, outerX, outerY, outerZ };

    template <Column C>
    class ColumnView {
    public:
      ALPAKA_FN_ACC ColumnView(PlacedMiniDoublets const& mds) : mds_(mds) {}
      ALPAKA_FN_ACC float operator[](unsigned int mdIndex) const { return mds_.value<C>(mdIndex); }

    private:
      PlacedMiniDoublets const& mds_;
    };

    ALPAKA_FN_ACC PlacedMiniDoublets(MiniDoubletsConst mds, HitsBaseConst hits)
        : mds_(mds), hits_(hits), nPlaced_(0), nPlaceholders_(0), nFullyFake_(0) {}

    ALPAKA_FN_ACC bool addPlacement(MDPlacement const& placement) {
      if (nPlaced_ >= kMaxPlacedMDs)
        return false;
      placed_[nPlaced_] = placement;
      ++nPlaced_;
      return true;
    }

    // placeholder minidoublets of the object (placed or not), and how many of them are fully fake
    ALPAKA_FN_ACC void setCounts(int nPlaceholders, int nFullyFake) {
      nPlaceholders_ = nPlaceholders;
      nFullyFake_ = nFullyFake;
    }

    ALPAKA_FN_ACC MiniDoubletsConst stored() const { return mds_; }
    ALPAKA_FN_ACC HitsBaseConst hits() const { return hits_; }
    ALPAKA_FN_ACC int nPlaced() const { return nPlaced_; }
    ALPAKA_FN_ACC int nPlaceholders() const { return nPlaceholders_; }
    ALPAKA_FN_ACC int nFullyFake() const { return nFullyFake_; }

    // event switches and placeholder flags (see the top of this file)
    ALPAKA_FN_ACC bool hasPlaceholderHits() const { return lst::hasPlaceholderHits(hits_); }
    ALPAKA_FN_ACC bool option(uint32_t option) const { return deadHitOption(hits_, option); }
    ALPAKA_FN_ACC uint8_t deadHitFlags(unsigned int mdIndex) const { return lst::deadHitFlags(mds_, hits_, mdIndex); }
    ALPAKA_FN_ACC bool hasPlaceholder(unsigned int mdIndex) const { return deadHitFlags(mdIndex) != 0; }
    ALPAKA_FN_ACC bool isDeadStack(unsigned int mdIndex) const { return deadHitFlags(mdIndex) == kDeadStack; }
    ALPAKA_FN_ACC bool hasDeadAnchor(unsigned int mdIndex) const {
      return (deadHitFlags(mdIndex) & kDeadHitAnchor) != 0;
    }

    ALPAKA_FN_ACC bool isPlaced(unsigned int mdIndex) const {
      for (int i = 0; i < nPlaced_; ++i) {
        if (placed_[i].mdIndex == mdIndex)
          return true;
      }
      return false;
    }

    // Direction (dphichange) of the minidoublet: the placed one if the object set it, else storedAlpha (the
    // minidoublet's own, MiniDoubletsBuild::dphichanges, in the segment stage).
    ALPAKA_FN_ACC float alpha(unsigned int mdIndex, float storedAlpha) const {
      for (int i = 0; i < nPlaced_; ++i) {
        if (placed_[i].mdIndex == mdIndex and placed_[i].hasAlpha)
          return placed_[i].alpha;
      }
      return storedAlpha;
    }

    ALPAKA_FN_ACC bool hasPlacedAlpha(unsigned int mdIndex) const {
      for (int i = 0; i < nPlaced_; ++i) {
        if (placed_[i].mdIndex == mdIndex)
          return placed_[i].hasAlpha;
      }
      return false;
    }

    // Positions, placed per object
    ALPAKA_FN_ACC ColumnView<Column::anchorX> anchorX() const { return {*this}; }
    ALPAKA_FN_ACC ColumnView<Column::anchorY> anchorY() const { return {*this}; }
    ALPAKA_FN_ACC ColumnView<Column::anchorZ> anchorZ() const { return {*this}; }
    ALPAKA_FN_ACC ColumnView<Column::anchorRt> anchorRt() const { return {*this}; }
    ALPAKA_FN_ACC ColumnView<Column::anchorPhi> anchorPhi() const { return {*this}; }
    ALPAKA_FN_ACC ColumnView<Column::anchorEta> anchorEta() const { return {*this}; }
    ALPAKA_FN_ACC ColumnView<Column::outerX> outerX() const { return {*this}; }
    ALPAKA_FN_ACC ColumnView<Column::outerY> outerY() const { return {*this}; }
    ALPAKA_FN_ACC ColumnView<Column::outerZ> outerZ() const { return {*this}; }

    // Everything else, as stored
    ALPAKA_FN_ACC auto anchorHitIndices() const { return mds_.anchorHitIndices(); }
    ALPAKA_FN_ACC auto outerHitIndices() const { return mds_.outerHitIndices(); }

    template <Column C>
    ALPAKA_FN_ACC float value(unsigned int mdIndex) const {
      for (int i = 0; i < nPlaced_; ++i) {
        if (placed_[i].mdIndex == mdIndex)
          return placedValue<C>(placed_[i]);
      }
      return storedValue<C>(mdIndex);
    }

  private:
    template <Column C>
    ALPAKA_FN_ACC float placedValue(MDPlacement const& p) const {
      if constexpr (C == Column::anchorX)
        return p.x;
      else if constexpr (C == Column::anchorY)
        return p.y;
      else if constexpr (C == Column::anchorZ)
        return p.z;
      else if constexpr (C == Column::anchorRt)
        return p.rt;
      else if constexpr (C == Column::anchorPhi)
        return p.phi;
      else if constexpr (C == Column::anchorEta)
        return p.eta;
      else if constexpr (C == Column::outerX)
        return p.outerX;
      else if constexpr (C == Column::outerY)
        return p.outerY;
      else
        return p.outerZ;
    }

    template <Column C>
    ALPAKA_FN_ACC float storedValue(unsigned int mdIndex) const {
      if constexpr (C == Column::anchorX)
        return mds_.anchorX()[mdIndex];
      else if constexpr (C == Column::anchorY)
        return mds_.anchorY()[mdIndex];
      else if constexpr (C == Column::anchorZ)
        return mds_.anchorZ()[mdIndex];
      else if constexpr (C == Column::anchorRt)
        return mds_.anchorRt()[mdIndex];
      else if constexpr (C == Column::anchorPhi)
        return mds_.anchorPhi()[mdIndex];
      else if constexpr (C == Column::anchorEta)
        return mds_.anchorEta()[mdIndex];
      else if constexpr (C == Column::outerX)
        return mds_.outerX()[mdIndex];
      else if constexpr (C == Column::outerY)
        return mds_.outerY()[mdIndex];
      else
        return mds_.outerZ()[mdIndex];
    }

    MiniDoubletsConst mds_;
    HitsBaseConst hits_;
    MDPlacement placed_[kMaxPlacedMDs];
    int nPlaced_;
    int nPlaceholders_;
    int nFullyFake_;
  };

  // Placeholder test usable on stored or placed minidoublets (stored ones carry no placeholder information).
  ALPAKA_FN_ACC ALPAKA_FN_INLINE bool hasPlaceholderMD(MiniDoubletsConst, unsigned int) { return false; }
  ALPAKA_FN_ACC ALPAKA_FN_INLINE bool hasPlaceholderMD(PlacedMiniDoublets const& mds, unsigned int mdIndex) {
    return mds.hasPlaceholder(mdIndex);
  }

  ALPAKA_FN_ACC ALPAKA_FN_INLINE MDPlacement storedPlacement(MiniDoubletsConst mds, unsigned int mdIndex) {
    MDPlacement placement;
    placement.mdIndex = mdIndex;
    placement.x = mds.anchorX()[mdIndex];
    placement.y = mds.anchorY()[mdIndex];
    placement.z = mds.anchorZ()[mdIndex];
    placement.rt = mds.anchorRt()[mdIndex];
    placement.phi = mds.anchorPhi()[mdIndex];
    placement.eta = mds.anchorEta()[mdIndex];
    placement.outerX = mds.outerX()[mdIndex];
    placement.outerY = mds.outerY()[mdIndex];
    placement.outerZ = mds.outerZ()[mdIndex];
    placement.alpha = 0.f;
    placement.hasAlpha = false;
    return placement;
  }

  // The anchor of a placement was moved in r-phi.
  template <alpaka::concepts::Acc TAcc>
  ALPAKA_FN_ACC ALPAKA_FN_INLINE void setMovedAnchor(TAcc const& acc, float x, float y, MDPlacement& placement) {
    placement.x = x;
    placement.y = y;
    placement.phi = alpaka::math::atan2(acc, y, x);
  }

  // ---- fully fake minidoublets: placement on the dead module

  // Surface and size of the dead module of a fully fake minidoublet.
  struct DeadModuleGeometry {
    float rc, zc, phic;  // centre of the dead anchor sensor
    float drdz;          // tilted barrel surface: r - rc = drdz * (z - zc), signed (tiltedSurfaceDrDz)
    float halfWidth;     // across the strips (r-phi)
    float halfLength;    // along the strips: z in the barrel, r in the endcap
    short subdet;
    bool isTilted;
  };

  // The half sizes are those of the dead sensors of the module type, from the tracker geometry (LSTInputProducer).
  ALPAKA_FN_ACC ALPAKA_FN_INLINE DeadModuleGeometry deadModuleGeometry(MiniDoubletsConst mds,
                                                                       HitsBaseConst hits,
                                                                       unsigned int mdIndex,
                                                                       short subdet,
                                                                       short side,
                                                                       short moduleType,
                                                                       float drdz) {
    DeadModuleGeometry dead;
    dead.rc = mds.anchorRt()[mdIndex];
    dead.zc = mds.anchorZ()[mdIndex];
    dead.phic = mds.anchorPhi()[mdIndex];
    dead.drdz = tiltedSurfaceDrDz(drdz, side);
    if (moduleType == PS) {
      dead.halfWidth = hits.deadSensorHalfWidthPS();
      dead.halfLength = hits.deadSensorHalfLengthPS();
    } else {
      dead.halfWidth = hits.deadSensorHalfWidth2S();
      dead.halfLength = hits.deadSensorHalfLength2S();
    }
    dead.subdet = subdet;
    dead.isTilted = (subdet == Barrel and side != Center);
    return dead;
  }

  ALPAKA_FN_ACC ALPAKA_FN_INLINE DeadModuleGeometry deadModuleGeometry(ModulesConst modules,
                                                                       MiniDoubletsConst mds,
                                                                       HitsBaseConst hits,
                                                                       unsigned int mdIndex,
                                                                       uint16_t lowerModuleIndex) {
    return deadModuleGeometry(mds,
                              hits,
                              mdIndex,
                              modules.subdets()[lowerModuleIndex],
                              modules.sides()[lowerModuleIndex],
                              modules.moduleType()[lowerModuleIndex],
                              modules.drdzs()[lowerModuleIndex]);
  }

  // Places the fully fake minidoublet on the dead module surface, on the track through the points a and b: r and z
  // linear in the fraction f along a -> b, phi linear in r (with a on the beam line, the straight line through b).
  // False if the track does not cross the surface, or crosses it outside the module half sizes plus the tolerances.
  template <alpaka::concepts::Acc TAcc>
  ALPAKA_FN_ACC ALPAKA_FN_INLINE bool placeOnDeadModule(TAcc const& acc,
                                                        DeadModuleGeometry const& dead,
                                                        TrackPoint const& a,
                                                        TrackPoint const& b,
                                                        bool aOnBeamLine,
                                                        float transverseTolerance,
                                                        float longitudinalTolerance,
                                                        MDPlacement& placed) {
    const float dr = b.rt - a.rt;
    const float dz = b.z - a.z;
    float numerator, denominator;
    if (dead.subdet == Endcap) {
      numerator = dead.zc - a.z;
      denominator = dz;
    } else if (not dead.isTilted) {
      numerator = dead.rc - a.rt;
      denominator = dr;
    } else {
      numerator = (dead.rc - a.rt) - dead.drdz * (dead.zc - a.z);
      denominator = dr - dead.drdz * dz;
    }
    constexpr float kMinDenominator = 1e-6f;  // the track runs parallel to the module surface
    if (alpaka::math::abs(acc, denominator) < kMinDenominator)
      return false;
    const float f = numerator / denominator;

    const float rt = a.rt + f * dr;
    const float z = a.z + f * dz;
    if (rt <= 0.f)
      return false;
    const float phi = aOnBeamLine ? b.phi
                                  : cms::alpakatools::reducePhiRange(
                                        acc, a.phi + f * cms::alpakatools::reducePhiRange(acc, b.phi - a.phi));

    // The track must cross the dead module itself, not only its surface.
    const float transverseOffset = rt * alpaka::math::abs(acc, cms::alpakatools::reducePhiRange(acc, phi - dead.phic));
    float longitudinalOffset;
    if (dead.subdet == Endcap) {
      longitudinalOffset = alpaka::math::abs(acc, rt - dead.rc);
    } else if (not dead.isTilted) {
      longitudinalOffset = alpaka::math::abs(acc, z - dead.zc);
    } else {
      longitudinalOffset = alpaka::math::sqrt(acc, (rt - dead.rc) * (rt - dead.rc) + (z - dead.zc) * (z - dead.zc));
    }
    if (transverseOffset > dead.halfWidth + transverseTolerance)
      return false;
    if (longitudinalOffset > dead.halfLength + longitudinalTolerance)
      return false;

    // A fully fake minidoublet collapses to its anchor: it has no measured direction.
    placed.rt = rt;
    placed.z = z;
    placed.phi = phi;
    placed.x = rt * alpaka::math::cos(acc, phi);
    placed.y = rt * alpaka::math::sin(acc, phi);
    placed.eta = etaFromRZ(acc, rt, z);
    placed.outerX = placed.x;
    placed.outerY = placed.y;
    placed.outerZ = placed.z;
    return true;
  }

  // ---- half-fake minidoublets: moving a placeholder anchor

  // Moves the point (liveX, liveY) along the circle (centerX, centerY, radius) to the radius targetRt. False if there
  // is no circle (radius <= 0) or the track runs along the sensor.
  template <alpaka::concepts::Acc TAcc>
  ALPAKA_FN_ACC ALPAKA_FN_INLINE bool moveAlongCircle(TAcc const& acc,
                                                      float liveX,
                                                      float liveY,
                                                      float centerX,
                                                      float centerY,
                                                      float radius,
                                                      float targetRt,
                                                      float& x,
                                                      float& y) {
    if (not(radius > 0.f))
      return false;
    const float liveRt = alpaka::math::sqrt(acc, liveX * liveX + liveY * liveY);
    // unit tangent of the circle at the live hit, pointing outwards
    float tangentX = -(liveY - centerY) / radius;
    float tangentY = (liveX - centerX) / radius;
    float drds = (tangentX * liveX + tangentY * liveY) / liveRt;
    if (drds < 0.f) {
      tangentX = -tangentX;
      tangentY = -tangentY;
      drds = -drds;
    }
    constexpr float kMinDrDs = 0.1f;  // the track runs (almost) along the sensor: the move is not defined
    if (drds <= kMinDrDs)
      return false;
    // arc length to the target radius; the circle bends towards its centre by ds^2 / 2R
    const float ds = (targetRt - liveRt) / drds;
    const float bend = 0.5f * ds * ds / radius;
    x = liveX + ds * tangentX + bend * (centerX - liveX) / radius;
    y = liveY + ds * tangentY + bend * (centerY - liveY) / radius;
    const float scaleToRadius = targetRt / alpaka::math::sqrt(acc, x * x + y * y);
    x *= scaleToRadius;
    y *= scaleToRadius;
    return true;
  }

  // r-z: move the anchor of a PS module along its strip to the r-z line through the points ref1 and ref2, by at most
  // half a strip length (the live hit is a strip hit: its position along the strip is not measured).
  template <alpaka::concepts::Acc TAcc>
  ALPAKA_FN_ACC ALPAKA_FN_INLINE void moveAnchorAlongStrip(TAcc const& acc,
                                                           ModulesConst modules,
                                                           uint16_t lowerModuleIndex,
                                                           TrackPoint const& ref1,
                                                           TrackPoint const& ref2,
                                                           MDPlacement& anchor) {
    // unit direction of the strip in the r-z plane
    float stripR = 0.f;
    float stripZ = 1.f;
    if (modules.subdets()[lowerModuleIndex] == Endcap) {
      stripR = 1.f;
      stripZ = 0.f;
    } else if (modules.sides()[lowerModuleIndex] != Center) {
      const float drdz = tiltedSurfaceDrDz(modules.drdzs()[lowerModuleIndex], modules.sides()[lowerModuleIndex]);
      stripZ = 1.f / alpaka::math::sqrt(acc, 1.f + drdz * drdz);
      stripR = drdz * stripZ;
    }

    // ref1 + s * (ref2 - ref1) = anchor + u * strip, solved for the shift u along the strip (2D cross products)
    const float lineR = ref2.rt - ref1.rt;
    const float lineZ = ref2.z - ref1.z;
    const float toAnchorR = anchor.rt - ref1.rt;
    const float toAnchorZ = anchor.z - ref1.z;
    const float lineCrossStrip = lineR * stripZ - lineZ * stripR;
    const float lineLength = alpaka::math::sqrt(acc, lineR * lineR + lineZ * lineZ);
    constexpr float kMinSinAngle = 1e-3f;  // line (almost) along the strip: no crossing
    if (alpaka::math::abs(acc, lineCrossStrip) < kMinSinAngle * lineLength)
      return;
    float shift = (toAnchorR * lineZ - toAnchorZ * lineR) / lineCrossStrip;

    const float halfStrip = 0.5f * kStripPSZpitch;
    shift = alpaka::math::min(acc, alpaka::math::max(acc, shift, -halfStrip), halfStrip);
    anchor.rt += shift * stripR;
    anchor.z += shift * stripZ;
  }

  // Placeholder anchor of a half-fake minidoublet, refined from two points of the track: along the strip in r-z (PS),
  // then the live hit (outer hit of the minidoublet) along the circle through it and the two points.
  template <alpaka::concepts::Acc TAcc>
  ALPAKA_FN_ACC ALPAKA_FN_INLINE void refineDeadAnchor(TAcc const& acc,
                                                       ModulesConst modules,
                                                       MiniDoubletsConst mds,
                                                       uint16_t lowerModuleIndex,
                                                       TrackPoint const& ref1,
                                                       TrackPoint const& ref2,
                                                       MDPlacement& placement) {
    const unsigned int mdIndex = placement.mdIndex;
    const float storedRt = placement.rt;
    if (modules.moduleType()[lowerModuleIndex] == PS)
      moveAnchorAlongStrip(acc, modules, lowerModuleIndex, ref1, ref2, placement);

    // the live hit moves radially with the anchor along the strip
    const float liveX = mds.outerX()[mdIndex];
    const float liveY = mds.outerY()[mdIndex];
    const float liveRt = alpaka::math::sqrt(acc, liveX * liveX + liveY * liveY);
    const float liveScale = (liveRt + placement.rt - storedRt) / liveRt;

    float radius, centerX, centerY;
    std::tie(radius, centerX, centerY) =
        computeRadiusFromThreeAnchorHits(acc, ref1.x, ref1.y, ref2.x, ref2.y, liveScale * liveX, liveScale * liveY);
    float x, y;
    if (not moveAlongCircle(acc, liveScale * liveX, liveScale * liveY, centerX, centerY, radius, placement.rt, x, y)) {
      // no circle: keep the stored direction from the beam point, at the new radius
      x = mds.anchorX()[mdIndex] * placement.rt / storedRt;
      y = mds.anchorY()[mdIndex] * placement.rt / storedRt;
    }
    setMovedAnchor(acc, x, y, placement);
    placement.eta = etaFromRZ(acc, placement.rt, placement.z);
  }

  // ---- objects with three or more minidoublets

  // The (up to) two minidoublets nearest to minidoublet k in layer order whose anchors are real hits, ref1 < ref2.
  ALPAKA_FN_ACC ALPAKA_FN_INLINE int findReferenceMDs(
      PlacedMiniDoublets const& mds, const unsigned int* mdIndices, int nMDs, int k, int& ref1, int& ref2) {
    int found[2] = {-1, -1};
    int nFound = 0;
    for (int distance = 1; distance < nMDs and nFound < 2; ++distance) {
      const int candidates[2] = {k - distance, k + distance};
      for (int candidate : candidates) {
        if (nFound == 2 or candidate < 0 or candidate >= nMDs)
          continue;
        if (mds.hasDeadAnchor(mdIndices[candidate]))
          continue;
        found[nFound] = candidate;
        ++nFound;
      }
    }
    ref1 = (nFound == 2 and found[1] < found[0]) ? found[1] : found[0];
    ref2 = (nFound == 2 and found[1] < found[0]) ? found[0] : found[1];
    return nFound;
  }

  // Updates the placeholder minidoublets of an object with nMDs >= 3 minidoublets (mdIndices and their lower modules
  // lowerModuleIndices from inner to outer):
  //   fully fake: on the curve through the two nearest minidoublets with a real anchor; the object is not built if
  //               there are not two, if the track misses the dead module, or with two adjacent fully fake ones.
  //   placeholder anchor: refined from the two nearest real anchors (the beam point and the one if there is only one).
  //   placeholder outer hit: the anchor is real, nothing to place.
  // With deadhit::kOnePlaceholderPerT3 a triplet has at most one placeholder minidoublet. False: no such object.
  template <alpaka::concepts::Acc TAcc>
  ALPAKA_FN_ACC ALPAKA_FN_INLINE bool placeObjectMDs(TAcc const& acc,
                                                     ModulesConst modules,
                                                     const uint16_t* lowerModuleIndices,
                                                     const unsigned int* mdIndices,
                                                     int nMDs,
                                                     PlacedMiniDoublets& placedMDs) {
    if (not placedMDs.hasPlaceholderHits())
      return true;

    int nPlaceholders = 0;
    int nFullyFake = 0;
    for (int k = 0; k < nMDs; ++k) {
      if (placedMDs.hasPlaceholder(mdIndices[k]))
        ++nPlaceholders;
      if (placedMDs.isDeadStack(mdIndices[k]))
        ++nFullyFake;
    }
    placedMDs.setCounts(nPlaceholders, nFullyFake);
    if (nPlaceholders == 0)
      return true;

    if (nMDs == Params_T3::kLayers and nPlaceholders > 1 and placedMDs.option(deadhit::kOnePlaceholderPerT3))
      return false;
    for (int k = 0; k + 1 < nMDs; ++k) {
      if (placedMDs.isDeadStack(mdIndices[k]) and placedMDs.isDeadStack(mdIndices[k + 1]))
        return false;
    }

    MiniDoubletsConst mds = placedMDs.stored();
    HitsBaseConst hits = placedMDs.hits();
    for (int k = 0; k < nMDs; ++k) {
      if (not placedMDs.hasDeadAnchor(mdIndices[k]))
        continue;
      int ref1, ref2;
      const int nRefs = findReferenceMDs(placedMDs, mdIndices, nMDs, k, ref1, ref2);
      MDPlacement placement = storedPlacement(mds, mdIndices[k]);

      if (placedMDs.isDeadStack(mdIndices[k])) {
        if (nRefs < 2)
          return false;
        const float tolerance = hits.deadHitTolerance();
        if (not placeOnDeadModule(acc,
                                  deadModuleGeometry(modules, mds, hits, mdIndices[k], lowerModuleIndices[k]),
                                  anchorPoint(mds, mdIndices[ref1]),
                                  anchorPoint(mds, mdIndices[ref2]),
                                  false,
                                  tolerance,
                                  tolerance,
                                  placement))
          return false;
      } else {
        if (nRefs == 0)
          continue;
        const TrackPoint first = (nRefs == 2) ? anchorPoint(mds, mdIndices[ref1]) : beamPoint(hits);
        const TrackPoint second = (nRefs == 2) ? anchorPoint(mds, mdIndices[ref2]) : anchorPoint(mds, mdIndices[ref1]);
        refineDeadAnchor(acc, modules, mds, lowerModuleIndices[k], first, second, placement);
      }
      if (not placedMDs.addPlacement(placement))
        return false;
    }
    return true;
  }

  // The minidoublets of a triplet as seen by it, with its placeholder minidoublets placed from its real ones.
  // False if the triplet cannot be built with its placeholder minidoublets.
  template <alpaka::concepts::Acc TAcc>
  ALPAKA_FN_ACC ALPAKA_FN_INLINE bool placeTripletMDs(TAcc const& acc,
                                                      ModulesConst modules,
                                                      SegmentsConst segments,
                                                      unsigned int innerSegmentIndex,
                                                      unsigned int outerSegmentIndex,
                                                      uint16_t innerInnerLowerModuleIndex,
                                                      uint16_t middleLowerModuleIndex,
                                                      uint16_t outerOuterLowerModuleIndex,
                                                      PlacedMiniDoublets& placedMDs) {
    if (not placedMDs.hasPlaceholderHits())
      return true;
    const unsigned int mdIndices[Params_T3::kLayers] = {segments.mdIndices()[innerSegmentIndex][0],
                                                        segments.mdIndices()[innerSegmentIndex][1],
                                                        segments.mdIndices()[outerSegmentIndex][1]};
    const uint16_t lowerModuleIndices[Params_T3::kLayers] = {
        innerInnerLowerModuleIndex, middleLowerModuleIndex, outerOuterLowerModuleIndex};
    return placeObjectMDs(acc, modules, lowerModuleIndices, mdIndices, Params_T3::kLayers, placedMDs);
  }

  // The same for a stored triplet.
  template <alpaka::concepts::Acc TAcc>
  ALPAKA_FN_ACC ALPAKA_FN_INLINE bool placeTripletMDs(TAcc const& acc,
                                                      ModulesConst modules,
                                                      SegmentsConst segments,
                                                      TripletsConst triplets,
                                                      unsigned int tripletIndex,
                                                      PlacedMiniDoublets& placedMDs) {
    return placeTripletMDs(acc,
                           modules,
                           segments,
                           triplets.segmentIndices()[tripletIndex][0],
                           triplets.segmentIndices()[tripletIndex][1],
                           triplets.lowerModuleIndices()[tripletIndex][0],
                           triplets.lowerModuleIndices()[tripletIndex][1],
                           triplets.lowerModuleIndices()[tripletIndex][2],
                           placedMDs);
  }

  // The minidoublets of a quintuplet (inner and outer triplet) as seen by it. False if the quintuplet cannot be built
  // with its placeholder minidoublets.
  template <alpaka::concepts::Acc TAcc>
  ALPAKA_FN_ACC ALPAKA_FN_INLINE bool placeQuintupletMDs(TAcc const& acc,
                                                         ModulesConst modules,
                                                         SegmentsConst segments,
                                                         TripletsConst triplets,
                                                         unsigned int innerTripletIndex,
                                                         unsigned int outerTripletIndex,
                                                         PlacedMiniDoublets& placedMDs) {
    if (not placedMDs.hasPlaceholderHits())
      return true;
    const auto& segmentIndices = triplets.segmentIndices();
    const auto& tripletModules = triplets.lowerModuleIndices();
    const unsigned int mdIndices[Params_T5::kBaseLayers] = {
        segments.mdIndices()[segmentIndices[innerTripletIndex][0]][0],
        segments.mdIndices()[segmentIndices[innerTripletIndex][1]][0],
        segments.mdIndices()[segmentIndices[innerTripletIndex][1]][1],
        segments.mdIndices()[segmentIndices[outerTripletIndex][0]][1],
        segments.mdIndices()[segmentIndices[outerTripletIndex][1]][1]};
    const uint16_t lowerModuleIndices[Params_T5::kBaseLayers] = {tripletModules[innerTripletIndex][0],
                                                                 tripletModules[innerTripletIndex][1],
                                                                 tripletModules[innerTripletIndex][2],
                                                                 tripletModules[outerTripletIndex][1],
                                                                 tripletModules[outerTripletIndex][2]};
    return placeObjectMDs(acc, modules, lowerModuleIndices, mdIndices, Params_T5::kBaseLayers, placedMDs);
  }

  // ---- segments

  // Angle between the outward tangent of the circle (centerX, centerY) at the point (x, y) and the radial direction:
  // the direction (dphichange) that a minidoublet on this circle measures.
  template <alpaka::concepts::Acc TAcc>
  ALPAKA_FN_ACC ALPAKA_FN_INLINE float tangentAlpha(TAcc const& acc, float centerX, float centerY, float x, float y) {
    float tangentX = -(y - centerY);
    float tangentY = x - centerX;
    if (tangentX * x + tangentY * y < 0.f) {
      tangentX = -tangentX;
      tangentY = -tangentY;
    }
    return cms::alpakatools::reducePhiRange(
        acc, alpaka::math::atan2(acc, tangentY, tangentX) - alpaka::math::atan2(acc, y, x));
  }

  // The real hit of a half-fake minidoublet: its anchor, or its outer hit if the anchor is the placeholder.
  ALPAKA_FN_ACC ALPAKA_FN_INLINE void liveHit(PlacedMiniDoublets const& placedMDs,
                                              unsigned int mdIndex,
                                              float& x,
                                              float& y) {
    MiniDoubletsConst mds = placedMDs.stored();
    const bool deadAnchor = placedMDs.hasDeadAnchor(mdIndex);
    x = deadAnchor ? mds.outerX()[mdIndex] : mds.anchorX()[mdIndex];
    y = deadAnchor ? mds.outerY()[mdIndex] : mds.anchorY()[mdIndex];
  }

  // Segment of two minidoublets, none fully fake (Segment.h handles those), at least one half-fake. Without
  // deadhit::kSegmentCircle nothing is placed (the segment then takes chord-consistent directions). With it, each
  // half-fake minidoublet gets the direction of a circle, and a placeholder anchor moves along that circle onto the
  // dead sensor (see the top of this file). False: two half-fake minidoublets without deadhit::kSegmentTwoHalfFake.
  template <alpaka::concepts::Acc TAcc>
  ALPAKA_FN_ACC ALPAKA_FN_INLINE bool placeSegmentMDs(TAcc const& acc,
                                                      unsigned int innerMDIndex,
                                                      unsigned int outerMDIndex,
                                                      PlacedMiniDoublets& placedMDs) {
    if (not placedMDs.hasPlaceholderHits())
      return true;
    const bool innerIsHalfFake = placedMDs.hasPlaceholder(innerMDIndex);
    const bool outerIsHalfFake = placedMDs.hasPlaceholder(outerMDIndex);
    if (not innerIsHalfFake and not outerIsHalfFake)
      return true;
    placedMDs.setCounts(int(innerIsHalfFake) + int(outerIsHalfFake), 0);
    if (innerIsHalfFake and outerIsHalfFake and not placedMDs.option(deadhit::kSegmentTwoHalfFake))
      return false;
    if (not placedMDs.option(deadhit::kSegmentCircle))
      return true;

    MiniDoubletsConst mds = placedMDs.stored();
    const TrackPoint beam = beamPoint(placedMDs.hits());
    float radius, centerX, centerY;
    if (innerIsHalfFake != outerIsHalfFake) {
      const unsigned int halfFakeMDIndex = innerIsHalfFake ? innerMDIndex : outerMDIndex;
      const unsigned int realMDIndex = innerIsHalfFake ? outerMDIndex : innerMDIndex;
      const float realX = mds.anchorX()[realMDIndex];
      const float realY = mds.anchorY()[realMDIndex];
      float liveX, liveY;
      liveHit(placedMDs, halfFakeMDIndex, liveX, liveY);
      radius = -1.f;
      if (not placedMDs.hasDeadAnchor(halfFakeMDIndex)) {
        // the clear case (e.g. P real / S dead): circle through the three real hits
        std::tie(radius, centerX, centerY) = computeRadiusFromThreeAnchorHits(
            acc, realX, realY, mds.outerX()[realMDIndex], mds.outerY()[realMDIndex], liveX, liveY);
      }
      if (not(radius > 0.f)) {
        // placeholder anchor, or no circle through the real hits: point to the beam spot
        std::tie(radius, centerX, centerY) =
            computeRadiusFromThreeAnchorHits(acc, beam.x, beam.y, realX, realY, liveX, liveY);
      }
    } else {
      // two half-fake minidoublets: two real hits, point to the beam spot
      float innerX, innerY, outerX, outerY;
      liveHit(placedMDs, innerMDIndex, innerX, innerY);
      liveHit(placedMDs, outerMDIndex, outerX, outerY);
      std::tie(radius, centerX, centerY) =
          computeRadiusFromThreeAnchorHits(acc, beam.x, beam.y, innerX, innerY, outerX, outerY);
    }
    if (not(radius > 0.f))
      return true;  // no circle: chord-consistent directions

    const unsigned int mdIndices[2] = {innerMDIndex, outerMDIndex};
    for (unsigned int mdIndex : mdIndices) {
      if (not placedMDs.hasPlaceholder(mdIndex))
        continue;
      MDPlacement placement = storedPlacement(mds, mdIndex);
      if (placedMDs.hasDeadAnchor(mdIndex)) {
        float x, y;
        if (moveAlongCircle(
                acc, mds.outerX()[mdIndex], mds.outerY()[mdIndex], centerX, centerY, radius, placement.rt, x, y))
          setMovedAnchor(acc, x, y, placement);
      }
      placement.alpha = tangentAlpha(acc, centerX, centerY, placement.x, placement.y);
      placement.hasAlpha = true;
      placedMDs.addPlacement(placement);
    }
    return true;
  }

  // A segment with a fully fake minidoublet (dead stack), from its two minidoublets or from the stored segment.
  ALPAKA_FN_ACC ALPAKA_FN_INLINE bool segmentHasDeadStackMDs(PlacedMiniDoublets const& mds,
                                                             unsigned int innerMDIndex,
                                                             unsigned int outerMDIndex) {
    if (not mds.hasPlaceholderHits())
      return false;
    return mds.isDeadStack(innerMDIndex) or mds.isDeadStack(outerMDIndex);
  }

  ALPAKA_FN_ACC ALPAKA_FN_INLINE bool segmentHasDeadStack(PlacedMiniDoublets const& mds,
                                                          SegmentsConst segments,
                                                          unsigned int segmentIndex) {
    return segmentHasDeadStackMDs(mds, segments.mdIndices()[segmentIndex][0], segments.mdIndices()[segmentIndex][1]);
  }

  // A segment with a placed minidoublet has the direction of its stored positions, which the object has updated: the
  // object recomputes it as in the segment algorithm (Segment.h): chord direction relative to the inner anchor in the
  // barrel, phi change extrapolated in z otherwise. innerModuleIndex and outerModuleIndex are the lower modules of the
  // two minidoublets of the segment.
  template <alpaka::concepts::Acc TAcc>
  ALPAKA_FN_ACC ALPAKA_FN_INLINE float segmentAlpha(TAcc const& acc,
                                                    ModulesConst modules,
                                                    PlacedMiniDoublets const& mds,
                                                    SegmentsConst segments,
                                                    unsigned int segmentIndex,
                                                    uint16_t innerModuleIndex,
                                                    uint16_t outerModuleIndex,
                                                    float storedAlpha) {
    if (mds.nPlaced() == 0)
      return storedAlpha;
    const unsigned int innerMDIndex = segments.mdIndices()[segmentIndex][0];
    const unsigned int outerMDIndex = segments.mdIndices()[segmentIndex][1];
    if (not mds.isPlaced(innerMDIndex) and not mds.isPlaced(outerMDIndex))
      return storedAlpha;
    const bool isBarrel = modules.subdets()[innerModuleIndex] == Barrel and modules.subdets()[outerModuleIndex] == Barrel;
    if (isBarrel) {
      const float chordPhi = cms::alpakatools::phi(acc,
                                                   mds.anchorX()[outerMDIndex] - mds.anchorX()[innerMDIndex],
                                                   mds.anchorY()[outerMDIndex] - mds.anchorY()[innerMDIndex]);
      return cms::alpakatools::reducePhiRange(acc, chordPhi - mds.anchorPhi()[innerMDIndex]);
    }
    const float dPhi =
        cms::alpakatools::reducePhiRange(acc, mds.anchorPhi()[outerMDIndex] - mds.anchorPhi()[innerMDIndex]);
    const float dzFrac = (mds.anchorZ()[outerMDIndex] - mds.anchorZ()[innerMDIndex]) / mds.anchorZ()[innerMDIndex];
    return dPhi / dzFrac * (1.f + dzFrac);
  }

}  // namespace ALPAKA_ACCELERATOR_NAMESPACE::lst

#endif
