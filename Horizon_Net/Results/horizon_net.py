"""
HORIZON NET -- certified anytime inference for a weight-tied contracting network.

The claim under test (the two-horizon principle made prescriptive):
  For an iteration map F with Lipschitz constant rho < 1, the Banach a
  posteriori bound  ||x* - x_n|| <= rho/(1-rho) * ||x_n - x_{n-1}||
  lets us STOP with a CERTIFICATE:
    - classification: stop when the top-logit margin exceeds what the
      remaining trajectory could possibly change  -> prediction provably
      equals the infinite-depth prediction.
    - regression at b-bit output resolution: stop when the bound falls
      below half a quantum -> quantized output provably final.
  Theorem to verify numerically: certified depth grows LINEARLY in bits
  demanded, slope = ln(2)/ln(1/rho).  (Resolution horizon law.)

No hype: fixed random contracting cell (reservoir), ridge readout.
Everything measured, certificate validated against ground-truth fixed points.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json

rng = np.random.default_rng(7)

# ---------------- data: K noisy prototype classes, per-sample difficulty ----
K, D_IN, D_H = 10, 32, 128
N_TR, N_TE = 4000, 2000
protos = rng.normal(size=(K, D_IN)); protos /= np.linalg.norm(protos, axis=1, keepdims=True)

def make(n):
    y = rng.integers(0, K, n)
    sig = rng.uniform(0.1, 0.9, n)               # per-sample noise = difficulty
    u = protos[y] + rng.normal(size=(n, D_IN)) * sig[:, None]
    return u.astype(np.float64), y, sig

Utr, ytr, str_ = make(N_TR)
Ute, yte, ste  = make(N_TE)

# ---------------- the cell: x <- tanh(W x + V u + b), spectral norm(W)=rho --
def build_cell(rho, seed=0):
    r = np.random.default_rng(seed)
    W = r.normal(size=(D_H, D_H))
    W *= rho / np.linalg.svd(W, compute_uv=False)[0]   # exact Lipschitz bound: |tanh'|<=1
    V = r.normal(size=(D_H, D_IN)) / np.sqrt(D_IN)
    b = r.normal(size=D_H) * 0.1
    return W, V, b

def iterate(W, V, b, U, n_steps):
    x = np.zeros((U.shape[0], D_H))
    drive = U @ V.T + b
    for _ in range(n_steps):
        x = np.tanh(x @ W.T + drive)
    return x

# ---------------- certified halting --------------------------------------
def certified_run(W, V, b, U, rho, C=None, r_vec=None, quantum=None,
                  max_steps=400):
    """Runs the iteration; per sample, records the first step at which the
    certificate fires. Returns halt depths, halted-state predictions."""
    n = U.shape[0]
    x_prev = np.zeros((n, D_H))
    drive = U @ V.T + b
    fac = rho / (1.0 - rho)
    halt = np.full(n, -1)
    frozen_pred = np.full(n, -1)
    frozen_val = np.zeros(n)
    x = x_prev
    for step in range(1, max_steps + 1):
        x = np.tanh(x_prev @ W.T + drive)
        d = np.linalg.norm(x - x_prev, axis=1)
        B = fac * d                                   # ||x* - x_step|| <= B
        active = halt < 0
        if C is not None:                             # classification certificate
            logits = x[active] @ C.T
            top = np.argmax(logits, axis=1)
            # pairwise: gap(i,j) > ||c_i - c_j|| * B  for all j != top
            cn = np.linalg.norm(C[None, :, :] - C[top][:, None, :], axis=2)  # (na,K)
            gaps = logits[np.arange(len(top)), top][:, None] - logits
            ok = np.all(gaps >= cn * B[active][:, None], axis=1)
            idx = np.where(active)[0][ok]
            halt[idx] = step
            frozen_pred[idx] = top[ok]
        else:                                         # regression certificate
            ok = (np.linalg.norm(r_vec) * B[active]) < quantum / 2
            idx = np.where(active)[0][ok]
            halt[idx] = step
            frozen_val[idx] = x[idx] @ r_vec
        x_prev = x
        if np.all(halt > 0):
            break
    # anything never certified: halt at max_steps
    left = halt < 0
    halt[left] = max_steps
    if C is not None:
        frozen_pred[left] = np.argmax(x[left] @ C.T, axis=1)
        return halt, frozen_pred, x
    else:
        frozen_val[left] = x[left] @ r_vec
        return halt, frozen_val, x

# ============================================================================
# PART 1: classification, rho = 0.8
# ============================================================================
RHO = 0.8
W, V, b = build_cell(RHO, seed=1)

X_tr = iterate(W, V, b, Utr, 120)                    # near-exact fixed points
Y1h = np.eye(K)[ytr]
lam = 1e-3
C = np.linalg.solve(X_tr.T @ X_tr + lam * np.eye(D_H), X_tr.T @ Y1h).T   # (K, D_H)

# ground truth at "infinite" depth
X_te_star = iterate(W, V, b, Ute, 400)
pred_star = np.argmax(X_te_star @ C.T, axis=1)
acc_star = (pred_star == yte).mean()

halt, pred_halt, _ = certified_run(W, V, b, Ute, RHO, C=C)
agree = (pred_halt == pred_star).mean()
acc_halt = (pred_halt == yte).mean()

print(f"[cls] fixed-depth-400 acc = {acc_star:.4f}")
print(f"[cls] certified-halt  acc = {acc_halt:.4f}   agreement with depth-400: {agree:.4f}")
print(f"[cls] depth: mean {halt.mean():.1f}  median {np.median(halt):.0f}  "
      f"p90 {np.percentile(halt,90):.0f}  max {halt.max()}")

# depth vs difficulty (noise sigma)
bins = np.linspace(0.1, 0.9, 7)
bi = np.digitize(ste, bins)
depth_by_sig = [halt[bi == i].mean() for i in range(1, 7)]

# ============================================================================
# PART 2: resolution-horizon law -- regression, depth vs bits demanded
# ============================================================================
w_true = rng.normal(size=D_IN); w_true /= np.linalg.norm(w_true)
ztr = Utr @ w_true
r_vec = np.linalg.solve(X_tr.T @ X_tr + lam * np.eye(D_H), X_tr.T @ ztr)

z_range = np.percentile(Ute @ w_true, 99) - np.percentile(Ute @ w_true, 1)
bits = np.arange(2, 15)
mean_depth_bits = []
for bcount in bits:
    q = z_range / (2 ** bcount)
    h, _, _ = certified_run(W, V, b, Ute[:500], RHO, r_vec=r_vec, quantum=q)
    mean_depth_bits.append(h.mean())
mean_depth_bits = np.array(mean_depth_bits)
slope_meas = np.polyfit(bits, mean_depth_bits, 1)[0]
slope_pred = np.log(2) / np.log(1 / RHO)

# empirical contraction rate: fit decay of ||x_n - x_{n-1}|| on test set
def fit_rho_eff(W, V, b, U, n_steps=40):
    x_prev = np.zeros((U.shape[0], D_H)); drive = U @ V.T + b
    ds = []
    x = x_prev
    for _ in range(n_steps):
        x_new = np.tanh(x @ W.T + drive)
        ds.append(np.linalg.norm(x_new - x, axis=1).mean())
        x = x_new
    ds = np.array(ds[3:])              # skip transient
    k = np.arange(len(ds))
    return float(np.exp(np.polyfit(k, np.log(ds + 1e-300), 1)[0]))

rho_eff = fit_rho_eff(W, V, b, Ute[:500])
slope_pred_eff = np.log(2) / np.log(1 / rho_eff)
print(f"[res-law] empirical contraction rho_eff = {rho_eff:.3f}; predicted slope with rho_eff = {slope_pred_eff:.3f} it/bit")

print(f"[res-law] measured slope {slope_meas:.3f} iters/bit | predicted ln2/ln(1/rho) = {slope_pred:.3f}")

# ============================================================================
# PART 3: extravagance-is-thrift sweep -- contraction strength vs depth & acc
# ============================================================================
rhos = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
sweep = []
for rho in rhos:
    Ws, Vs, bs = build_cell(rho, seed=1)
    Xtr_s = iterate(Ws, Vs, bs, Utr, 300)
    Cs = np.linalg.solve(Xtr_s.T @ Xtr_s + lam * np.eye(D_H), Xtr_s.T @ Y1h).T
    Xte_s = iterate(Ws, Vs, bs, Ute, 600)
    acc_s = (np.argmax(Xte_s @ Cs.T, axis=1) == yte).mean()
    h_s, p_s, _ = certified_run(Ws, Vs, bs, Ute, rho, C=Cs, max_steps=600)
    ag_s = (p_s == np.argmax(Xte_s @ Cs.T, axis=1)).mean()
    sweep.append((rho, h_s.mean(), acc_s, ag_s))
    print(f"[sweep] rho={rho:.2f}  mean certified depth={h_s.mean():6.1f}  acc={acc_s:.4f}  cert-agree={ag_s:.4f}")

# ============================================================================
# plots
# ============================================================================
fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))

ax[0].hist(halt, bins=40, color="#4477aa")
ax[0].set_title(f"certified halt depth (rho=0.8)\nacc {acc_halt:.3f} = full-depth acc {acc_star:.3f}, agreement {agree:.0%}")
ax[0].set_xlabel("iterations until certificate"); ax[0].set_ylabel("test samples")

ax[1].plot(bits, mean_depth_bits, "o-", color="#cc6677", label=f"measured ({slope_meas:.2f} it/bit)")
ax[1].plot(bits, mean_depth_bits[0] + slope_pred_eff * (bits - bits[0]), "--", color="k",
           label=f"theory, empirical ρ_eff={rho_eff:.2f}: {slope_pred_eff:.2f} it/bit")
ax[1].plot(bits, mean_depth_bits[0] + slope_pred * (bits - bits[0]), ":", color="gray",
           label=f"worst-case bound ρ={RHO}: {slope_pred:.2f} it/bit")
ax[1].set_title("resolution-horizon law")
ax[1].set_xlabel("output resolution demanded (bits)"); ax[1].set_ylabel("mean certified depth")
ax[1].legend()

rr = [s[0] for s in sweep]
ax[2].plot(rr, [s[1] for s in sweep], "o-", color="#228833", label="mean certified depth")
ax2b = ax[2].twinx()
ax2b.plot(rr, [s[2] for s in sweep], "s--", color="#aa3377", label="accuracy")
ax[2].set_xlabel("contraction rho (spectral norm)"); ax[2].set_ylabel("depth")
ax2b.set_ylabel("accuracy"); ax2b.set_ylim(0, 1)
ax[2].set_title("thrift vs capacity")
h1, l1 = ax[2].get_legend_handles_labels(); h2, l2 = ax2b.get_legend_handles_labels()
ax[2].legend(h1 + h2, l1 + l2, loc="center left")

plt.tight_layout()
plt.savefig("/home/claude/horizon_net_results.png", dpi=130)

json.dump({
    "acc_full_depth": float(acc_star), "acc_certified": float(acc_halt),
    "certificate_agreement": float(agree),
    "depth_mean": float(halt.mean()), "depth_median": float(np.median(halt)),
    "depth_p90": float(np.percentile(halt, 90)), "depth_max": int(halt.max()),
    "depth_by_noise_bin": [float(d) for d in depth_by_sig],
    "res_law_slope_measured": float(slope_meas), "res_law_slope_predicted_bound": float(slope_pred),
    "rho_eff": float(rho_eff), "res_law_slope_predicted_eff": float(slope_pred_eff),
    "rho_sweep": [{"rho": s[0], "mean_depth": float(s[1]), "acc": float(s[2]), "agree": float(s[3])} for s in sweep],
}, open("/home/claude/horizon_net_results.json", "w"), indent=1)
print("saved results + plot")
