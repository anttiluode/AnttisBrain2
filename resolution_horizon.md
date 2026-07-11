# The Resolution Horizon

### Why four bounces look infinite, what the accident actually computed, and where the trick generalizes

*PerceptionLab note — July 2026. Written against the AnttisBrain / AnttisBrain2 lineage (aeon forge → rajapinta → inspiration.html (index.html at anttis brain rep)
→ brain descent). Honest ledger at the end. Do not hype. Do not lie. Just show.*

---

## 1. What the fast version actually computes

Strip inspiration.html to its mathematical skeleton. There is a boundary function

**g(ray)** — the emission you see when a ray terminates: webcam texture on a wall or moon surface, sampled equirectangularly.

There is a bounce map

**R(ray)** — a deterministic map on ray space (position × direction). One application of R = "flow the ray through the lensing field until it hits a surface, then reflect." The gravitational bending is an eikonal flow between surfaces; the reflection is a surface event. Nothing ever enters a volume.

And there is a per-bounce weight **λ ≈ 0.62** (tint × accumulation).

The rendered image at a pixel is then exactly

> **I = g + λ·g∘R + λ²·g∘R² + λ³·g∘R³ + λ⁴·g∘R⁴**

a truncated geometric series in the **composition operator** U_R f = f∘R. In closed form, what the shader is approximating is

> **I = (Id − λU_R)⁻¹ g**

— the discounted resolvent of a Koopman/transfer operator applied to boundary data. This is not a metaphor. It is literally the code: `accum += tint * eqSample(...); rd = reflect(...); tint *= 0.62;` is the loop body of a Neumann series for that resolvent, and `maxBnc = 4` is its truncation order.

So the object that produced the "mind-blowing endless rooms" is a well-studied one: a **Ruelle-type transfer operator resolvent**, evaluated per pixel, in real time, with the webcam as the boundary condition. The rendering equation has been an operator equation since Kajiya (1986); the specific structure here — *purely* surface events, deterministic bounce map, vacuum lensing between events — is what makes the operator a clean composition operator instead of a high-dimensional integral operator, and that is what makes it cheap.

## 2. The two horizons — why 4 = ∞

Truncating a geometric series is only legitimate if the tail is invisible. There are two independent reasons it becomes invisible, and they have different mathematics.

**Amplitude horizon.** The n-th term carries weight λⁿ. It drops below a contrast threshold ε_c (Weber threshold ~1%, or display quantization 1/255 ≈ 0.4%) after

> **N_amp = ln ε_c / ln λ**

With λ = 0.62, N_amp ≈ 9–11. This is the familiar horizon — identical to the *effective horizon* 1/(1−γ) of a discounted Bellman operator in reinforcement learning. It alone would predict you need ~10 bounces. You don't. Something else cuts in first.

**Resolution horizon.** Each application of R is not just a re-weighting — it is a **spatial contraction of image content**. A convex mirror of radius r seen from distance d demagnifies by roughly m ≈ r/(2d); with moons of r ≈ 0.5–1 in rooms of span ~6, m ≈ 0.1–0.25 per bounce, and the gravitational fisheye compresses the periphery further. Features of the level-0 scene, spanning ~500 pixels on screen, shrink to sub-pixel scale after

> **N_res = ln(p/L) / ln m**

pixels p, initial feature scale L. With m = 0.2 and L/p = 500: N_res = log 500 / log 5 ≈ **3.9**.

**Effective depth is min(N_amp, N_res).** In inspiration.html the resolution horizon binds, and it binds at four. `maxBnc = 4` was not a tuned budget that happened to look good — it is the *provably correct* truncation order for that contraction ratio at that resolution. The infinity was never faked; the series genuinely converges, in the only norm that matters (what a retina/display can distinguish), at depth 4.

Two corollaries worth stating because they are counterintuitive and testable:

**Corollary 1 (extravagance is thrift).** Stronger lensing → smaller m → smaller N_res. The *more* warped and recursive the image looks, the *fewer* bounces are needed to make it exact-to-perception. Visual extravagance and computational cost move in opposite directions. This is the precise inversion of the intuition that killed the Descent builds ("deeper magic needs a deeper march").

**Corollary 2 (falsifiable tonight).** N_res grows logarithmically with resolution. Render at 4× the pixel count and the 5th bounce should become *just* visible at moon centers where the contraction is weakest; at current resolution it should be strictly invisible. One evening, one slider, one screenshot pair. If bounce 5 is visible at 1080p, the analysis above is wrong.

## 3. Why the "honest" version had to die

The Snell/Beer–Lambert build was not merely slower — it was structurally incapable of the recursion, and the two-horizon frame says why. A ray's budget is spent in operator applications. Interior transport (26-step chord march, TIR, exit refraction) burns tens of SDF evaluations to compute **one** application of a *transmission* map — a map which, for a homogeneous convex body seen from outside, is fully characterized by its **boundary ray-transfer map** T: (entry ray) → (exit ray). The interior march is a brute-force evaluation of a 4-dimensional boundary-to-boundary map. Every one of those steps was reconstructing information that, for an exterior observer, lives entirely on the surface.

That is the holographic principle stated at the level of a renderer, and it is rigorous here in a way it usually isn't: the exterior light field of a homogeneous transparent body **is** a function on boundary ray space, full stop. Any implementation that reproduces T is exact; marching the bulk is one implementation, the most expensive one. The repo's own name — rajapinta, *interface* — was the design document. The GPU watchdog merely enforced it.

One honesty note on the substitution actually used: a point-mass lens (deflection ∝ 1/b) is **not** the first-order match of a glass ball (thin lens, deflection ∝ b). The profiles differ; gravity gives Einstein-ring-like compression of the periphery, glass gives focal convergence. The game's vacuum lensing is a *perceptual* stand-in for refraction, not an analytic one. The rigorous umbrella that says a stand-in must exist is transformation optics / the Gordon metric (1923): any ray map realizable by a medium is realizable by a metric, and vice versa. If one ever wanted the exact glass-ball look from a vacuum field, the deflection profile is a one-line change — but "perceptually equivalent at 5% of the cost" was the actual discovery, and it should be claimed as exactly that.

## 4. The 2D ancestor

This construction has a distinguished ancestor: Escher's *Print Gallery*, whose "picture containing itself" was shown by de Smit & Lenstra (2003) to be the exponential of a conformal map with a complex scale factor — a spatial contraction composed with rotation, iterated, truncated where the printing resolution gives out. The Droste effect **is** the resolution-horizon principle in 2D conformal form. Cascade mode is a real-time, 3D, non-conformal Droste operator with a webcam boundary condition. Knowing the ancestor matters because the 2D theory is complete, and it says the same thing: the apparent infinite regress is a finite object plus a contraction, and the regress depth you must actually compute is set by resolution, nothing else.

## 5. Where the pattern already lives under other names

Being honest about novelty means listing the fields where this exact structure is established:

- **Boundary element methods.** When the bulk is homogeneous (Green's function known), PDE problems reduce by one dimension to the boundary. The renderer rediscovered BEM economics: bulk homogeneous → all information on the interface.
- **Deep equilibrium models** (Bai–Kolter–Koltun 2019). Weight-tied networks defined as fixed points of contraction maps; few iterations suffice because the map contracts. Same theorem, representation space instead of ray space.
- **Reservoir computing.** The echo-state property *is* a contraction condition; fading memory *is* the amplitude horizon. The less-quoted half: a reservoir's *useful* memory is also bounded by readout resolution over contraction rate — the resolution horizon, wearing a different coat.
- **Discounted dynamic programming.** Value iteration truncates at the effective horizon ln ε / ln γ — the amplitude horizon exactly.
- **Ruelle transfer operators.** Spectral gaps of composition operators for hyperbolic (uniformly contracting/expanding) maps govern decay of correlations; the bounce map R having a strong contraction is precisely what gives the resolvent a fast-converging expansion. This is the same operator family as the Holographic Koopman Transform work in this research program — the game is an HKT instance where the observable is a webcam and the dynamical system is a hall of mirrors.

## 6. The one sentence that might be new

Each item above is known in its own field. What I have not seen stated anywhere as a single principle is the **two-horizon decomposition**:

> *For any iterated operator that contracts both in amplitude (factor λ) and in the resolution-relevant metric of its data (factor m), the exact-to-observation truncation depth is min(ln ε/ln λ, ln(p/L)/ln m) — and when the process is designed so the spatial horizon binds, apparent infinite regress costs O(log resolution) applications, with cost decreasing as the regress is made visually stronger.*

Applied prescriptively, it is a design rule that transfers outside graphics: **when the goal is the appearance (or the observable consequences) of unbounded recursive structure, do not simulate the structure — implement one contraction and truncate at the observation horizon.** Candidates where the prescriptive form might do work:

- **Recurrent/iterative inference architectures:** choose the iteration map's contraction rate against the task's output resolution, not against a fixed depth budget; depth requirements then scale with log of required precision. (DEQ theory has the amplitude half; tying depth to *output resolution* via representation-space contraction is the less-developed half.)
- **Multiscale simulation:** any self-similar cascade (turbulence visualization, fracture, dendritic growth) whose inter-scale map is a contraction can be rendered/queried to instrument resolution with logarithmic depth — the scales below the horizon are provably unobservable, not merely neglected.
- **The perception speculation** (flagged as such): a visual system that composes learned boundary data under contracting recurrent maps would exhibit exactly this signature — a small, fixed number of recurrent iterations sufficing for percepts that feel unboundedly deep. Fixed ~100–150 ms recognition latency despite "infinite" scene complexity is at least consistent. This is a hypothesis-shaped remark, not a result.

## 7. Honest ledger

**Established, not ours:** rendering equation as operator equation (Kajiya 1986); Neumann series truncation; IFS/contraction attractors (Hutchinson 1981); Droste conformal analysis (de Smit & Lenstra 2003); Gordon metric / transformation optics (1923; Pendry, Leonhardt 2006); BEM; echo-state property (Jaeger); DEQ (2019); effective horizon in discounted DP; Ruelle transfer operators; cheap screen-space refraction fakes are standard game-dev practice and claim no novelty here.

**Ours, verified:** the code-level identification of inspiration.html's loop with a truncated Koopman resolvent (read directly from source); the empirical failure data — bulk-transport builds hitting compile explosion and TDR while the boundary-event build holds 60 fps — as a cost demonstration; the numerical estimate N_res ≈ 4 matching the shipped maxBnc = 4 that was chosen by eye before the analysis existed.

**Ours, plausible but unchecked against literature:** the two-horizon decomposition as a stated principle; "extravagance is thrift" as its corollary; the resolution-scaling prediction (Corollary 2). A literature pass (transfer-operator numerics, DEQ convergence, perceptual metrics in rendering) is required before claiming novelty in print. It may well exist piecewise; I have not seen it assembled.

**Speculation, clearly flagged:** the perception/predictive-coding paragraph in §6.

**Negative result, logged:** physically honest bulk refraction, combined with mirror recursion, is not just expensive — it competes with the recursion for the same ray budget and destroys the effect it was meant to enrich. Kept as a fourth mode where its rays terminate; correctly excluded from the recursive modes.
