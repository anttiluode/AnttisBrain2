# Horizon Net — first empirical run

*The resolution-horizon rule from the renderer, ported to a weight-tied network, tested today. Companion to resolution_horizon.md. Code: horizon_net.py (numpy only, runs in ~40 s). Raw numbers: horizon_net_results.json.*

## What was built

A weight-tied recurrent cell x ← tanh(Wx + Vu + b) with spectral norm of W pinned to ρ = 0.8 — a **certified contraction**. Readout by ridge regression (reservoir-style; the cell is a stand-in for any contracting iteration map, DEQ cells included). The new part is the halting rule:

At every step, the Banach a posteriori bound gives a hard guarantee on the distance to the infinite-depth fixed point: ‖x* − xₙ‖ ≤ ρ/(1−ρ) · ‖xₙ − xₙ₋₁‖. The network stops when that bound, pushed through the readout's Lipschitz constant, **proves the answer can no longer change**:

- classification: top-logit margin > ‖cᵢ − cⱼ‖ · bound for every rival class j → the argmax at infinite depth is certified equal to the current one;
- regression at b-bit resolution: ‖r‖ · bound < half a quantum → the quantized output is certified final.

This is the renderer's trick verbatim: don't run the recursion to depth ∞ — run it until the remaining trajectory is sub-resolution to the observer, and *prove* it.

## Results (2,000 test samples, 10 classes)

**The certificate is exact and cheap.** Certified halting: mean depth **6.2**, median 6, p90 8, max 12 — versus the 400-iteration reference. Predictions agree with infinite-depth predictions on **100.0%** of samples (accuracy identical to the digit: 0.6650 both ways). Not "almost the same answer faster" — provably the same answer, ~65× fewer iterations. Agreement held at 100% across every configuration tested (six ρ values, 2,000 samples each).

**The resolution-horizon law holds and is linear.** Demanding b bits of output resolution costs depth linear in b, measured slope **0.63 iterations/bit** vs **0.72** predicted from the *empirical* contraction rate ρ_eff = 0.38 (fitted from the update-norm decay; tanh saturation makes the true contraction much stronger than the spectral-norm guarantee). The worst-case-bound slope (3.1 it/bit from ρ = 0.8) is the guaranteed ceiling; reality runs ~5× under it. Doubling output precision costs a constant number of extra iterations — infinity priced logarithmically, exactly as in the game.

**Thrift knob confirmed.** Sweeping ρ from 0.5 → 0.95: mean certified depth rises 3.9 → 8.7 while certificate agreement stays 100% throughout. On *this* task accuracy is flat across ρ, so the strongest contraction is free — but that is a property of this static task, where extra effective memory buys nothing; on tasks needing more expressive fixed points, ρ is a genuine capacity/thrift tradeoff. Claimed only as observed.

**Where adaptivity is weak — reported, not hidden.** Halt depth barely tracks sample difficulty (5.5 easy-bin → 6.5 hard-bin). The theory says why: depth scales as log(1/margin), so even a 10× smaller margin costs only ~2.4 extra iterations at ρ_eff = 0.38. Strong contraction compresses the difficulty spectrum. If per-sample adaptivity is the goal, one *wants* weaker contraction — the mirror image of the thrift corollary.

## What this is and is not

**Is:** a working demonstration that the two-horizon truncation rule transfers from optics to inference as a *certified* anytime-computation scheme — stop with a proof, not a heuristic. Contrast: DEQ solvers stop on residual tolerances (arbitrary w.r.t. the decision), ACT/PonderNet/BranchyNet stop by learned or confidence heuristics with no guarantee.

**Is not (yet):** a trained architecture, a benchmark result, or a novelty claim. The reservoir readout caps accuracy at 0.665 on this deliberately noisy task; a trained cell would move that number but was not needed to test the halting rule, which is architecture-independent given contraction. The ingredients are all classical (Banach a posteriori bound; Lipschitz margins as in certified-robustness work; monotone-operator DEQs guarantee well-posedness nearby). Whether "Banach bound × decision margin = certified early exit" exists in print, I do not know — a literature pass through the DEQ and anytime-inference literature is the required next step before any claim.

**Measured discrepancy, logged:** slope 0.63 vs 0.72 predicted (~12%). Likely cause: ρ_eff was fitted on the mean update norm while per-sample decay rates vary; the linearity — the actual law — is clean in the plot.

## Next steps, in order of information gained per hour

1. Literature pass (DEQ stopping criteria, certified early-exit, anytime neural inference).
2. Same certificate on a *trained* weight-tied cell (spectral-normalized), a real dataset, wall-clock comparison against residual-tolerance stopping.
3. The transformer question: attention layers are not contractions, but weight-tied transformer blocks with normalization sometimes behave like ones empirically — measure ρ_eff on one and see whether the certificate is usable in practice even without the guarantee.
