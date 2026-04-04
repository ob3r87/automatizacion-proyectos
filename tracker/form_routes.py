# -*- coding: utf-8 -*-
"""
Blueprint del Formulario de Proyectos — versión webapp.
Reemplaza formulario.py (tkinter) con interfaz web.
"""
import base64
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from flask import (Blueprint, render_template, request, jsonify,
                   current_app, redirect, url_for, flash)

from config import PROJECT_ROOT, load_config, save_config
from db import (buscar_vehiculo, guardar_vehiculo, buscar_vehiculos_por_texto,
                init_vehiculos_db)

form_bp = Blueprint("form", __name__, url_prefix="/formulario")

# ── Datos estáticos (migrados de formulario.py) ─────────────────────────────

CATEGORIAS_VEHICULO = [
    "M1 — Turismos (hasta 8 plazas)",
    "M2 — Microbuses (>8 plazas, <=5 000 kg)",
    "M3 — Autobuses (>8 plazas, >5 000 kg)",
    "N1 — Vehiculos de carga ligeros (<=3 500 kg)",
    "N2 — Vehiculos de carga medios (3 500-12 000 kg)",
    "N3 — Vehiculos de carga pesados (>12 000 kg)",
    "O1 — Remolques ligeros (<=750 kg)",
    "O2 — Remolques medios (750-3 500 kg)",
    "O3 — Remolques pesados (3 500-10 000 kg)",
    "O4 — Remolques muy pesados (>10 000 kg)",
    "L1e — Ciclomotor de 2 ruedas",
    "L2e — Ciclomotor de 3 ruedas",
    "L3e — Motocicleta de 2 ruedas",
    "L4e — Motocicleta con sidecar",
    "L5e — Triciclo a motor",
    "L6e — Cuadriciclo ligero",
    "L7e — Cuadriciclo pesado",
    "T — Tractor agricola",
]

USOS_VEHICULO = [
    "Transporte de personas",
    "Transporte de mercancias",
    "Uso mixto (personas y carga)",
    "Servicio publico de viajeros",
    "Emergencias / Servicios especiales",
    "Agricola / Forestal",
    "Obra / Construccion",
    "Otro",
]

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}


def _siguiente_referencia():
    """Calcula la siguiente referencia PH.NNN-YYYY."""
    output_dir = PROJECT_ROOT / "proyectos_generados"
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    ahora = datetime.now()
    anio = ahora.year
    maximo = 0
    for d in output_dir.iterdir():
        if d.is_dir() and d.name.startswith("PH."):
            import re
            m = re.match(r"PH\.(\d+)-(\d{4})", d.name)
            if m and int(m.group(2)) == anio:
                maximo = max(maximo, int(m.group(1)))
    num = maximo + 1
    return f"PH.{num:03d}/{anio}-0"


def _mes_anio_hoy():
    ahora = datetime.now()
    return f"{MESES_ES[ahora.month].upper()} {ahora.year}"


def _fecha_hoy():
    ahora = datetime.now()
    return f"{ahora.day} de {MESES_ES[ahora.month]} de {ahora.year}"


# ── Códigos de reforma (cargar desde JSON o formulario.py) ──────────────────

def _load_codigos_reforma():
    """Carga los códigos de reforma desde codigos_reforma.json o genera desde formulario.py."""
    json_path = Path(__file__).parent / "codigos_reforma.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Intentar importar desde formulario.py
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from formulario import CODIGOS_REFORMA_V7
        return {k: list(v) for k, v in CODIGOS_REFORMA_V7.items()}
    except Exception:
        return {}


# ── Rutas de página ─────────────────────────────────────────────────────────

@form_bp.route("/nuevo")
def nuevo_proyecto():
    """Página principal del formulario de nuevo proyecto."""
    cfg = load_config()
    codigos = _load_codigos_reforma()
    return render_template(
        "form_proyecto.html",
        categorias=CATEGORIAS_VEHICULO,
        usos=USOS_VEHICULO,
        codigos_reforma=codigos,
        config=cfg,
        ref_default=_siguiente_referencia(),
        mes_anio=_mes_anio_hoy(),
        fecha_firma=_fecha_hoy(),
    )


# ── API: Vehículos (BD local) ──────────────────────────────────────────────

@form_bp.route("/api/vehiculo/buscar", methods=["GET"])
def api_buscar_vehiculo():
    """Busca vehículo por matrícula o bastidor en la BD local."""
    mat = request.args.get("matricula", "").strip()
    bas = request.args.get("bastidor", "").strip()
    texto = request.args.get("q", "").strip()

    if texto:
        resultados = buscar_vehiculos_por_texto(texto)
        return jsonify({"resultados": resultados})

    if not mat and not bas:
        return jsonify({"error": "Indica matricula o bastidor"}), 400

    veh = buscar_vehiculo(matricula=mat, bastidor=bas)
    if veh:
        return jsonify({"vehiculo": veh})
    return jsonify({"vehiculo": None}), 404


@form_bp.route("/api/vehiculo/guardar", methods=["POST"])
def api_guardar_vehiculo():
    """Guarda datos de vehículo en la BD local."""
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "Datos vacios"}), 400
    guardar_vehiculo(datos)
    return jsonify({"ok": True}), 201


# ── API: Ficha técnica con Vision (Gemini / Anthropic) ───────────────────────

_VISION_PROMPT = (
    "Analiza esta ficha tecnica (tarjeta ITV) de un vehiculo espanol. "
    "Extrae los datos y devuelve SOLO un JSON con estas claves exactas. "
    "Valores numericos sin unidades. Si no encuentras un dato pon \"\".\n\n"
    "CLAVES EXACTAS (no cambiar los nombres):\n"
    "MARCA, MODELO, TIPO_VEHICULO, VERSION_VEHICULO, "
    "NUM_BASTIDOR, MATRICULA, N_HOMOLOGACION, "
    "DISTANCIA_EJES, LONGITUD_VEH, ANCHURA_VEH, ALTURA_VEH, VOLADIZO_A, "
    "TARA_VEHICULO_KG, "
    "MMA, MMA_EJE1, MMA_EJE2, MMTA, MMTC, "
    "MMTA_EJE_A, MMA_EJE_A, "
    "PLAZAS_A, VEL_MAX_A, CILINDRADA_A, POT_NETA_A, "
    "COMBUSTIBLE_A, EMISIONES_A, CO2_A, POT_FISCAL_A, "
    "CARROCERIA_A, NUM_EJES, VIAS_EJES_A, SUSPENSION_A, DIRECCION_A, "
    "FRENADO_A, FABR_BASE_A, FABR_MOTOR_A, COD_MOTOR_A, RUIDO_A, "
    "CATEGORIA_DGT\n\n"
    "NOTAS para la ficha ITV espanola:\n"
    "- N_HOMOLOGACION = contrasena/numero de homologacion (ej: e3*2007/46*0044*14)\n"
    "- DISTANCIA_EJES = distancia entre ejes en mm (suele ser ~2500-4500)\n"
    "- LONGITUD_VEH = longitud total en mm (siempre mayor que distancia ejes, ~3500-7000)\n"
    "- ANCHURA_VEH = anchura en mm (~1500-2200)\n"
    "- ALTURA_VEH = altura en mm (~1400-3000)\n"
    "- TARA_VEHICULO_KG = masa en orden de marcha en kg\n"
    "- MMA = masa maxima autorizada kg\n"
    "- CATEGORIA_DGT = M1, M2, N1, N2, etc.\n"
    "- COMBUSTIBLE_A = gasolina/diesel/electrico/hibrido\n\n"
    "SOLO JSON, sin markdown ni explicaciones."
)


def _vision_log(msg):
    """Log a archivo para debug (los print no aparecen con start_web.py)."""
    try:
        with open("vision_debug.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def _repair_truncated_json(texto):
    """Intenta reparar un JSON truncado por Gemini (respuesta cortada).
    Devuelve dict o None si no se puede reparar."""
    import re
    texto = texto.strip()
    if not texto.startswith("{"):
        return None

    # Estrategia 1: truncar en la última clave:valor completa y cerrar
    # Buscar la última línea completa tipo "KEY": VALUE,
    lines = texto.split("\n")
    repaired = []
    for line in lines:
        repaired.append(line)
        stripped = line.strip()
        # Si la línea termina en coma o es un valor completo, es segura
        if stripped.endswith(",") or stripped.endswith("{") or stripped == "}":
            continue
        # Si es una línea de clave:valor sin coma al final (última línea válida)
        if ":" in stripped and (stripped.endswith('"') or stripped.endswith("0") or
           stripped.endswith("1") or stripped.endswith("2") or stripped.endswith("3") or
           stripped.endswith("4") or stripped.endswith("5") or stripped.endswith("6") or
           stripped.endswith("7") or stripped.endswith("8") or stripped.endswith("9")):
            continue

    # Ir eliminando líneas del final hasta que podamos parsear
    for i in range(len(repaired), 0, -1):
        attempt = "\n".join(repaired[:i]).rstrip().rstrip(",")
        # Cerrar el JSON
        if not attempt.endswith("}"):
            attempt += "\n}"
        try:
            result = json.loads(attempt)
            _vision_log(f"Reparacion exitosa cortando en linea {i}/{len(repaired)}")
            return result
        except json.JSONDecodeError:
            continue

    # Estrategia 2: regex para extraer pares key:value individualmente
    campos = {}
    for m in re.finditer(r'"(\w+)"\s*:\s*(".*?"|[\d.]+|\[\])', texto):
        key = m.group(1)
        val = m.group(2)
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        else:
            try:
                val = int(val) if "." not in val else float(val)
            except ValueError:
                pass
        campos[key] = val

    if campos:
        _vision_log(f"Reparacion por regex: {len(campos)} campos extraidos")
        return campos

    return None


def _vision_gemini(b64, media_type, api_key):
    """Llama a Gemini Vision API (gratis hasta 15 req/min)."""
    import httpx
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": media_type, "data": b64}},
                {"text": _VISION_PROMPT},
            ]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 8192,
            "responseMimeType": "application/json",
        }
    }
    _vision_log(f"Gemini request: media={media_type}, b64_len={len(b64)}")
    resp = httpx.post(url, json=payload, timeout=120.0)
    _vision_log(f"Gemini response status: {resp.status_code}")

    if resp.status_code != 200:
        err_text = resp.text[:500]
        _vision_log(f"Gemini error: {err_text}")
        return None, f"Error Gemini API: {resp.status_code} - {err_text}"

    data = resp.json()
    try:
        texto = data["candidates"][0]["content"]["parts"][0]["text"]
        _vision_log(f"Gemini texto OK (len={len(texto)}): {repr(texto[:200])}")
    except (KeyError, IndexError):
        dump = json.dumps(data)[:500]
        _vision_log(f"Gemini respuesta inesperada: {dump}")
        return None, f"Respuesta inesperada de Gemini: {dump}"
    return texto, None


def _vision_anthropic(b64, media_type, api_key):
    """Llama a Claude Vision API."""
    import httpx
    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2000,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64",
                     "media_type": media_type, "data": b64}},
                    {"type": "text", "text": _VISION_PROMPT},
                ],
            }],
        },
        timeout=60.0,
    )
    if resp.status_code != 200:
        return None, f"Error Anthropic API: {resp.status_code} - {resp.text}"

    data = resp.json()
    texto = data.get("content", [{}])[0].get("text", "")
    return texto, None


@form_bp.route("/api/ficha-vision", methods=["POST"])
def api_ficha_vision():
    """Recibe imagen de ficha técnica, la envía a Vision AI y devuelve campos."""
    import traceback
    try:
        return _do_ficha_vision()
    except Exception as e:
        tb = traceback.format_exc()
        # Log a archivo para debug
        with open("vision_error.log", "w", encoding="utf-8") as f:
            f.write(tb)
        return jsonify({"error": f"Excepcion: {type(e).__name__}: {e}", "traceback": tb}), 500

def _do_ficha_vision():
    import re
    cfg = load_config()

    # Determinar proveedor: Gemini (preferido, gratis) o Anthropic
    gemini_key = cfg.get("GEMINI_API_KEY", "").strip()
    anthropic_key = cfg.get("ANTHROPIC_API_KEY", "").strip()

    if not gemini_key and not anthropic_key:
        return jsonify({
            "error": "API Key no configurada. Necesitas una GEMINI_API_KEY (gratis) o ANTHROPIC_API_KEY.",
            "need_key": True
        }), 400

    if "imagen" not in request.files:
        return jsonify({"error": "No se envio imagen"}), 400

    file = request.files["imagen"]
    image_data = file.read()

    if not image_data or len(image_data) < 100:
        return jsonify({"error": f"Imagen vacia o corrupta (size={len(image_data)})"}), 400

    _vision_log(f"Imagen recibida: filename={file.filename}, content_type={file.content_type}, size={len(image_data)} bytes")

    # --- Redimensionar si la imagen es muy grande (>4MB) para evitar timeouts ---
    if len(image_data) > 4 * 1024 * 1024:
        _vision_log(f"Imagen grande ({len(image_data)} bytes), intentando comprimir...")
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(image_data))
            # Reducir a max 2000px lado largo
            max_side = 2000
            if max(img.size) > max_side:
                ratio = max_side / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            image_data = buf.getvalue()
            _vision_log(f"Imagen comprimida a {len(image_data)} bytes")
        except ImportError:
            _vision_log("Pillow no instalado, enviando imagen original")
        except Exception as e:
            _vision_log(f"Error comprimiendo: {e}")

    b64 = base64.b64encode(image_data).decode("utf-8")

    # Media type: preferir content_type del navegador, fallback a extensión
    media_type = file.content_type if file.content_type and file.content_type.startswith("image/") else None
    if not media_type:
        ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "jpg"
        media_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                     "png": "image/png", "webp": "image/webp", "bmp": "image/bmp",
                     "heic": "image/heic", "heif": "image/heif"}
        media_type = media_map.get(ext, "image/jpeg")

    _vision_log(f"Media type: {media_type}, b64 length: {len(b64)}")

    try:
        import httpx
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
        import httpx

    # Intentar Gemini primero, luego Anthropic
    texto, error = None, None
    provider = None
    if gemini_key:
        texto, error = _vision_gemini(b64, media_type, gemini_key)
        provider = "Gemini"
    if (not texto or error) and anthropic_key:
        prev_error = error
        texto, error = _vision_anthropic(b64, media_type, anthropic_key)
        provider = "Anthropic"
        if error and prev_error:
            error = f"Gemini: {prev_error} | Anthropic: {error}"

    if error:
        _vision_log(f"Error final: {error}")
        return jsonify({"error": error}), 502
    if not texto:
        return jsonify({"error": "No se obtuvo respuesta del servicio Vision"}), 502

    # Limpiar markdown y extraer JSON
    _vision_log(f"Texto raw (500): {repr(texto[:500])}")
    texto = texto.strip()

    # Extraer bloque ```json ... ``` o ``` ... ```
    md_match = re.search(r'```(?:json)?\s*\n?(.*?)```', texto, re.DOTALL)
    if md_match:
        texto = md_match.group(1).strip()

    # Si aún no empieza con {, buscar el primer { y último }
    if not texto.startswith("{"):
        idx_start = texto.find("{")
        idx_end = texto.rfind("}")
        if idx_start >= 0 and idx_end > idx_start:
            texto = texto[idx_start:idx_end + 1]

    _vision_log(f"Texto limpio (500): {repr(texto[:500])}")

    try:
        campos = json.loads(texto)
    except json.JSONDecodeError as e:
        _vision_log(f"JSON parse error: {e}")
        _vision_log(f"Texto completo: {repr(texto)}")
        # Intentar reparar JSON truncado (Gemini a veces corta la respuesta)
        campos = _repair_truncated_json(texto)
        if campos is None:
            return jsonify({
                "error": f"No se pudo parsear la respuesta ({provider}): {str(e)[:100]}",
                "raw": texto[:800]
            }), 500
        _vision_log(f"JSON reparado OK! {len(campos)} campos")

    # Normalizar claves: quitar unidades entre paréntesis que Gemini pueda añadir
    # Ej: "DISTANCIA_EJES(mm)" → "DISTANCIA_EJES"
    normalized = {}
    for k, v in campos.items():
        clean_key = re.sub(r'\(.*?\)$', '', k).strip()
        normalized[clean_key] = v
    campos = normalized

    # PARTE_FIJA_VIN = siempre los 9 primeros caracteres del NUM_BASTIDOR
    bastidor = str(campos.get("NUM_BASTIDOR", "")).strip()
    if bastidor and len(bastidor) >= 9:
        campos["PARTE_FIJA_VIN"] = bastidor[:9]

    _vision_log(f"OK! {len(campos)} campos extraidos via {provider}: {list(campos.keys())}")
    return jsonify({"campos": campos, "provider": provider})


# ── API: Generar proyecto ───────────────────────────────────────────────────

@form_bp.route("/api/generar", methods=["POST"])
def api_generar_proyecto():
    """Genera el proyecto llamando a generar_proyecto.py con los datos del formulario."""
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "Datos vacios"}), 400

    # Guardar datos temporales
    tmp_path = PROJECT_ROOT / "tmp_generacion" / "datos_web.json"
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    # Guardar vehículo en BD
    try:
        guardar_vehiculo(datos)
    except Exception:
        pass

    # Ejecutar generar_proyecto.py
    script = PROJECT_ROOT / "generar_proyecto.py"
    if not script.exists():
        return jsonify({"error": "generar_proyecto.py no encontrado"}), 404

    try:
        result = subprocess.run(
            [sys.executable, str(script), "--json", str(tmp_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            return jsonify({"error": result.stderr or "Error en la generacion",
                            "stdout": result.stdout}), 500
        return jsonify({"ok": True, "output": result.stdout})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout al generar proyecto"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@form_bp.route("/api/generar-anexo", methods=["POST"])
def api_generar_anexo():
    """Genera el anexo de cálculo."""
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "Datos vacios"}), 400

    tmp_path = PROJECT_ROOT / "tmp_generacion" / "datos_anexo_web.json"
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    script = PROJECT_ROOT / "generar_anexo.py"
    if not script.exists():
        return jsonify({"error": "generar_anexo.py no encontrado"}), 404

    try:
        result = subprocess.run(
            [sys.executable, str(script), "--json", str(tmp_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            return jsonify({"error": result.stderr or "Error generando anexo",
                            "stdout": result.stdout}), 500
        return jsonify({"ok": True, "output": result.stdout})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── API: Configuración ──────────────────────────────────────────────────────

@form_bp.route("/api/config", methods=["GET"])
def api_get_config():
    """Devuelve la configuración actual."""
    cfg = load_config()
    # Ocultar API key parcialmente
    if "ANTHROPIC_API_KEY" in cfg and cfg["ANTHROPIC_API_KEY"]:
        key = cfg["ANTHROPIC_API_KEY"]
        cfg["ANTHROPIC_API_KEY_MASKED"] = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
    return jsonify(cfg)


@form_bp.route("/api/config", methods=["POST"])
def api_save_config():
    """Guarda configuración."""
    datos = request.get_json()
    save_config(datos)
    return jsonify({"ok": True})
