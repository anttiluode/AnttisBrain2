# ANTTI'S BRAIN — DESCENT

It is at huggingface: 

https://huggingface.co/spaces/Aluode/AnttisBrain

At huggingface there is 10 songs from suno. (Instrumental chill)

Its also here: 

https://anttiluode.github.io/AnttisBrain2/ (Without soundtrack). 

To play it locally you can just copy the files from huggingface: 

https://huggingface.co/spaces/Aluode/AnttisBrain/tree/main 

Or make soundtrack of your own. The sound files are game1.mp3 to game10.mp3. 

An infinite procedural key-hunt built on the Antti's Brain 2 engine (WebGL2 raymarcher,
hash-dreamed chambers, refracting crystal moons, webcam boundary). One HTML file, no
dependencies, no build step. No enemies, no timers, no hand-made levels — only geometry,
depth, and the hash.

> Do not hype. Do not lie. Just show.

## The game

- The brain is an endless chain of chambers, a pure function of `(SEED, room index)`.
- **A level is a run of rooms**: level 1 is 4 rooms, level 2 is 5, … capped at 10 per level.
- Somewhere in the level, **one crystal is the key**: it is gold and it pulses. Touch it.
- The corridor after the level's last room is closed by a **red seal** — a glowing
  membrane you cannot pass. Touch the key and the seal dissolves. Walk through: next level.
- The **resonance meter** in the HUD is your only guide: it tells you how many rooms away
  the key is, and once you're in the right room it runs hot with live distance. Hot / cold,
  nothing more.

There is no way to lose. There is only further down.

## What deepens with the level

Everything below is still deterministic — same seed, same descent.

| property | how it grows |
|---|---|
| level length | 4 rooms → 10 rooms (cap) |
| shape pool | 6 shapes at level 1, +1 new shape per level, 12 total by level 7 |
| **twist** | rooms shear around their vertical axis, stronger with depth |
| ripple | from level 3, walls start to breathe with a triple-sine displacement |
| **mass** | each room has its own mass factor (shown in HUD); moons grow heavier, lensing pulls harder |
| moons per room | 3 → 5 |

The twelve chamber shapes, in unlock order:

1. cube · 2. sphere · 3. hex prism · 4. star (5–7 points) · 5. octahedron · 6. cylinder —
the classics —
then 7. **capsule vault** · 8. **cut crystal** (box ∩ octahedron) · 9. **ellipsoid dome** ·
10. **cross cathedral** · 11. **gear** (cog-rippled cylinder) · 12. **wheel** (walkable
torus + hub + four spokes).

The moons wear their room's shape, rounded into optical glass, so new room shapes mean
new crystal shapes too. Twist applies on top of any shape, so a twisted star at level 6
and a twisted gear at level 9 are genuinely different rooms even with the same base index
math.

## Controls

- **W A S D** — move · **Q / E** — down / up · **Shift** — boost
- **drag** — look (horizontal inverted, as tradition demands)
- Modes: **Boundary** (walls are your camera) / **Projection** (moons carry the image) /
  **Cascade** (heavy refracting glass)
- Sliders: mass gain, lensing strength, music volume
- **Music: on/off** — toggles the soundtrack
- **New brain** — fresh seed, back to level 1

## Music

Put `game1.mp3` … `game10.mp3` next to the HTML file. They play as an endless
playlist: a random track starts on your first click (browsers require a gesture
before audio), then they chain forever — when one ends the next begins, wrapping
around after `game10.mp3`. Missing files are skipped automatically; if none of
the ten are found the HUD says `no mp3s found` and the game plays silent.
Volume slider in the control panel; the Music button pauses/resumes.

## Save / load

The entire game state is six numbers: `{version, seed, level, room index, key flag,
max level reached}`. Everything else is re-dreamed from the hash on load, including the
key's location and the walk direction of the chain (reconstructed by replaying the turn
angles — verified bit-exact).

- **Save** — writes to localStorage (when the browser allows it) and keeps a code ready.
- **Save code** — prints the save as a short base64 string and copies it to the clipboard.
  This works everywhere, including `file://` pages and sandboxes where localStorage is
  blocked. Paste it into a text file, an email, a commit message.
- **Load** — reads the local save, or accepts a pasted code.
- The game **autosaves** on every level-up and key pickup, and silently resumes on launch
  if a local save exists.

Walking backward is always allowed. Levels you have already beaten stay open (the game
remembers your max level, so re-crossing an old seal never re-locks it), but the current
level's key must be found each fresh descent into new territory.

## How the infinity works

Same principle as Brain 2, extended:

- `rng(index, salt)` — an integer hash (multiply/xor/shift mix of `SEED`, index, salt).
  Any room at any depth can be queried in O(1) without generating the rooms before it.
- `roomDef(i)` now first computes which level room `i` belongs to (cumulative level
  depths are a closed-form loop), then draws shape / size / twist / ripple / mass / turn /
  name from independent salts, with the level scaling the ranges.
- Per level, a second hash stream `rngL(level, salt)` places the key room. The key is
  always moon 0 of that room, so it can never be hidden by settings.
- Only 3 rooms exist at a time (prev / current / next). The seal is a single sphere SDF
  in the exit corridor, present only while the key is unfound and you are in the exit room —
  blocked in the JS collision twin and rendered as a pulsing membrane in the shader.

## Technical notes

- Single fragment shader, one fullscreen triangle, raymarched SDFs with real Snell
  refraction + total internal reflection through the moons and Beer–Lambert tinting.
- Rooms and moons share one 12-way shape function; moons are derived from it via
  const scale/rounding tables, which roughly halves the shader the driver must
  compile. Well loops use dynamic bounds so ANGLE doesn't unroll them 15-wide.
- Shader compilation is deferred until after first paint and uses
  KHR_parallel_shader_compile when available, with a shimmer bar and elapsed
  timer on the boot screen. Loop bounds (march steps, glass-refraction steps,
  wall-escape steps) are uniforms, which blocks driver loop unrolling — the
  main cause of minutes-long first compiles on Windows.
- The wheel room's four spokes fold to two by symmetry (|x|,|z|), an exact
  identity that trims the hottest SDF.
- The key crystal orbits wide (up to ~0.34 × room size off the center line) with a
  tight pickup radius, so finding the key room via resonance is only half the hunt.
- Twist and ripple are applied as domain modifications with a Lipschitz correction
  factor on the returned distance, so marching stays conservative and never tunnels.
- Every SDF has a JavaScript twin used for collision and gate transitions; the twelve
  room shapes were tested to guarantee the room center is deep interior (transition
  trigger fires at −1.0), so no shape can ever strand you in a wall.
- Webcam feeds the boundary texture; falls back to an animated test pattern.
- WebGL2 required.

## Running

Open `anttis-brain-descent.html` in any WebGL2 browser, with the mp3s in the
same folder. Allow the camera if you want the walls to be you; decline and the
pattern takes over.

## First launch and the "dreaming the shader" bar

The boot screen reports its state. `dreaming the shader…` means the GPU driver
is compiling; an amber shimmer bar and a live seconds counter run while it does
(compile progress isn't queryable from WebGL, so the counter is honest elapsed
time rather than a fake percentage). This happens on the FIRST launch only —
the driver caches the compiled shader on disk, so later launches are near
instant.

It should now be fast even the first time: all raymarch loop bounds are passed
as uniforms, so the D3D/ANGLE compiler cannot unroll the 180-step march and is
forced to compile the loop body once instead of 180 times. That, not the shape
count, was the compile-time bomb — all twelve chamber shapes stay.

`ready — click to enter` means go. Any JavaScript or shader error paints itself
on the boot screen in red with the actual message — send that text and it can
be fixed.
