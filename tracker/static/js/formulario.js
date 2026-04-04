/* ═══════════════════════════════════════════════════════════════
   PHICAN WebApp — Lógica del formulario de proyecto
   ═══════════════════════════════════════════════════════════════ */

// ── Recoger todos los datos del formulario ──────────────────────
function recogerDatos() {
  const datos = {};
  document.querySelectorAll("input[id], select[id], textarea[id]").forEach(el => {
    if (el.id && !el.id.startsWith("sil_") && !el.id.startsWith("bal-") &&
        !el.id.startsWith("ficha-") && !el.id.startsWith("cfo-foto-")) {
      datos[el.id] = el.value;
    }
  });

  // Campos de silueta y balance
  datos.SIL_TIPO = silTipo;
  datos.SIL_FILAS = silFilas;
  datos.SIL_LONGITUD = fval("sil_longitud");
  datos.SIL_VOLADIZO = fval("sil_voladizo");
  datos.SIL_DIST_EJES = fval("sil_dist_ejes");
  datos.SIL_TARA1 = fval("sil_tara1");
  datos.SIL_TARA2 = fval("sil_tara2");
  datos.SIL_MMA = fval("sil_mma");
  datos.SIL_MMA1 = fval("sil_mma1");
  datos.SIL_MMA2 = fval("sil_mma2");

  // Asientos por fila
  for (let i = 0; i < silFilas; i++) {
    datos[`SIL_ASIENTOS_${i}`] = fval(`sil_asientos_${i}`, 0);
  }

  // Categoría código
  const catFull = document.getElementById("CATEGORIA_VEHICULO")?.value || "";
  datos.CATEGORIA_CODIGO = catFull.split(" ")[0] || "";

  // Reformas
  datos.REFORMAS = recogerReformas();

  // Cálculos
  datos.CALCULOS = recogerCalculos();

  return datos;
}


// ── Ficha técnica desde foto (Claude Vision) ────────────────────
function leerFichaVision() {
  document.getElementById("ficha-file-input").click();
}

function enviarFichaVision(input) {
  if (!input.files || !input.files[0]) return;
  const file = input.files[0];
  const status = document.getElementById("ficha-status");
  const sizeMB = (file.size / 1024 / 1024).toFixed(1);
  status.textContent = `Leyendo ficha tecnica (${sizeMB} MB)... puede tardar 15-30s`;
  status.style.color = "#1565c0";

  const formData = new FormData();
  formData.append("imagen", file);

  fetch("/formulario/api/ficha-vision", {
    method: "POST",
    body: formData,
  })
    .then(r => {
      if (!r.ok && r.status >= 500) {
        return r.text().then(txt => {
          try { return JSON.parse(txt); }
          catch(e) { return {error: `Error servidor (${r.status}): ${txt.substring(0,300)}`}; }
        });
      }
      return r.json();
    })
    .then(data => {
      if (data.error) {
        // Si falta la API Key, pedir al usuario que la introduzca
        if (data.need_key) {
          status.textContent = "";
          const key = prompt(
            "Introduce tu API Key de Google Gemini (GRATIS).\n\n" +
            "1. Ve a: aistudio.google.com/apikey\n" +
            "2. Pulsa 'Create API Key'\n" +
            "3. Copia la key y pegala aqui:\n"
          );
          if (key && key.trim()) {
            fetch("/formulario/api/config", {
              method: "POST",
              headers: {"Content-Type": "application/json"},
              body: JSON.stringify({"GEMINI_API_KEY": key.trim()})
            }).then(() => {
              status.textContent = "API Key de Gemini guardada. Pulsa de nuevo para leer la ficha.";
              status.style.color = "#2e7d32";
            });
          } else {
            status.textContent = "Operacion cancelada — se necesita API Key";
            status.style.color = "#e65100";
          }
          return;
        }
        let errMsg = "Error: " + data.error;
        if (data.raw) errMsg += " | Raw: " + data.raw.substring(0, 150);
        if (data.traceback) errMsg += " | TB: " + data.traceback.substring(0, 200);
        status.textContent = errMsg;
        status.style.color = "#c62828";
        console.error("Vision error:", data);
        return;
      }
      const campos = data.campos || {};
      let n = 0;

      // Mapeo de campos Vision → IDs de la silueta/balance
      const visionToSilueta = {
        "DISTANCIA_EJES": "sil_dist_ejes",
        "LONGITUD_VEH":   "sil_longitud",
        "VOLADIZO_A":     "sil_voladizo",
        "MMA":            "sil_mma",
        "TARA_EJE1":      "sil_tara1",
        "TARA_EJE2":      "sil_tara2",
        "MMA_EJE1":       "sil_mma1",
        "MMA_EJE2":       "sil_mma2",
      };

      // Mapeo de campos Vision → campos del formulario con ID diferente
      const visionToForm = {
        "N_HOMOLOGACION": "HOMOL_BASE_A",
      };

      for (const [key, val] of Object.entries(campos)) {
        if (!val) continue;
        // 1) Rellenar campo directo (ficha reducida)
        const el = document.getElementById(key);
        if (el) { el.value = val; n++; }

        // 2) Rellenar campo mapeado (Vision key → Form ID diferente)
        if (visionToForm[key]) {
          _setIfEmpty(visionToForm[key], val);
          n++;
        }

        // 3) Rellenar campo de silueta si hay mapeo
        if (visionToSilueta[key]) {
          _setIfEmpty(visionToSilueta[key], String(val).replace(/[^\d.]/g, ""));
        }
      }

      // Parsear tara por ejes si viene como "eje1/eje2" en TARA_VEHICULO_KG
      if (campos.TARA_VEHICULO_KG && !campos.TARA_EJE1) {
        const taraStr = String(campos.TARA_VEHICULO_KG);
        if (taraStr.includes("/")) {
          const parts = taraStr.split("/");
          _setIfEmpty("sil_tara1", parts[0]?.trim().replace(/[^\d]/g, ""));
          _setIfEmpty("sil_tara2", parts[1]?.trim().replace(/[^\d]/g, ""));
        }
      }

      // Parsear MMA por ejes si viene como texto en MMA_EJE_A
      if (campos.MMA_EJE_A && !campos.MMA_EJE1) {
        const mmaEStr = String(campos.MMA_EJE_A);
        if (mmaEStr.includes("/")) {
          const parts = mmaEStr.split("/");
          _setIfEmpty("sil_mma1", parts[0]?.trim().replace(/[^\d]/g, ""));
          _setIfEmpty("sil_mma2", parts[1]?.trim().replace(/[^\d]/g, ""));
        }
      }

      // Autoseleccionar categoría del vehículo si viene CATEGORIA_DGT
      if (campos.CATEGORIA_DGT) {
        const catSel = document.getElementById("CATEGORIA_VEHICULO");
        if (catSel) {
          const catVal = String(campos.CATEGORIA_DGT).toUpperCase().trim();
          for (const opt of catSel.options) {
            if (opt.value.toUpperCase().startsWith(catVal.substring(0, 2))) {
              catSel.value = opt.value;
              catSel.dispatchEvent(new Event("change"));
              break;
            }
          }
        }
      }

      // Disparar recalculos de la silueta y balance
      if (typeof onSilDataChange === "function") onSilDataChange();
      if (typeof recalcularBalance === "function") recalcularBalance();

      const prov = data.provider || "Vision";
      status.textContent = `${n} campos completados (${prov})`;
      status.style.color = "#2e7d32";
    })
    .catch(err => {
      console.error("Vision error:", err);
      status.textContent = "Error de conexion";
      status.style.color = "#c62828";
    });

  // Reset input
  input.value = "";
}

/** Helper: poner valor solo si el campo esta vacio */
function _setIfEmpty(id, val) {
  if (!val) return;
  const el = document.getElementById(id);
  if (el && !el.value) el.value = val;
}


// ── Buscar vehículo en BD local ─────────────────────────────────
function buscarVehiculoBD() {
  const mat = document.getElementById("MATRICULA")?.value?.trim() || "";
  const bas = document.getElementById("NUM_BASTIDOR")?.value?.trim() || "";
  const status = document.getElementById("ficha-status");

  if (!mat && !bas) {
    status.textContent = "Indica matricula o bastidor para buscar";
    status.style.color = "#e65100";
    return;
  }

  status.textContent = "Buscando en BD local...";
  status.style.color = "#1565c0";

  const params = new URLSearchParams();
  if (mat) params.set("matricula", mat);
  if (bas) params.set("bastidor", bas);

  fetch(`/formulario/api/vehiculo/buscar?${params}`)
    .then(r => r.json())
    .then(data => {
      if (data.vehiculo) {
        let n = 0;
        for (const [key, val] of Object.entries(data.vehiculo)) {
          if (val) {
            const el = document.getElementById(key);
            if (el) { el.value = val; n++; }
          }
        }
        status.textContent = `${n} campos completados desde BD local`;
        status.style.color = "#2e7d32";
      } else {
        status.textContent = "No encontrado en BD local";
        status.style.color = "#c62828";
      }
    })
    .catch(() => {
      status.textContent = "Error de conexion";
      status.style.color = "#c62828";
    });
}


// ── GIAVEH ──────────────────────────────────────────────────────
function abrirGiaveh() {
  window.open(
    "https://industria.serviciosmin.gob.es/giaveh/FR/Extranet/ConsultaFichasReducidas.aspx",
    "_blank"
  );
}


// ── Cambio de categoría ─────────────────────────────────────────
function onCategoriaChange() {
  const catFull = document.getElementById("CATEGORIA_VEHICULO").value;
  const codigo = catFull.split(" ")[0];
  // Actualizar códigos de reforma disponibles
  updateReformaOptions(codigo);
}


// ── Reformas ────────────────────────────────────────────────────
let reformaCount = 0;

function addReforma() {
  reformaCount++;
  const id = reformaCount;
  const container = document.getElementById("reforma-list");

  const card = document.createElement("div");
  card.className = "reforma-card";
  card.id = `reforma-${id}`;
  card.innerHTML = `
    <div class="d-flex justify-content-between align-items-center mb-2">
      <strong class="text-primary">Reforma #${id}</strong>
      <button class="btn btn-outline-danger btn-sm" onclick="delReforma(${id})">
        <i class="bi bi-trash"></i>
      </button>
    </div>
    <div class="row g-2">
      <div class="col-md-3">
        <label class="form-label-sm">Codigo de reforma</label>
        <select class="form-select form-select-sm reforma-codigo" id="ref_cod_${id}"
                onchange="onReformaCodChange(${id})">
          <option value="">— Seleccionar —</option>
        </select>
      </div>
      <div class="col-md-2">
        <label class="form-label-sm">Grupo</label>
        <input type="text" class="form-control form-control-sm" id="ref_grp_${id}" readonly>
      </div>
      <div class="col-md-7">
        <label class="form-label-sm">Descripcion</label>
        <input type="text" class="form-control form-control-sm" id="ref_desc_${id}" readonly>
      </div>
    </div>
    <div id="ref_dir_${id}" class="mt-2"></div>
    <div id="ref_items_${id}" class="mt-2"></div>
    <button class="btn btn-outline-secondary btn-sm mt-1" onclick="addReformaItem(${id})">
      <i class="bi bi-plus"></i> Anadir detalle
    </button>
  `;
  container.appendChild(card);

  // Llenar opciones de código
  const catFull = document.getElementById("CATEGORIA_VEHICULO")?.value || "";
  const catCod = catFull.split(" ")[0];
  updateReformaSelect(id, catCod);
}

function delReforma(id) {
  const el = document.getElementById(`reforma-${id}`);
  if (el) el.remove();
}

function onReformaCodChange(id) {
  const sel = document.getElementById(`ref_cod_${id}`);
  const cod = sel.value;
  // Los datos de códigos se cargan al inicio via Jinja
  if (cod && window._codigosReforma && window._codigosReforma[cod]) {
    const info = window._codigosReforma[cod];
    document.getElementById(`ref_grp_${id}`).value = info[0] || "";
    document.getElementById(`ref_desc_${id}`).value = info[1] || "";
  } else {
    document.getElementById(`ref_grp_${id}`).value = "";
    document.getElementById(`ref_desc_${id}`).value = "";
  }
}

function updateReformaSelect(id, catCod) {
  const sel = document.getElementById(`ref_cod_${id}`);
  if (!sel || !window._codigosReforma) return;
  sel.innerHTML = '<option value="">— Seleccionar —</option>';
  for (const [cod, info] of Object.entries(window._codigosReforma)) {
    const cats = info[2] || [];
    if (!catCod || cats.includes(catCod)) {
      const opt = document.createElement("option");
      opt.value = cod;
      opt.textContent = `${cod} — ${(info[1] || "").substring(0, 60)}`;
      sel.appendChild(opt);
    }
  }
}

function updateReformaOptions(catCod) {
  document.querySelectorAll(".reforma-codigo").forEach(sel => {
    const id = sel.id.replace("ref_cod_", "");
    updateReformaSelect(id, catCod);
  });
}

let reformaItemCount = 0;
function addReformaItem(refId) {
  reformaItemCount++;
  const container = document.getElementById(`ref_items_${refId}`);
  const itemId = reformaItemCount;
  const div = document.createElement("div");
  div.className = "row g-1 mb-1";
  div.id = `ref_item_${itemId}`;
  div.innerHTML = `
    <div class="col-md-4">
      <input type="text" class="form-control form-control-sm" placeholder="Componente"
             id="refi_comp_${itemId}">
    </div>
    <div class="col-md-3">
      <input type="text" class="form-control form-control-sm" placeholder="Marca / Ref."
             id="refi_marca_${itemId}">
    </div>
    <div class="col-md-4">
      <input type="text" class="form-control form-control-sm" placeholder="Descripcion"
             id="refi_desc_${itemId}">
    </div>
    <div class="col-md-1">
      <button class="btn btn-outline-danger btn-sm w-100" onclick="document.getElementById('ref_item_${itemId}').remove()">
        <i class="bi bi-x"></i>
      </button>
    </div>
  `;
  container.appendChild(div);
}

function recogerReformas() {
  const reformas = [];
  document.querySelectorAll(".reforma-card").forEach(card => {
    const id = card.id.replace("reforma-", "");
    const cod = document.getElementById(`ref_cod_${id}`)?.value || "";
    if (!cod) return;
    const items = [];
    const itemsContainer = document.getElementById(`ref_items_${id}`);
    if (itemsContainer) {
      itemsContainer.querySelectorAll(".row").forEach(row => {
        const inputs = row.querySelectorAll("input");
        if (inputs.length >= 3) {
          items.push({
            componente: inputs[0].value,
            marca: inputs[1].value,
            descripcion: inputs[2].value,
          });
        }
      });
    }
    reformas.push({
      codigo: cod,
      grupo: document.getElementById(`ref_grp_${id}`)?.value || "",
      descripcion: document.getElementById(`ref_desc_${id}`)?.value || "",
      items,
    });
  });
  return reformas;
}


// ── Cálculos ────────────────────────────────────────────────────
let calcCount = 0;

function addCalcBloque() {
  calcCount++;
  const id = calcCount;
  const container = document.getElementById("calc-bloques");

  const card = document.createElement("div");
  card.className = "reforma-card";
  card.id = `calc-${id}`;
  card.innerHTML = `
    <div class="d-flex justify-content-between align-items-center mb-2">
      <strong class="text-primary">Calculo #${id}</strong>
      <button class="btn btn-outline-danger btn-sm" onclick="delCalcBloque(${id})">
        <i class="bi bi-trash"></i>
      </button>
    </div>
    <div class="row g-2">
      <div class="col-md-6">
        <label class="form-label-sm">Tipo de calculo</label>
        <select class="form-select form-select-sm" id="calc_tipo_${id}">
          <option value="">— Sin calculo —</option>
          <option value="union_atornillada_int">Uniones atornilladas — Interior</option>
          <option value="union_atornillada_ext">Uniones atornilladas — Exterior</option>
          <option value="flexion">Flexion simple de viga — Navier</option>
          <option value="torsion">Torsion de perfil — Saint-Venant</option>
          <option value="pandeo">Pandeo de columna — Euler</option>
          <option value="ejes_pasadores">Ejes y pasadores</option>
          <option value="vuelco">Estabilidad al vuelco</option>
          <option value="soldadura">Soldadura</option>
          <option value="grua">Resistencia estructura grua</option>
          <option value="balance_masas">Balance de masas</option>
          <option value="ua_aero">Estabilidad UA — Efecto aerodinamico</option>
          <option value="adh_aero">Adherencia — Efecto aerodinamico</option>
          <option value="tacos_elasticos">Tacos elasticos / Silent-blocks</option>
          <option value="pt_remolque">Peso maximo tecnico remolque</option>
          <option value="frenos">Calculo del sistema de frenado</option>
          <option value="suspension_neumatica">Suspension neumatica</option>
          <option value="suspension_mecanica">Suspension mecanica</option>
          <option value="motor">Cambio de motor</option>
          <option value="conversion_electrica">Conversion electrica</option>
          <option value="enganche">Enganche / Dispositivo acoplamiento</option>
          <option value="masas">Modificacion de masas / MMA</option>
          <option value="carroceria">Modificacion de carroceria</option>
          <option value="frenos_mod">Modificacion sistema de frenos</option>
        </select>
      </div>
      <div class="col-md-6">
        <label class="form-label-sm">Descripcion / Notas</label>
        <input type="text" class="form-control form-control-sm" id="calc_desc_${id}">
      </div>
    </div>
    <div id="calc_campos_${id}" class="mt-2">
      <small class="text-muted">Selecciona un tipo de calculo para ver los campos</small>
    </div>
  `;
  container.appendChild(card);
}

function delCalcBloque(id) {
  const el = document.getElementById(`calc-${id}`);
  if (el) el.remove();
}

function recogerCalculos() {
  const calcs = [];
  document.querySelectorAll("[id^='calc-']").forEach(card => {
    if (!card.id.startsWith("calc-")) return;
    const id = card.id.replace("calc-", "");
    const tipo = document.getElementById(`calc_tipo_${id}`)?.value || "";
    if (!tipo) return;
    calcs.push({
      tipo,
      descripcion: document.getElementById(`calc_desc_${id}`)?.value || "",
    });
  });
  return calcs;
}


// ── CFO Fotos ───────────────────────────────────────────────────
let fotoCount = 0;
function addFotoCfo() {
  fotoCount++;
  const container = document.getElementById("cfo-fotos");
  const div = document.createElement("div");
  div.className = "row g-2 mb-2";
  div.id = `cfo-foto-row-${fotoCount}`;
  div.innerHTML = `
    <div class="col-md-5">
      <input type="file" class="form-control form-control-sm" accept="image/*"
             id="cfo-foto-file-${fotoCount}">
    </div>
    <div class="col-md-5">
      <input type="text" class="form-control form-control-sm" placeholder="Descripcion de la foto"
             id="cfo-foto-desc-${fotoCount}">
    </div>
    <div class="col-md-2">
      <button class="btn btn-outline-danger btn-sm" onclick="document.getElementById('cfo-foto-row-${fotoCount}').remove()">
        <i class="bi bi-trash"></i> Quitar
      </button>
    </div>
  `;
  container.appendChild(div);
}


// ── Generación ──────────────────────────────────────────────────
function setGenStatus(text, color) {
  const el = document.getElementById("gen-status");
  if (el) { el.textContent = text; el.style.color = color || "#555"; }
}

function generarProyecto() {
  const datos = recogerDatos();
  setGenStatus("Generando proyecto...", "#1565c0");

  fetch("/formulario/api/generar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(datos),
  })
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        setGenStatus("Proyecto generado correctamente", "#2e7d32");
      } else {
        setGenStatus("Error: " + (data.error || "desconocido"), "#c62828");
      }
    })
    .catch(err => {
      setGenStatus("Error de conexion", "#c62828");
    });
}

function generarAnexo() {
  const datos = recogerDatos();
  setGenStatus("Generando anexo...", "#1565c0");

  fetch("/formulario/api/generar-anexo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(datos),
  })
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        setGenStatus("Anexo generado correctamente", "#2e7d32");
      } else {
        setGenStatus("Error: " + (data.error || ""), "#c62828");
      }
    })
    .catch(() => setGenStatus("Error de conexion", "#c62828"));
}

function generarCFO() {
  setGenStatus("Generando CFO...", "#1565c0");
  const datos = recogerDatos();
  fetch("/formulario/api/generar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...datos, _tipo: "cfo" }),
  })
    .then(r => r.json())
    .then(data => {
      if (data.ok) setGenStatus("CFO generado", "#2e7d32");
      else setGenStatus("Error: " + (data.error || ""), "#c62828");
    })
    .catch(() => setGenStatus("Error de conexion", "#c62828"));
}

function generarCT() {
  setGenStatus("Generando CT...", "#1565c0");
  const datos = recogerDatos();
  fetch("/formulario/api/generar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...datos, _tipo: "ct" }),
  })
    .then(r => r.json())
    .then(data => {
      if (data.ok) setGenStatus("CT generado", "#2e7d32");
      else setGenStatus("Error: " + (data.error || ""), "#c62828");
    })
    .catch(() => setGenStatus("Error de conexion", "#c62828"));
}
