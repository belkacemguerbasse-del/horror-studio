"""Visionneuse 3D autonome (HTML + three.js) du modèle généré.

La page embarque les maillages (positions et indices en base64) de chaque pièce,
en version complète et en demi-coupe, avec un panneau de cotes. Elle ne charge
que three.js depuis un CDN ; aucun serveur, aucun fichier externe.
"""

from __future__ import annotations

import base64
import json
import struct
from pathlib import Path

THREE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"
FONTS = "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap"


def _mesh_blob(shape, tolerance: float = 0.25, angular: float = 0.3) -> dict:
    verts, tris = shape.tessellate(tolerance, angular)
    pos = struct.pack(f"<{3 * len(verts)}f", *[c for v in verts for c in (v.x, v.y, v.z)])
    idx = struct.pack(f"<{3 * len(tris)}I", *[i for t in tris for i in t])
    return {"p": base64.b64encode(pos).decode("ascii"), "i": base64.b64encode(idx).decode("ascii"),
            "nv": len(verts), "nt": len(tris)}


def export_viewer(parts: dict, cut_shapes: list, dims, out_path: Path, title: str) -> Path:
    data = {
        "title": title,
        "parts": [
            {"name": name, "label": name.replace("_", " "), "color": rgb,
             "full": _mesh_blob(wp.val()), "cut": _mesh_blob(cut)}
            for (name, (wp, rgb)), cut in zip(parts.items(), cut_shapes)
        ],
        "dims": dims.to_dict(),
    }
    html = _TEMPLATE.replace("__TITLE__", title).replace("__THREE__", THREE_CDN).replace("__FONTS__", FONTS)
    html = html.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    out_path.write_text(html, encoding="utf-8")
    return out_path


_TEMPLATE = r"""<title>__TITLE__</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="__FONTS__">
<style>
/* Layout : visionneuse pleine largeur, panneau d'ingénierie à droite ; empilé sur téléphone. */
:root {
  --bg: #0f1419; --panel: #161c23; --fg: #e6e9ee; --muted: #9aa5b4; --line: #2a333f;
  --accent: #e0893a; --accent-fg: #1a1208; --chip: #1f2730;
  --font-ui: "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
  --font-data: "IBM Plex Mono", "SFMono-Regular", Menlo, Consolas, monospace;
  color-scheme: dark;
}
@media (prefers-color-scheme: light) {
  :root:not([data-theme="dark"]) {
    --bg: #eef1f4; --panel: #ffffff; --fg: #1b2129; --muted: #5b6673; --line: #d5dbe3;
    --accent: #b8621c; --accent-fg: #ffffff; --chip: #f1f4f7; color-scheme: light;
  }
}
:root[data-theme="light"] {
  --bg: #eef1f4; --panel: #ffffff; --fg: #1b2129; --muted: #5b6673; --line: #d5dbe3;
  --accent: #b8621c; --accent-fg: #ffffff; --chip: #f1f4f7; color-scheme: light;
}
html, body { height: 100%; }
body { margin: 0; background: var(--bg); color: var(--fg); font-family: var(--font-ui); font-size: 14px; line-height: 1.45; }
.app { display: grid; grid-template-columns: 1fr minmax(280px, 360px); grid-template-rows: auto 1fr; height: 100%; }
header { grid-column: 1 / -1; display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 18px;
  padding-block: 12px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  border-bottom: 1px solid var(--line); background: var(--panel); }
header h1 { font-size: 17px; font-weight: 600; margin: 0; text-wrap: balance; }
header .sub { color: var(--muted); font-family: var(--font-data); font-size: 12.5px; }
.stage { position: relative; min-width: 0; min-height: 320px; padding-left: env(safe-area-inset-left, 0px); }
canvas { display: block; width: 100%; height: 100%; touch-action: none; outline: none; }
.hint { position: absolute; left: max(16px, env(safe-area-inset-left, 0px)); bottom: 12px; color: var(--muted); font-size: 12px; pointer-events: none; }
.controls { position: absolute; top: 12px; left: max(16px, env(safe-area-inset-left, 0px)); display: flex; flex-wrap: wrap; gap: 8px; }
button { font: inherit; font-weight: 500; padding: 6px 12px; border-radius: 6px; border: 1px solid var(--line);
  background: var(--panel); color: var(--fg); cursor: pointer; }
button[aria-pressed="true"] { background: var(--accent); color: var(--accent-fg); border-color: var(--accent); }
button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
aside { min-width: 0; overflow-y: auto; border-left: 1px solid var(--line); background: var(--panel);
  padding-block: 14px 24px; padding-left: 16px; padding-right: max(16px, env(safe-area-inset-right, 0px)); }
aside h2 { font-size: 11.5px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin: 18px 0 8px; font-weight: 600; }
aside h2:first-child { margin-top: 0; }
.parts { display: grid; gap: 4px; }
.parts label { display: flex; align-items: center; gap: 10px; padding: 5px 8px; border-radius: 6px; cursor: pointer; }
.parts label:hover { background: var(--chip); }
.parts input { accent-color: var(--accent); margin: 0; }
.swatch { width: 12px; height: 12px; border-radius: 3px; border: 1px solid rgba(0,0,0,.25); flex: none; }
table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
td { padding: 4px 0; border-bottom: 1px solid var(--line); vertical-align: baseline; }
td:last-child { text-align: right; font-family: var(--font-data); font-size: 13px; white-space: nowrap; }
p.note { color: var(--muted); font-size: 12.5px; margin: 8px 0 0; }
@media (max-width: 760px) {
  .app { grid-template-columns: 1fr; grid-template-rows: auto minmax(300px, 56vh) 1fr; }
  aside { border-left: 0; border-top: 1px solid var(--line); padding-left: max(16px, env(safe-area-inset-left, 0px)); }
}
@media (prefers-reduced-motion: reduce) { .spin { display: none; } }
</style>

<div class="app">
  <header>
    <h1>__TITLE__</h1>
    <span class="sub" id="subtitle"></span>
  </header>
  <div class="stage">
    <canvas id="c" tabindex="0" aria-label="Modèle 3D du moteur"></canvas>
    <div class="controls">
      <button id="btn-cut" aria-pressed="false">Coupe</button>
      <button id="btn-spin" class="spin" aria-pressed="true">Rotation</button>
      <button id="btn-reset">Recentrer</button>
    </div>
    <div class="hint">Glisser pour tourner, molette ou pincement pour zoomer</div>
  </div>
  <aside>
    <h2>Pièces</h2>
    <div class="parts" id="parts"></div>
    <h2>Cotes principales</h2>
    <table id="dims"></table>
    <h2>Point de fonctionnement (point fixe, ISA)</h2>
    <table id="perf"></table>
    <p class="note">Modèle d'implantation généré à partir du cycle thermodynamique : enveloppes, sections,
      positions et nombres d'aubes sont dimensionnés ; les aubes sont des plaques simplifiées, pas des
      profils aérodynamiques. Fichiers STEP et STL fournis séparément.</p>
  </aside>
</div>

<script src="__THREE__"></script>
<script>
(function () {
  var DATA = __DATA__;
  var dims = DATA.dims;
  function fmt(v, d) { return Number(v).toLocaleString('fr-FR', { maximumFractionDigits: d, minimumFractionDigits: d }); }
  document.getElementById('subtitle').textContent =
    'Ø ' + fmt(dims.casing_diameter, 0) + ' mm · L ' + fmt(dims.overall_length, 0) + ' mm · ' +
    fmt(dims.thrust_N, 0) + ' N · ' + fmt(dims.mass_flow_kg_s, 2) + ' kg/s';

  var rows = [
    ['Diamètre du carter', fmt(dims.casing_diameter, 1) + ' mm'],
    ['Longueur hors tout', fmt(dims.overall_length, 0) + ' mm'],
    ['Diamètre d’entrée d’air', fmt(dims.inlet_diameter, 1) + ' mm'],
    ['Diamètre du rouet compresseur', fmt(dims.compressor_tip_diameter, 1) + ' mm'],
    ['Diamètre de la roue de turbine', fmt(dims.turbine_tip_diameter, 1) + ' mm'],
    ['Diamètre de sortie tuyère', fmt(dims.nozzle_exit_diameter, 1) + ' mm'],
    ['Section de sortie', fmt(dims.exit_area_cm2, 1) + ' cm²'],
    ['Diamètre d’arbre', fmt(dims.shaft_diameter, 1) + ' mm'],
    ['Aubes rouet / diffuseur', dims.compressor_blades + ' / ' + dims.diffuser_vanes],
    ['Aubes distributeur / turbine', dims.ngv_count + ' / ' + dims.turbine_blades],
    ['Tubes vaporisateurs', String(dims.vaporizer_tubes)]
  ];
  var perf = [
    ['Poussée', fmt(dims.thrust_N, 0) + ' N'],
    ['Débit d’air', fmt(dims.mass_flow_kg_s, 3) + ' kg/s'],
    ['Débit carburant', fmt(dims.fuel_flow_kg_s * 60000, 0) + ' g/min'],
    ['TSFC', fmt(dims.tsfc_kg_per_N_h, 3) + ' kg/(N·h)'],
    ['Vitesse d’éjection', fmt(dims.exhaust_velocity_m_s, 0) + ' m/s'],
    ['Température des gaz en sortie', fmt(dims.exhaust_temp_K - 273.15, 0) + ' °C']
  ];
  function fill(id, arr) {
    var t = document.getElementById(id);
    arr.forEach(function (r) {
      var tr = document.createElement('tr');
      var a = document.createElement('td'); a.textContent = r[0];
      var b = document.createElement('td'); b.textContent = r[1];
      tr.appendChild(a); tr.appendChild(b); t.appendChild(tr);
    });
  }
  fill('dims', rows); fill('perf', perf);

  function decode(blob) {
    var bp = atob(blob.p), bi = atob(blob.i);
    var pos = new Float32Array(blob.nv * 3), idx = new Uint32Array(blob.nt * 3);
    var u8p = new Uint8Array(pos.buffer), u8i = new Uint8Array(idx.buffer);
    for (var k = 0; k < u8p.length; k++) u8p[k] = bp.charCodeAt(k);
    for (var m = 0; m < u8i.length; m++) u8i[m] = bi.charCodeAt(m);
    var g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setIndex(new THREE.BufferAttribute(idx, 1));
    g.computeVertexNormals();
    return g;
  }

  var canvas = document.getElementById('c');
  var renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(38, 1, 1, 5000);
  scene.add(new THREE.HemisphereLight(0xdde6f0, 0x2a2420, 0.9));
  var key = new THREE.DirectionalLight(0xffffff, 0.9); key.position.set(1, 1.2, 1.6); scene.add(key);
  var fill2 = new THREE.DirectionalLight(0xffe2c2, 0.35); fill2.position.set(-1.5, -0.6, -1); scene.add(fill2);

  var root = new THREE.Group(); scene.add(root);
  var meshes = [];
  DATA.parts.forEach(function (p) {
    var col = new THREE.Color(p.color[0], p.color[1], p.color[2]);
    var mat = new THREE.MeshStandardMaterial({ color: col, metalness: 0.35, roughness: 0.55, side: THREE.DoubleSide });
    var full = new THREE.Mesh(decode(p.full), mat);
    var cut = new THREE.Mesh(decode(p.cut), mat);
    cut.visible = false;
    root.add(full); root.add(cut);
    meshes.push({ part: p, full: full, cut: cut, on: true });
  });

  // Centre et cadrage
  var box = new THREE.Box3().setFromObject(root);
  var center = box.getCenter(new THREE.Vector3());
  var size = box.getSize(new THREE.Vector3());
  var radius = Math.max(size.x, size.y, size.z) * 0.62;
  var target = center.clone();
  var sph = { theta: -0.95, phi: 1.15, r: radius * 2.9 };
  var home = { theta: sph.theta, phi: sph.phi, r: sph.r };
  function updateCamera() {
    var sp = Math.sin(sph.phi);
    camera.position.set(target.x + sph.r * sp * Math.cos(sph.theta),
                        target.y + sph.r * Math.cos(sph.phi),
                        target.z + sph.r * sp * Math.sin(sph.theta));
    camera.lookAt(target);
  }

  var spinning = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var cutMode = false;
  function applyVisibility() {
    meshes.forEach(function (m) { m.full.visible = m.on && !cutMode; m.cut.visible = m.on && cutMode; });
  }
  var list = document.getElementById('parts');
  meshes.forEach(function (m, i) {
    var lab = document.createElement('label');
    var cb = document.createElement('input'); cb.type = 'checkbox'; cb.checked = true; cb.id = 'part-' + i;
    cb.addEventListener('change', function () { m.on = cb.checked; applyVisibility(); });
    var sw = document.createElement('span'); sw.className = 'swatch';
    sw.style.background = '#' + new THREE.Color(m.part.color[0], m.part.color[1], m.part.color[2]).getHexString();
    var tx = document.createElement('span'); tx.textContent = m.part.label;
    lab.appendChild(cb); lab.appendChild(sw); lab.appendChild(tx); list.appendChild(lab);
  });

  var btnCut = document.getElementById('btn-cut'), btnSpin = document.getElementById('btn-spin');
  btnCut.addEventListener('click', function () { cutMode = !cutMode; btnCut.setAttribute('aria-pressed', String(cutMode)); applyVisibility(); });
  btnSpin.setAttribute('aria-pressed', String(spinning));
  btnSpin.addEventListener('click', function () { spinning = !spinning; btnSpin.setAttribute('aria-pressed', String(spinning)); });
  document.getElementById('btn-reset').addEventListener('click', function () { sph.theta = home.theta; sph.phi = home.phi; sph.r = home.r; updateCamera(); });

  // Orbite : un pointeur tourne, deux pincent, la molette zoome
  var pointers = {}, lastDist = 0;
  canvas.addEventListener('pointerdown', function (e) { canvas.setPointerCapture(e.pointerId); pointers[e.pointerId] = { x: e.clientX, y: e.clientY }; spinning = false; btnSpin.setAttribute('aria-pressed', 'false'); });
  canvas.addEventListener('pointermove', function (e) {
    if (!pointers[e.pointerId]) return;
    var ids = Object.keys(pointers);
    if (ids.length === 1) {
      var dx = e.clientX - pointers[e.pointerId].x, dy = e.clientY - pointers[e.pointerId].y;
      sph.theta -= dx * 0.008; sph.phi = Math.min(3.0, Math.max(0.15, sph.phi - dy * 0.008)); updateCamera();
    }
    pointers[e.pointerId] = { x: e.clientX, y: e.clientY };
    if (ids.length === 2) {
      var a = pointers[ids[0]], b = pointers[ids[1]];
      var d = Math.hypot(a.x - b.x, a.y - b.y);
      if (lastDist) { sph.r = Math.min(radius * 8, Math.max(radius * 0.8, sph.r * lastDist / d)); updateCamera(); }
      lastDist = d;
    }
  });
  function up(e) { delete pointers[e.pointerId]; lastDist = 0; }
  canvas.addEventListener('pointerup', up); canvas.addEventListener('pointercancel', up);
  canvas.addEventListener('wheel', function (e) { e.preventDefault(); sph.r = Math.min(radius * 8, Math.max(radius * 0.8, sph.r * (1 + e.deltaY * 0.0012))); updateCamera(); }, { passive: false });

  function resize() {
    var w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', resize);
  var last = performance.now();
  function frame(now) {
    var dt = (now - last) / 1000; last = now;
    if (spinning) { sph.theta += dt * 0.35; updateCamera(); }
    resize();
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }
  applyVisibility(); updateCamera(); resize();
  requestAnimationFrame(frame);
})();
</script>
"""
