/* ═══════════════════════════════════════════════════════════════
   PHICAN WebApp — Silueta interactiva del vehículo (Canvas)
   Migrado de formulario.py (tkinter) a HTML5 Canvas
   ═══════════════════════════════════════════════════════════════ */

// ── Configuración de siluetas ───────────────────────────────────
const SIL_DIMS = {
  turismo:   { bx: [0.050, 0.950], wx: [0.220, 0.780] },
  suv:       { bx: [0.045, 0.955], wx: [0.215, 0.785] },
  mono:      { bx: [0.040, 0.960], wx: [0.200, 0.800] },
  minibus:   { bx: [0.040, 0.960], wx: [0.180, 0.820] },
  autobus:   { bx: [0.025, 0.975], wx: [0.160, 0.500, 0.840] },
  furgoneta: { bx: [0.038, 0.958], wx: [0.190, 0.790] },
  camion:    { bx: [0.030, 0.968], wx: [0.175, 0.740, 0.850] },
  moto:      { bx: [0.240, 0.760], wx: [0.270, 0.730] },
};

const SIL_SEAT_ROWS = {
  turismo:   { 1: [0.500],        2: [0.320, 0.620],        3: [0.280, 0.500, 0.700] },
  suv:       { 1: [0.500],        2: [0.310, 0.630],        3: [0.270, 0.500, 0.710] },
  mono:      { 1: [0.370],        2: [0.300, 0.580],        3: [0.260, 0.480, 0.680] },
  minibus:   { 1: [0.300],        2: [0.300, 0.620],        3: [0.220, 0.460, 0.620] },
  autobus:   { 1: [0.310],        2: [0.310, 0.710],        3: [0.220, 0.460, 0.710] },
  furgoneta: { 1: [0.200],        2: [0.200, 0.650],        3: [0.180, 0.500, 0.750] },
  camion:    { 1: [0.175],        2: [0.155, 0.240],        3: [0.140, 0.195, 0.250] },
  moto:      { 1: [0.500],        2: [0.420, 0.580],        3: [0.380, 0.500, 0.620] },
};

const COL = {
  body_fill:   "#d6e4f7",
  body_out:    "#1565c0",
  wheel_fill:  "#37474f",
  wheel_out:   "#263238",
  win_fill:    "#90caf9",
  win_out:     "#1565c0",
  seat_fill:   "#ff8f00",
  road:        "#bdbdbd",
  ground:      "#e0e0e0",
  shadow:      "#cfd8dc",
  truck_box:   "#b0bec5",
  truck_cabin: "#d6e4f7",
};

// ── Estado global ───────────────────────────────────────────────
let silTipo = "turismo";
let silFilas = 2;
let silRowXnorm = [];  // posiciones normalizadas [0-1] de cada fila
let silDragIdx = -1;
let silBalR1 = 0, silBalR2 = 0;

// ── Inicialización ──────────────────────────────────────────────
function initSilueta() {
  const canvas = document.getElementById("sil-canvas");
  const rowCanvas = document.getElementById("sil-row-canvas");

  // Botones de tipo
  document.querySelectorAll(".sil-type-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".sil-type-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      silTipo = btn.dataset.sil;
      resetRowPositions();
      buildAsientosInputs();
      drawAll();
    });
  });

  // Drag en row canvas (mouse)
  rowCanvas.addEventListener("mousedown", silDragStart);
  rowCanvas.addEventListener("mousemove", silDragMove);
  rowCanvas.addEventListener("mouseup", silDragEnd);
  rowCanvas.addEventListener("mouseleave", silDragEnd);

  // Touch events (movil/tablet)
  rowCanvas.addEventListener("touchstart", e => { e.preventDefault(); silDragStart(e.touches[0]); }, {passive: false});
  rowCanvas.addEventListener("touchmove", e => { e.preventDefault(); silDragMove(e.touches[0]); }, {passive: false});
  rowCanvas.addEventListener("touchend", silDragEnd);

  // Responsive: resize canvas al cambiar tamano ventana
  resizeCanvases();
  let resizeTimer;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => { resizeCanvases(); drawAll(); }, 150);
  });

  resetRowPositions();
  drawAll();
}

function resizeCanvases() {
  const container = document.getElementById("sil-canvas")?.parentElement;
  if (!container) return;

  const maxW = container.clientWidth - 4; // -4 para borders
  const targetW = Math.min(560, maxW);
  const scale = targetW / 560;

  ["sil-canvas", "sil-row-canvas", "sil-dim-canvas"].forEach(id => {
    const c = document.getElementById(id);
    if (!c) return;
    const baseH = id === "sil-canvas" ? 210 : (id === "sil-row-canvas" ? 52 : 82);
    c.width = targetW;
    c.height = Math.round(baseH * scale);
    c.style.width = targetW + "px";
    c.style.height = Math.round(baseH * scale) + "px";
  });
}

function setFilas(n) {
  silFilas = n;
  document.querySelectorAll(".btn-group .btn").forEach((btn, i) => {
    btn.classList.toggle("active", i + 1 === n);
  });
  resetRowPositions();
  buildAsientosInputs();
  drawAll();
}

function resetRowPositions() {
  const rows = SIL_SEAT_ROWS[silTipo] || {};
  silRowXnorm = (rows[silFilas] || [0.5]).slice();
}

// ── Dibujo principal ────────────────────────────────────────────
function drawAll() {
  drawSilueta();
  drawRowBars();
  drawDimensiones();
  recalcularBalance();
}

function drawSilueta() {
  const canvas = document.getElementById("sil-canvas");
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  // Suelo
  const roadY = H * 0.88;
  ctx.fillStyle = COL.ground;
  ctx.fillRect(0, roadY, W, H - roadY);
  ctx.strokeStyle = COL.road;
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(0, roadY); ctx.lineTo(W, roadY); ctx.stroke();

  // Sombra
  const dims = SIL_DIMS[silTipo];
  const bx0 = dims.bx[0] * W, bx1 = dims.bx[1] * W;
  ctx.fillStyle = COL.shadow;
  ctx.beginPath();
  ctx.ellipse((bx0 + bx1) / 2, roadY + 2, (bx1 - bx0) / 2.1, 5, 0, 0, Math.PI * 2);
  ctx.fill();

  // Intentar dibujar SVG vectorial; si no existe, usar dibujo manual
  const svgDrawn = drawSvgVehicle(ctx, W, H, roadY, silTipo);
  if (!svgDrawn) {
    const drawFn = SIL_DRAW[silTipo] || SIL_DRAW.turismo;
    drawFn(ctx, W, H, roadY);
  }

  // Dibujar filas de asientos
  for (let i = 0; i < silFilas; i++) {
    const x = silRowXnorm[i] * W;
    drawSeat(ctx, x, roadY - H * 0.32, 12, 22);
  }
}

function drawSeat(ctx, cx, top, w, h) {
  ctx.fillStyle = COL.seat_fill;
  ctx.strokeStyle = "#e65100";
  ctx.lineWidth = 1.5;
  // Respaldo
  const rx = cx - w / 2, ry = top;
  ctx.beginPath();
  ctx.roundRect(rx, ry, w, h * 0.65, 2);
  ctx.fill(); ctx.stroke();
  // Asiento
  ctx.beginPath();
  ctx.roundRect(rx - 2, ry + h * 0.65, w + 4, h * 0.35, 2);
  ctx.fill(); ctx.stroke();
}

function drawWheel(ctx, cx, cy, r) {
  // Neumático (exterior)
  ctx.fillStyle = "#263238";
  ctx.strokeStyle = "#1a1a1a";
  ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  // Banda de rodadura
  ctx.strokeStyle = "#37474f";
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.arc(cx, cy, r * 0.88, 0, Math.PI * 2); ctx.stroke();
  // Llanta
  const grad = ctx.createRadialGradient(cx - r * 0.15, cy - r * 0.15, 0, cx, cy, r * 0.65);
  grad.addColorStop(0, "#cfd8dc");
  grad.addColorStop(0.5, "#90a4ae");
  grad.addColorStop(1, "#607d8b");
  ctx.fillStyle = grad;
  ctx.beginPath(); ctx.arc(cx, cy, r * 0.65, 0, Math.PI * 2); ctx.fill();
  // Radios de la llanta
  ctx.strokeStyle = "#78909c"; ctx.lineWidth = 2;
  for (let a = 0; a < 5; a++) {
    const ang = a * Math.PI * 2 / 5 - Math.PI / 2;
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(ang) * r * 0.18, cy + Math.sin(ang) * r * 0.18);
    ctx.lineTo(cx + Math.cos(ang) * r * 0.55, cy + Math.sin(ang) * r * 0.55);
    ctx.stroke();
  }
  // Centro (tuerca)
  ctx.fillStyle = "#b0bec5";
  ctx.beginPath(); ctx.arc(cx, cy, r * 0.15, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = "#90a4ae"; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.arc(cx, cy, r * 0.15, 0, Math.PI * 2); ctx.stroke();
}

// ── SVG Path data (Font Awesome 6 — CC BY 4.0) ────────────────
// Usamos Path2D para renderizar siluetas vectoriales nítidas
// Ya no usamos SVG_VEHICLES - todo se dibuja con SIL_DRAW (delantera a IZQUIERDA)
function drawSvgVehicle() { return false; }

// ── Helpers de dibujo ───────────────────────────────────────────
function _headlight(ctx, x, y, w, h, front) {
  const grad = ctx.createLinearGradient(x, y, x + w, y);
  if (front) { grad.addColorStop(0, "#fff9c4"); grad.addColorStop(1, "#ffee58"); }
  else       { grad.addColorStop(0, "#ef5350"); grad.addColorStop(1, "#e53935"); }
  ctx.fillStyle = grad;
  ctx.strokeStyle = front ? "#f9a825" : "#c62828";
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.roundRect(x, y, w, h, 2); ctx.fill(); ctx.stroke();
}

function _mirror(ctx, x, y, left) {
  ctx.fillStyle = "#78909c";
  ctx.strokeStyle = "#455a64";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.ellipse(x, y, 5, 3, 0, 0, Math.PI * 2);
  ctx.fill(); ctx.stroke();
  // Brazo del retrovisor apunta hacia la izquierda (delantera)
  const dir = left ? -1 : 1;
  ctx.beginPath();
  ctx.moveTo(x + dir * 3, y); ctx.lineTo(x + dir * 8, y + 2); ctx.lineTo(x + dir * 8, y - 2);
  ctx.closePath(); ctx.fill();
}

function _doorLine(ctx, x, yTop, yBot) {
  ctx.strokeStyle = "#90a4ae";
  ctx.lineWidth = 1;
  ctx.setLineDash([]);
  ctx.beginPath(); ctx.moveTo(x, yTop); ctx.lineTo(x, yBot); ctx.stroke();
}

function _bumper(ctx, x1, x2, y, h) {
  ctx.fillStyle = "#78909c";
  ctx.strokeStyle = "#546e7a";
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.roundRect(x1, y, x2 - x1, h, 2); ctx.fill(); ctx.stroke();
}

function _wheelArch(ctx, cx, y, r, color) {
  ctx.fillStyle = color || "#b0bec5";
  ctx.beginPath();
  ctx.arc(cx, y, r + 4, Math.PI, 0);
  ctx.fill();
}

// ═══════════════════════════════════════════════════════════════════
// ── Funciones de dibujo por tipo (DELANTERA A LA IZQUIERDA) ─────
// ═══════════════════════════════════════════════════════════════════
const SIL_DRAW = {
  turismo(ctx, W, H, roadY) {
    const wheelR = H * 0.11;
    const wheelY = roadY - wheelR;
    const dims = SIL_DIMS.turismo;
    const wx = dims.wx.map(x => x * W);
    const bx = dims.bx.map(x => x * W);

    const bodyBot = roadY - wheelR * 0.7;
    const bodyTop = H * 0.44, roofTop = H * 0.16;

    wx.forEach(x => _wheelArch(ctx, x, roadY, wheelR, "#b0bec5"));

    // Faldón inferior
    ctx.fillStyle = "#b0bec5";
    ctx.beginPath();
    ctx.moveTo(bx[0], bodyBot + 4); ctx.lineTo(bx[1], bodyBot + 4);
    ctx.lineTo(bx[1], bodyBot + 8); ctx.lineTo(bx[0], bodyBot + 8);
    ctx.closePath(); ctx.fill();

    // Carrocería — delantera IZQUIERDA
    ctx.fillStyle = COL.body_fill; ctx.strokeStyle = COL.body_out; ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(bx[1], bodyBot);
    ctx.lineTo(bx[1], bodyTop + 5);
    ctx.quadraticCurveTo(bx[1], bodyTop, bx[1] - W * 0.04, bodyTop);
    // Maletero (derecha)
    ctx.lineTo(W * 0.82, bodyTop);
    // Pilar C + luneta trasera
    ctx.quadraticCurveTo(W * 0.78, bodyTop, W * 0.735, roofTop + 4);
    ctx.quadraticCurveTo(W * 0.72, roofTop, W * 0.68, roofTop);
    // Techo
    ctx.lineTo(W * 0.34, roofTop);
    // Pilar A + parabrisas (izquierda = delantera)
    ctx.quadraticCurveTo(W * 0.30, roofTop, W * 0.28, roofTop + 4);
    ctx.quadraticCurveTo(W * 0.22, bodyTop, W * 0.18, bodyTop);
    // Capó (izquierda)
    ctx.lineTo(bx[0] + W * 0.04, bodyTop);
    ctx.quadraticCurveTo(bx[0], bodyTop, bx[0], bodyTop + 5);
    ctx.lineTo(bx[0], bodyBot);
    ctx.closePath();
    ctx.fill(); ctx.stroke();

    // Línea de cintura
    ctx.strokeStyle = "#90a4ae"; ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(bx[0] + 5, bodyTop + (bodyBot - bodyTop) * 0.35);
    ctx.lineTo(bx[1] - 5, bodyTop + (bodyBot - bodyTop) * 0.35);
    ctx.stroke();

    // Puertas
    _doorLine(ctx, W * 0.43, roofTop + 3, bodyBot);
    _doorLine(ctx, W * 0.56, roofTop + 3, bodyBot);

    // Ventanas
    ctx.fillStyle = COL.win_fill; ctx.strokeStyle = COL.win_out; ctx.lineWidth = 1.5;
    // Delantera (izquierda)
    ctx.beginPath();
    ctx.moveTo(W * 0.42, bodyTop - 1);
    ctx.lineTo(W * 0.42, roofTop + 6);
    ctx.lineTo(W * 0.30, roofTop + 6);
    ctx.quadraticCurveTo(W * 0.24, bodyTop - 1, W * 0.20, bodyTop - 1);
    ctx.closePath(); ctx.fill(); ctx.stroke();
    // Central
    ctx.beginPath();
    ctx.rect(W * 0.44, roofTop + 6, W * 0.11, bodyTop - roofTop - 7);
    ctx.fill(); ctx.stroke();
    // Trasera (derecha)
    ctx.beginPath();
    ctx.moveTo(W * 0.57, bodyTop - 1);
    ctx.lineTo(W * 0.57, roofTop + 6);
    ctx.lineTo(W * 0.68, roofTop + 6);
    ctx.quadraticCurveTo(W * 0.74, bodyTop * 0.7, W * 0.80, bodyTop - 1);
    ctx.closePath(); ctx.fill(); ctx.stroke();

    // Faros: delantero IZQUIERDA, trasero DERECHA
    _headlight(ctx, bx[0] + 2, bodyTop + 4, W * 0.05, 8, true);
    _headlight(ctx, bx[1] - W * 0.05 - 2, bodyTop + 4, W * 0.05, 8, false);

    // Parachoques
    _bumper(ctx, bx[0], bx[0] + W * 0.06, bodyBot - 2, 6);
    _bumper(ctx, bx[1] - W * 0.06, bx[1], bodyBot - 2, 6);

    // Retrovisor (delantero izquierda)
    _mirror(ctx, W * 0.19, bodyTop - 2, true);

    wx.forEach(x => drawWheel(ctx, x, wheelY, wheelR));
  },

  suv(ctx, W, H, roadY) {
    const wheelR = H * 0.13;
    const wheelY = roadY - wheelR;
    const dims = SIL_DIMS.suv;
    const wx = dims.wx.map(x => x * W);
    const bx = dims.bx.map(x => x * W);

    const bodyBot = roadY - wheelR * 0.5;
    const bodyTop = H * 0.38, roofTop = H * 0.12;

    wx.forEach(x => _wheelArch(ctx, x, roadY, wheelR, "#78909c"));

    // Faldón alto
    ctx.fillStyle = "#78909c";
    ctx.beginPath();
    ctx.roundRect(bx[0], bodyBot + 2, bx[1] - bx[0], 6, 2);
    ctx.fill();

    // Carrocería — delantera IZQUIERDA
    ctx.fillStyle = COL.body_fill; ctx.strokeStyle = COL.body_out; ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(bx[1], bodyBot);
    ctx.lineTo(bx[1], bodyTop + 5);
    ctx.quadraticCurveTo(bx[1], bodyTop, bx[1] - W * 0.03, bodyTop);
    ctx.lineTo(W * 0.83, bodyTop);
    // Pilar C + luneta
    ctx.quadraticCurveTo(W * 0.79, bodyTop, W * 0.75, roofTop + 4);
    ctx.quadraticCurveTo(W * 0.73, roofTop, W * 0.70, roofTop);
    // Techo
    ctx.lineTo(W * 0.30, roofTop);
    // Pilar A + parabrisas
    ctx.quadraticCurveTo(W * 0.27, roofTop, W * 0.25, roofTop + 4);
    ctx.quadraticCurveTo(W * 0.21, bodyTop, W * 0.17, bodyTop);
    // Capó
    ctx.lineTo(bx[0] + W * 0.03, bodyTop);
    ctx.quadraticCurveTo(bx[0], bodyTop, bx[0], bodyTop + 5);
    ctx.lineTo(bx[0], bodyBot);
    ctx.closePath(); ctx.fill(); ctx.stroke();

    // Moldura
    ctx.strokeStyle = "#546e7a"; ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(bx[0] + 5, bodyTop + (bodyBot - bodyTop) * 0.4);
    ctx.lineTo(bx[1] - 5, bodyTop + (bodyBot - bodyTop) * 0.4);
    ctx.stroke();

    _doorLine(ctx, W * 0.42, roofTop + 3, bodyBot);
    _doorLine(ctx, W * 0.57, roofTop + 3, bodyBot);

    // Ventanas
    ctx.fillStyle = COL.win_fill; ctx.strokeStyle = COL.win_out; ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(W * 0.41, bodyTop - 1);
    ctx.lineTo(W * 0.41, roofTop + 6);
    ctx.lineTo(W * 0.27, roofTop + 6);
    ctx.quadraticCurveTo(W * 0.23, bodyTop - 1, W * 0.19, bodyTop - 1);
    ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.beginPath();
    ctx.rect(W * 0.43, roofTop + 6, W * 0.13, bodyTop - roofTop - 7);
    ctx.fill(); ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(W * 0.58, bodyTop - 1); ctx.lineTo(W * 0.58, roofTop + 6);
    ctx.lineTo(W * 0.69, roofTop + 6);
    ctx.quadraticCurveTo(W * 0.76, bodyTop * 0.6, W * 0.81, bodyTop - 1);
    ctx.closePath(); ctx.fill(); ctx.stroke();

    // Barras de techo
    ctx.strokeStyle = "#90a4ae"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(W * 0.30, roofTop - 2); ctx.lineTo(W * 0.70, roofTop - 2); ctx.stroke();

    _headlight(ctx, bx[0] + 2, bodyTop + 3, W * 0.06, 10, true);
    _headlight(ctx, bx[1] - W * 0.06 - 2, bodyTop + 3, W * 0.06, 10, false);
    _bumper(ctx, bx[0], bx[0] + W * 0.07, bodyBot - 3, 8);
    _bumper(ctx, bx[1] - W * 0.07, bx[1], bodyBot - 3, 8);
    _mirror(ctx, W * 0.18, bodyTop - 3, true);

    wx.forEach(x => drawWheel(ctx, x, wheelY, wheelR));
  },

  mono(ctx, W, H, roadY) {
    const wheelR = H * 0.1;
    const wheelY = roadY - wheelR;
    const dims = SIL_DIMS.mono;
    const wx = dims.wx.map(x => x * W);
    const bx = dims.bx.map(x => x * W);

    const bodyBot = roadY - wheelR * 0.65;
    const bodyTop = H * 0.38, roofTop = H * 0.08;

    wx.forEach(x => _wheelArch(ctx, x, roadY, wheelR, "#b0bec5"));

    // Carrocería monovolumen — delantera IZQUIERDA
    ctx.fillStyle = COL.body_fill; ctx.strokeStyle = COL.body_out; ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(bx[1], bodyBot);
    ctx.lineTo(bx[1], bodyTop);
    // Trasera vertical (derecha)
    ctx.quadraticCurveTo(bx[1], bodyTop * 0.7, W * 0.86, roofTop + 8);
    ctx.quadraticCurveTo(W * 0.84, roofTop, W * 0.80, roofTop);
    // Techo largo
    ctx.lineTo(W * 0.16, roofTop);
    // Frontal inclinado (izquierda = delantera)
    ctx.quadraticCurveTo(W * 0.12, roofTop, W * 0.10, roofTop + 10);
    ctx.quadraticCurveTo(bx[0] + W * 0.02, bodyTop, bx[0], bodyTop);
    ctx.lineTo(bx[0], bodyBot);
    ctx.closePath(); ctx.fill(); ctx.stroke();

    ctx.strokeStyle = "#90a4ae"; ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(bx[0] + 5, bodyTop + 4);
    ctx.lineTo(bx[1] - 5, bodyTop + 4);
    ctx.stroke();

    _doorLine(ctx, W * 0.32, roofTop + 3, bodyBot);
    _doorLine(ctx, W * 0.48, roofTop + 3, bodyBot);
    _doorLine(ctx, W * 0.65, roofTop + 3, bodyBot);

    // Ventanas
    ctx.fillStyle = COL.win_fill; ctx.strokeStyle = COL.win_out; ctx.lineWidth = 1.5;
    // Delantera (izquierda)
    ctx.beginPath();
    ctx.moveTo(W * 0.31, bodyTop - 1);
    ctx.lineTo(W * 0.31, roofTop + 6);
    ctx.lineTo(W * 0.16, roofTop + 6);
    ctx.quadraticCurveTo(W * 0.10, roofTop + 6, W * 0.08, bodyTop - 1);
    ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.beginPath();
    ctx.rect(W * 0.33, roofTop + 6, W * 0.14, bodyTop - roofTop - 7);
    ctx.fill(); ctx.stroke();
    ctx.beginPath();
    ctx.rect(W * 0.49, roofTop + 6, W * 0.15, bodyTop - roofTop - 7);
    ctx.fill(); ctx.stroke();
    // Trasera (derecha)
    ctx.beginPath();
    ctx.moveTo(W * 0.66, bodyTop - 1); ctx.lineTo(W * 0.66, roofTop + 6);
    ctx.lineTo(W * 0.79, roofTop + 6);
    ctx.quadraticCurveTo(W * 0.84, roofTop + 10, W * 0.85, bodyTop - 1);
    ctx.closePath(); ctx.fill(); ctx.stroke();

    _headlight(ctx, bx[0] + 2, bodyTop + 2, W * 0.05, 8, true);
    _headlight(ctx, bx[1] - W * 0.05 - 2, bodyTop + 2, W * 0.05, 8, false);
    _bumper(ctx, bx[0], bx[0] + W * 0.05, bodyBot - 2, 5);
    _bumper(ctx, bx[1] - W * 0.05, bx[1], bodyBot - 2, 5);
    _mirror(ctx, W * 0.09, bodyTop - 3, true);

    wx.forEach(x => drawWheel(ctx, x, wheelY, wheelR));
  },

  minibus(ctx, W, H, roadY) {
    const wheelR = H * 0.1;
    const wheelY = roadY - wheelR;
    const dims = SIL_DIMS.minibus;
    const wx = dims.wx.map(x => x * W);
    const bx = dims.bx.map(x => x * W);

    const bodyBot = roadY - wheelR * 0.55;
    const bodyTop = H * 0.36, roofTop = H * 0.06;

    wx.forEach(x => _wheelArch(ctx, x, roadY, wheelR, "#78909c"));

    // Carrocería rectangular
    ctx.fillStyle = COL.body_fill; ctx.strokeStyle = COL.body_out; ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(bx[0], bodyBot);
    ctx.lineTo(bx[0], roofTop + 12);
    ctx.quadraticCurveTo(bx[0], roofTop, bx[0] + 14, roofTop);
    ctx.lineTo(bx[1] - 14, roofTop);
    ctx.quadraticCurveTo(bx[1], roofTop, bx[1], roofTop + 12);
    ctx.lineTo(bx[1], bodyBot);
    ctx.closePath(); ctx.fill(); ctx.stroke();

    // Franja decorativa
    ctx.fillStyle = "#1565c0";
    ctx.beginPath();
    ctx.rect(bx[0] + 1, bodyTop + 2, bx[1] - bx[0] - 2, 5);
    ctx.fill();

    // Ventanas
    ctx.fillStyle = COL.win_fill; ctx.strokeStyle = COL.win_out; ctx.lineWidth = 1.5;
    const winY = roofTop + 10;
    const winH = bodyTop - roofTop - 8;
    const numWin = 6;
    const winGap = (bx[1] - bx[0] - W * 0.06) / numWin;
    for (let i = 0; i < numWin; i++) {
      const wx0 = bx[0] + W * 0.03 + i * winGap;
      const ww = winGap - 4;
      ctx.beginPath();
      ctx.roundRect(wx0, winY, ww, winH, i === 0 ? [4, 2, 2, 4] : 2);
      ctx.fill(); ctx.stroke();
    }

    // Puerta delantera (izquierda)
    ctx.strokeStyle = "#455a64"; ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.roundRect(bx[0] + W * 0.03, roofTop + 8, winGap - 2, bodyBot - roofTop - 10, 3);
    ctx.stroke();

    _headlight(ctx, bx[0] + 2, bodyTop + 8, W * 0.04, 8, true);
    _headlight(ctx, bx[1] - W * 0.04 - 2, bodyTop + 8, W * 0.04, 8, false);
    _mirror(ctx, bx[0] + 2, bodyTop - 3, true);

    wx.forEach(x => drawWheel(ctx, x, wheelY, wheelR));
  },

  autobus(ctx, W, H, roadY) {
    const wheelR = H * 0.1;
    const wheelY = roadY - wheelR;
    const dims = SIL_DIMS.autobus;
    const wx = dims.wx.map(x => x * W);
    const bx = dims.bx.map(x => x * W);

    const bodyBot = roadY - wheelR * 0.45;
    const roofTop = H * 0.04;
    const bodyTop = H * 0.36;

    wx.forEach(x => _wheelArch(ctx, x, roadY, wheelR, "#546e7a"));

    // Carrocería grande
    ctx.fillStyle = COL.body_fill; ctx.strokeStyle = COL.body_out; ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(bx[0], bodyBot);
    ctx.lineTo(bx[0], roofTop + 10);
    ctx.quadraticCurveTo(bx[0], roofTop, bx[0] + 12, roofTop);
    ctx.lineTo(bx[1] - 12, roofTop);
    ctx.quadraticCurveTo(bx[1], roofTop, bx[1], roofTop + 10);
    ctx.lineTo(bx[1], bodyBot);
    ctx.closePath(); ctx.fill(); ctx.stroke();

    // Franjas de color
    ctx.fillStyle = "#1565c0";
    ctx.beginPath(); ctx.rect(bx[0] + 1, bodyTop, bx[1] - bx[0] - 2, 4); ctx.fill();
    ctx.fillStyle = "#0d47a1";
    ctx.beginPath(); ctx.rect(bx[0] + 1, bodyTop + 5, bx[1] - bx[0] - 2, 3); ctx.fill();

    // Ventanas
    ctx.fillStyle = COL.win_fill; ctx.strokeStyle = COL.win_out; ctx.lineWidth = 1;
    const winY = roofTop + 8;
    const winH = bodyTop - roofTop - 10;
    const numWin = 9;
    const totalW = bx[1] - bx[0] - W * 0.04;
    const winGap = totalW / numWin;
    for (let i = 0; i < numWin; i++) {
      const wx0 = bx[0] + W * 0.02 + i * winGap;
      ctx.beginPath();
      ctx.roundRect(wx0, winY, winGap - 3, winH, 2);
      ctx.fill(); ctx.stroke();
    }

    // Puerta doble (delantera izquierda)
    ctx.strokeStyle = "#455a64"; ctx.lineWidth = 1.5;
    const doorX = bx[0] + W * 0.04;
    ctx.beginPath();
    ctx.roundRect(doorX, roofTop + 6, winGap * 1.2, bodyBot - roofTop - 8, 3);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(doorX + winGap * 0.6, roofTop + 8);
    ctx.lineTo(doorX + winGap * 0.6, bodyBot - 4);
    ctx.stroke();

    _headlight(ctx, bx[0] + 2, bodyTop + 10, W * 0.035, 10, true);
    _headlight(ctx, bx[1] - W * 0.035 - 2, bodyTop + 10, W * 0.035, 10, false);
    _mirror(ctx, bx[0] + 2, bodyTop - 5, true);

    wx.forEach(x => drawWheel(ctx, x, wheelY, wheelR));
  },

  furgoneta(ctx, W, H, roadY) {
    const wheelR = H * 0.1;
    const wheelY = roadY - wheelR;
    const dims = SIL_DIMS.furgoneta;
    const wx = dims.wx.map(x => x * W);
    const bx = dims.bx.map(x => x * W);

    const bodyBot = roadY - wheelR * 0.65;
    const bodyTop = H * 0.36, roofTop = H * 0.08;

    wx.forEach(x => _wheelArch(ctx, x, roadY, wheelR, "#78909c"));

    // Cabina (IZQUIERDA = delantera)
    ctx.fillStyle = COL.truck_cabin; ctx.strokeStyle = COL.body_out; ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(bx[0], bodyBot);
    ctx.lineTo(bx[0], bodyTop);
    ctx.quadraticCurveTo(bx[0], bodyTop - 5, W * 0.06, bodyTop - 5);
    ctx.lineTo(W * 0.08, bodyTop - 5);
    // Parabrisas curvo
    ctx.quadraticCurveTo(W * 0.10, roofTop + 4, W * 0.14, roofTop);
    ctx.lineTo(W * 0.31, roofTop);
    ctx.lineTo(W * 0.31, bodyBot);
    ctx.closePath(); ctx.fill(); ctx.stroke();

    // Caja de carga (DERECHA = trasera)
    ctx.fillStyle = COL.truck_box;
    ctx.beginPath();
    ctx.moveTo(W * 0.33, roofTop);
    ctx.lineTo(bx[1] - 3, roofTop);
    ctx.quadraticCurveTo(bx[1], roofTop, bx[1], roofTop + 3);
    ctx.lineTo(bx[1], bodyBot);
    ctx.lineTo(W * 0.33, bodyBot);
    ctx.closePath(); ctx.fill(); ctx.stroke();

    // Listones horizontales
    ctx.strokeStyle = "#90a4ae"; ctx.lineWidth = 0.8;
    for (let i = 1; i <= 3; i++) {
      const ly = roofTop + i * (bodyBot - roofTop) / 4;
      ctx.beginPath(); ctx.moveTo(W * 0.34, ly); ctx.lineTo(bx[1] - 2, ly); ctx.stroke();
    }

    // Ventana cabina
    ctx.fillStyle = COL.win_fill; ctx.strokeStyle = COL.win_out; ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(bx[0] + 6, bodyTop - 2);
    ctx.quadraticCurveTo(W * 0.11, roofTop + 6, W * 0.15, roofTop + 6);
    ctx.lineTo(W * 0.29, roofTop + 6);
    ctx.lineTo(W * 0.29, bodyTop - 2);
    ctx.closePath(); ctx.fill(); ctx.stroke();

    _doorLine(ctx, W * 0.22, roofTop + 4, bodyBot);

    _headlight(ctx, bx[0] + 1, bodyTop + 3, W * 0.04, 8, true);
    _headlight(ctx, bx[1] - W * 0.04 - 1, bodyBot - 14, W * 0.04, 8, false);
    _bumper(ctx, bx[0], bx[0] + W * 0.05, bodyBot - 2, 5);
    _mirror(ctx, W * 0.07, bodyTop - 8, true);

    wx.forEach(x => drawWheel(ctx, x, wheelY, wheelR));
  },

  camion(ctx, W, H, roadY) {
    const wheelR = H * 0.1;
    const wheelY = roadY - wheelR;
    const dims = SIL_DIMS.camion;
    const wx = dims.wx.map(x => x * W);
    const bx = dims.bx.map(x => x * W);

    const bodyBot = roadY - wheelR * 0.55;
    const cabTop = H * 0.12, boxTop = H * 0.14;

    wx.forEach(x => _wheelArch(ctx, x, roadY, wheelR, "#546e7a"));

    // Cabina (IZQUIERDA = delantera)
    ctx.fillStyle = COL.truck_cabin; ctx.strokeStyle = COL.body_out; ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(bx[0], bodyBot);
    ctx.lineTo(bx[0], cabTop + 12);
    ctx.quadraticCurveTo(bx[0], cabTop, bx[0] + 12, cabTop);
    ctx.lineTo(W * 0.27, cabTop);
    ctx.quadraticCurveTo(W * 0.28, cabTop, W * 0.28, cabTop + 5);
    ctx.lineTo(W * 0.28, bodyBot);
    ctx.closePath(); ctx.fill(); ctx.stroke();

    // Caja de carga (DERECHA = trasera)
    ctx.fillStyle = COL.truck_box;
    ctx.beginPath();
    ctx.moveTo(W * 0.30, boxTop);
    ctx.lineTo(bx[1] - 3, boxTop);
    ctx.quadraticCurveTo(bx[1], boxTop, bx[1], boxTop + 3);
    ctx.lineTo(bx[1], bodyBot);
    ctx.lineTo(W * 0.30, bodyBot);
    ctx.closePath(); ctx.fill(); ctx.stroke();

    // Listones
    ctx.strokeStyle = "#90a4ae"; ctx.lineWidth = 0.8;
    for (let i = 1; i <= 3; i++) {
      const ly = boxTop + i * (bodyBot - boxTop) / 4;
      ctx.beginPath(); ctx.moveTo(W * 0.31, ly); ctx.lineTo(bx[1] - 2, ly); ctx.stroke();
    }
    // Refuerzos verticales
    ctx.strokeStyle = "#78909c"; ctx.lineWidth = 1;
    for (let i = 1; i <= 4; i++) {
      const lx = W * 0.30 + i * (bx[1] - W * 0.30) / 5;
      ctx.beginPath(); ctx.moveTo(lx, boxTop + 2); ctx.lineTo(lx, bodyBot - 2); ctx.stroke();
    }

    // Ventana cabina
    ctx.fillStyle = COL.win_fill; ctx.strokeStyle = COL.win_out; ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.roundRect(bx[0] + 6, cabTop + 6, W * 0.22, H * 0.20, 3);
    ctx.fill(); ctx.stroke();

    // Estribo
    ctx.fillStyle = "#455a64";
    ctx.beginPath();
    ctx.roundRect(bx[0] + W * 0.02, bodyBot + 2, W * 0.08, 5, 2);
    ctx.fill();

    _headlight(ctx, bx[0] + 2, cabTop + H * 0.28, W * 0.04, 10, true);
    _headlight(ctx, bx[1] - W * 0.04, bodyBot - 14, W * 0.04, 8, false);
    _mirror(ctx, bx[0] + 2, cabTop + 6, true);

    wx.forEach(x => drawWheel(ctx, x, wheelY, wheelR));
    // Doble rueda trasera
    if (wx.length >= 3) {
      drawWheel(ctx, wx[2] + wheelR * 1.1, wheelY, wheelR * 0.9);
    }
  },

  moto(ctx, W, H, roadY) {
    const wheelR = H * 0.13;
    const wheelY = roadY - wheelR;
    const dims = SIL_DIMS.moto;
    const wx = dims.wx.map(x => x * W);

    // Horquilla delantera (IZQUIERDA)
    ctx.strokeStyle = "#546e7a"; ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(wx[0] + 2, wheelY - wheelR * 0.3);
    ctx.lineTo(W * 0.36, H * 0.20);
    ctx.stroke();

    // Chasis
    ctx.strokeStyle = COL.body_out; ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(W * 0.36, H * 0.22);
    ctx.quadraticCurveTo(W * 0.42, H * 0.18, W * 0.48, H * 0.22);
    ctx.lineTo(W * 0.62, H * 0.35);
    ctx.lineTo(wx[1], wheelY - wheelR * 0.5);
    ctx.stroke();

    // Basculante trasero (DERECHA)
    ctx.strokeStyle = "#546e7a"; ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(W * 0.55, H * 0.32);
    ctx.lineTo(wx[1], wheelY);
    ctx.stroke();

    // Depósito
    const grad = ctx.createLinearGradient(W * 0.38, H * 0.17, W * 0.38, H * 0.28);
    grad.addColorStop(0, "#1565c0"); grad.addColorStop(1, "#0d47a1");
    ctx.fillStyle = grad; ctx.strokeStyle = "#0d47a1"; ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(W * 0.36, H * 0.24);
    ctx.quadraticCurveTo(W * 0.38, H * 0.16, W * 0.46, H * 0.17);
    ctx.quadraticCurveTo(W * 0.52, H * 0.18, W * 0.52, H * 0.24);
    ctx.quadraticCurveTo(W * 0.48, H * 0.27, W * 0.40, H * 0.27);
    ctx.closePath(); ctx.fill(); ctx.stroke();

    // Asiento
    ctx.fillStyle = "#37474f"; ctx.strokeStyle = "#263238"; ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(W * 0.48, H * 0.24);
    ctx.quadraticCurveTo(W * 0.52, H * 0.21, W * 0.56, H * 0.23);
    ctx.lineTo(W * 0.64, H * 0.30);
    ctx.quadraticCurveTo(W * 0.62, H * 0.33, W * 0.56, H * 0.32);
    ctx.lineTo(W * 0.48, H * 0.28);
    ctx.closePath(); ctx.fill(); ctx.stroke();

    // Motor
    ctx.fillStyle = "#455a64"; ctx.strokeStyle = "#263238"; ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(W * 0.40, H * 0.34, W * 0.10, H * 0.16, 3);
    ctx.fill(); ctx.stroke();

    // Faro delantero (IZQUIERDA)
    ctx.fillStyle = "#ffee58"; ctx.strokeStyle = "#f9a825"; ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(W * 0.33, H * 0.20, 5, 0, Math.PI * 2);
    ctx.fill(); ctx.stroke();

    // Faro trasero (DERECHA)
    ctx.fillStyle = "#ef5350"; ctx.strokeStyle = "#c62828"; ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(W * 0.63, H * 0.27, 4, 6, 1);
    ctx.fill(); ctx.stroke();

    // Manillar
    ctx.strokeStyle = "#37474f"; ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(W * 0.34, H * 0.14); ctx.lineTo(W * 0.38, H * 0.20);
    ctx.stroke();

    // Escape (sale hacia la derecha = trasera)
    ctx.strokeStyle = "#78909c"; ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(W * 0.48, H * 0.42);
    ctx.quadraticCurveTo(W * 0.56, H * 0.48, W * 0.64, H * 0.45);
    ctx.stroke();
    ctx.fillStyle = "#90a4ae";
    ctx.beginPath();
    ctx.ellipse(W * 0.65, H * 0.45, 6, 4, 0, 0, Math.PI * 2);
    ctx.fill();

    // Ruedas
    wx.forEach(x => {
      drawWheel(ctx, x, wheelY, wheelR);
      ctx.strokeStyle = "#78909c"; ctx.lineWidth = 1;
      for (let a = 0; a < 6; a++) {
        const ang = a * Math.PI / 3;
        ctx.beginPath();
        ctx.moveTo(x, wheelY);
        ctx.lineTo(x + Math.cos(ang) * wheelR * 0.8, wheelY + Math.sin(ang) * wheelR * 0.8);
        ctx.stroke();
      }
    });
  },
};

// ── Row bars (arrastrables) ─────────────────────────────────────
function drawRowBars() {
  const canvas = document.getElementById("sil-row-canvas");
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const colors = ["#ff8f00", "#f57c00", "#ef6c00"];

  for (let i = 0; i < silFilas; i++) {
    const x = silRowXnorm[i] * W;
    const barW = 20, barH = H - 10;
    const y = 5;

    ctx.fillStyle = colors[i % 3];
    ctx.strokeStyle = "#e65100";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.roundRect(x - barW / 2, y, barW, barH, 4);
    ctx.fill(); ctx.stroke();

    // Texto fila
    ctx.fillStyle = "#fff";
    ctx.font = "bold 11px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(`F${i + 1}`, x, y + barH / 2);

    // Flecha triangular arriba
    ctx.fillStyle = "#e65100";
    ctx.beginPath();
    ctx.moveTo(x, y - 2);
    ctx.lineTo(x - 5, y + 5);
    ctx.lineTo(x + 5, y + 5);
    ctx.closePath();
    ctx.fill();
  }
}

function silDragStart(e) {
  const canvas = document.getElementById("sil-row-canvas");
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / rect.width;

  let bestDist = 0.04;
  silDragIdx = -1;
  for (let i = 0; i < silFilas; i++) {
    const d = Math.abs(silRowXnorm[i] - mx);
    if (d < bestDist) {
      bestDist = d;
      silDragIdx = i;
    }
  }
  if (silDragIdx >= 0) canvas.style.cursor = "grabbing";
}

function silDragMove(e) {
  if (silDragIdx < 0) return;
  const canvas = document.getElementById("sil-row-canvas");
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / rect.width;

  const dims = SIL_DIMS[silTipo];
  const xMin = dims.wx[0] + 0.02;
  const xMax = (dims.bx[1] || 0.95) - 0.02;
  silRowXnorm[silDragIdx] = Math.max(xMin, Math.min(xMax, mx));
  syncXnormToDist();
  drawAll();
}

function silDragEnd() {
  silDragIdx = -1;
  const canvas = document.getElementById("sil-row-canvas");
  if (canvas) canvas.style.cursor = "grab";
}

// ── Dimensiones (cotas) ─────────────────────────────────────────
function drawDimensiones() {
  const canvas = document.getElementById("sil-dim-canvas");
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const dims = SIL_DIMS[silTipo];
  const bx0 = dims.bx[0] * W, bx1 = dims.bx[1] * W;
  const wx = dims.wx.map(x => x * W);

  const y1 = 15, y2 = 40, y3 = 65;

  ctx.strokeStyle = "#1565c0";
  ctx.fillStyle = "#1565c0";
  ctx.font = "10px sans-serif";
  ctx.textAlign = "center";
  ctx.lineWidth = 1;

  // Longitud total
  drawDimLine(ctx, bx0, bx1, y1, getLongitud() || "Long. total");

  // Dist. entre ejes (eje 1 → eje 2)
  if (wx.length >= 2) {
    drawDimLine(ctx, wx[0], wx[1], y2, getDistEjes() || "Dist. ejes");
  }

  // Voladizo trasero
  if (wx.length >= 2) {
    drawDimLine(ctx, wx[wx.length - 1], bx1, y3, getVoladizo() || "Voladizo");
  }

  // Dist filas desde eje 1
  ctx.strokeStyle = "#e65100";
  ctx.fillStyle = "#e65100";
  ctx.font = "9px sans-serif";
  for (let i = 0; i < silFilas; i++) {
    const xf = silRowXnorm[i] * W;
    // Linea punteada vertical desde fila
    ctx.setLineDash([2, 2]);
    ctx.beginPath(); ctx.moveTo(xf, 0); ctx.lineTo(xf, y2 - 5); ctx.stroke();
    ctx.setLineDash([]);

    // Etiqueta distancia
    const distMm = getDistFilaMm(i);
    if (distMm !== null) {
      ctx.fillText(`F${i + 1}: ${distMm} mm`, xf, y2 + 18);
    }
  }

  // Flechas R1, R2 (reacciones del balance)
  if (silBalR1 > 0 || silBalR2 > 0) {
    ctx.strokeStyle = "#e65100";
    ctx.fillStyle = "#e65100";
    ctx.lineWidth = 2;
    ctx.font = "bold 10px sans-serif";

    wx.forEach((x, i) => {
      const r = i === 0 ? silBalR1 : (i === wx.length - 1 ? silBalR2 : 0);
      if (r > 0) {
        const arrowY = 8;
        // Flecha hacia arriba
        ctx.beginPath();
        ctx.moveTo(x, arrowY + 18);
        ctx.lineTo(x, arrowY);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(x, arrowY - 2);
        ctx.lineTo(x - 4, arrowY + 5);
        ctx.lineTo(x + 4, arrowY + 5);
        ctx.closePath(); ctx.fill();

        ctx.fillText(`R${i + 1}=${Math.round(r)}`, x, arrowY + 30);
      }
    });
  }
}

function drawDimLine(ctx, x1, x2, y, label) {
  ctx.beginPath();
  ctx.moveTo(x1, y); ctx.lineTo(x2, y);
  ctx.stroke();
  // Flechas
  ctx.beginPath(); ctx.moveTo(x1, y); ctx.lineTo(x1 + 5, y - 3); ctx.lineTo(x1 + 5, y + 3); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.moveTo(x2, y); ctx.lineTo(x2 - 5, y - 3); ctx.lineTo(x2 - 5, y + 3); ctx.closePath(); ctx.fill();
  // Líneas verticales extremos
  ctx.beginPath(); ctx.moveTo(x1, y - 6); ctx.lineTo(x1, y + 6); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x2, y - 6); ctx.lineTo(x2, y + 6); ctx.stroke();
  // Texto
  ctx.fillText(String(label), (x1 + x2) / 2, y - 5);
}

// ── Helpers de datos dimensionales ──────────────────────────────
function fval(id, defecto) {
  const el = document.getElementById(id);
  if (!el) return defecto || 0;
  const v = parseFloat(el.value.replace(",", "."));
  return isNaN(v) ? (defecto || 0) : v;
}

function getLongitud() { return fval("sil_longitud"); }
function getDistEjes() { return fval("sil_dist_ejes"); }
function getVoladizo() { return fval("sil_voladizo"); }

function getDistFilaMm(idx) {
  const longTotal = getLongitud();
  const distEjes = getDistEjes();
  if (!longTotal || !distEjes) return null;

  const dims = SIL_DIMS[silTipo];
  const wx0 = dims.wx[0]; // posición normalizada eje 1
  const xnorm = silRowXnorm[idx];

  // Convertir diferencia normalizada a mm
  const bx0 = dims.bx[0], bx1 = dims.bx[1];
  const escala = longTotal / (bx1 - bx0); // mm por unidad normalizada
  const distMm = (xnorm - wx0) * escala;
  return Math.round(distMm);
}

function syncXnormToDist() {
  // Actualizar inputs de distancia (si existen)
  for (let i = 0; i < silFilas; i++) {
    const el = document.getElementById(`sil_dist_fila_${i}`);
    if (el) {
      const d = getDistFilaMm(i);
      el.value = d !== null ? d : "";
    }
  }
}

function onDistFilaChange(idx) {
  const el = document.getElementById(`sil_dist_fila_${idx}`);
  if (!el) return;
  const distMm = parseFloat(el.value.replace(",", "."));
  if (isNaN(distMm)) return;

  const longTotal = getLongitud();
  if (!longTotal) return;

  const dims = SIL_DIMS[silTipo];
  const bx0 = dims.bx[0], bx1 = dims.bx[1];
  const wx0 = dims.wx[0];
  const escala = longTotal / (bx1 - bx0);
  const xnorm = wx0 + distMm / escala;
  silRowXnorm[idx] = Math.max(0.05, Math.min(0.95, xnorm));
  drawAll();
}

function onSilDataChange() {
  syncXnormToDist();
  drawAll();
}

// ── Balance de masas ────────────────────────────────────────────
function recalcularBalance() {
  const T1 = fval("sil_tara1");
  const T2 = fval("sil_tara2");
  const MMA = fval("sil_mma");
  const MMA_e1 = fval("sil_mma1");
  const MMA_e2 = fval("sil_mma2");
  const distEj = fval("sil_dist_ejes");
  const volad = fval("sil_voladizo");
  const longCaja = fval("sil_long_caja");
  const TARA = T1 + T2;

  if (!distEj || !TARA || !MMA) {
    setBalLabel("bal-qu", "— kg", "neutral");
    setBalLabel("bal-r1", "— kgf", "neutral");
    setBalLabel("bal-r2", "— kgf", "neutral");
    setBalLabel("bal-v1", "—", "neutral");
    setBalLabel("bal-v2", "—", "neutral");
    silBalR1 = 0; silBalR2 = 0;
    return;
  }

  // Peso ocupantes por fila
  const O = [];
  const dP = [];
  for (let i = 0; i < silFilas; i++) {
    const nPas = fval(`sil_asientos_${i}`, 0);
    O.push(nPas * 75);
    const d = getDistFilaMm(i);
    dP.push(d !== null ? d : 0);
  }
  const sumO = O.reduce((a, b) => a + b, 0);
  const Qu = MMA - (TARA + sumO);

  const esN1 = (silTipo === "furgoneta" || silTipo === "camion");
  let R1, R2;

  if (esN1 && longCaja > 0) {
    // N1: carga distribuida en caja
    const puntoCarga = longCaja / 2;
    const dQuEje2 = volad - puntoCarga;

    let R1_ocu = 0, R2_ocu = 0;
    for (let i = 0; i < silFilas; i++) {
      R1_ocu += (1 - dP[i] / distEj) * O[i];
      R2_ocu += (dP[i] / distEj) * O[i];
    }

    const R1_Qu = -(Qu * dQuEje2) / distEj;
    const R2_Qu = Qu - R1_Qu;

    R1 = T1 + R1_ocu + R1_Qu;
    R2 = T2 + R2_ocu + R2_Qu;
  } else {
    // M1/M2: momento respecto eje 1
    let dQu = distEj;
    if (volad > 0) dQu = distEj + volad / 2;

    let momentoR2 = T2 * distEj;
    for (let i = 0; i < silFilas; i++) {
      momentoR2 += O[i] * dP[i];
    }
    momentoR2 += Qu * dQu;

    R2 = momentoR2 / distEj;
    R1 = TARA + sumO + Qu - R2;
  }

  silBalR1 = R1;
  silBalR2 = R2;

  setBalLabel("bal-qu", `${Math.round(Qu)} kg`, Qu >= 0 ? "ok" : "err");
  setBalLabel("bal-r1", `${Math.round(R1)} kgf`, "neutral");
  setBalLabel("bal-r2", `${Math.round(R2)} kgf`, "neutral");

  if (MMA_e1 > 0) {
    setBalLabel("bal-v1", R1 <= MMA_e1 ? "OK" : "EXCEDE", R1 <= MMA_e1 ? "ok" : "err");
  } else {
    setBalLabel("bal-v1", "—", "neutral");
  }
  if (MMA_e2 > 0) {
    setBalLabel("bal-v2", R2 <= MMA_e2 ? "OK" : "EXCEDE", R2 <= MMA_e2 ? "ok" : "err");
  } else {
    setBalLabel("bal-v2", "—", "neutral");
  }

  // Redibujar dimensiones con flechas
  drawDimensiones();
}

function setBalLabel(id, text, cls) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  el.className = "bal-result bal-" + cls;
}

// ── Asientos por fila (inputs dinámicos) ────────────────────────
function buildAsientosInputs() {
  const container = document.getElementById("sil-asientos-container");
  if (!container) return;
  let html = '<div class="row g-1">';
  for (let i = 0; i < silFilas; i++) {
    html += `
      <div class="col">
        <label class="form-label-sm">Fila ${i + 1} (plazas)</label>
        <input type="number" class="form-control form-control-sm" id="sil_asientos_${i}"
               value="${i === 0 ? 2 : 3}" min="0" max="20" oninput="recalcularBalance()">
      </div>
      <div class="col">
        <label class="form-label-sm">Dist. eje 1 (mm)</label>
        <input type="text" class="form-control form-control-sm" id="sil_dist_fila_${i}"
               oninput="onDistFilaChange(${i})">
      </div>`;
  }
  html += '</div>';
  container.innerHTML = html;
  syncXnormToDist();
}
