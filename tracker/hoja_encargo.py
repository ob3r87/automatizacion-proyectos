"""
Generador de Hoja de Encargo (HE) en PDF.
Plantilla básica — se sustituirá por la plantilla real del cliente.
"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generar_hoja_encargo(oferta: dict, cliente: dict, codigo_proyecto: str,
                          pdf_path: str, pdf_settings: dict = None) -> str:
    """
    Genera la Hoja de Encargo en PDF.
    Devuelve la ruta del PDF generado.
    """
    cfg = pdf_settings or {}
    empresa_nombre    = cfg.get("empresa_nombre", "PHICAN INGENIEROS")
    empresa_subtitulo = cfg.get("empresa_subtitulo", "Ingeniería Técnica")
    empresa_dir       = cfg.get("empresa_direccion", "")
    empresa_tel       = cfg.get("empresa_tel", "")
    empresa_email     = cfg.get("empresa_email", "")
    empresa_cif       = cfg.get("empresa_cif", "")

    Path(pdf_path).parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    AZUL   = colors.HexColor("#1565C0")
    GRIS   = colors.HexColor("#F5F5F5")
    OSCURO = colors.HexColor("#212121")

    st_titulo = ParagraphStyle("titulo", fontSize=18, textColor=AZUL,
                                spaceAfter=4, fontName="Helvetica-Bold",
                                alignment=TA_CENTER)
    st_sub    = ParagraphStyle("sub", fontSize=10, textColor=colors.grey,
                                spaceAfter=2, alignment=TA_CENTER)
    st_codigo = ParagraphStyle("codigo", fontSize=13, textColor=AZUL,
                                fontName="Helvetica-Bold", alignment=TA_CENTER,
                                spaceAfter=8)
    st_label  = ParagraphStyle("label", fontSize=8, textColor=colors.grey,
                                fontName="Helvetica-Bold", spaceBefore=0)
    st_valor  = ParagraphStyle("valor", fontSize=10, textColor=OSCURO,
                                fontName="Helvetica", spaceAfter=2)
    st_legal  = ParagraphStyle("legal", fontSize=7.5, textColor=colors.grey,
                                leading=10, spaceAfter=4)
    st_firma  = ParagraphStyle("firma", fontSize=9, alignment=TA_CENTER)

    story = []

    # ── Cabecera empresa ──────────────────────────────────────────────────────
    story.append(Paragraph(empresa_nombre, st_titulo))
    story.append(Paragraph(empresa_subtitulo, st_sub))
    cab_info = []
    if empresa_dir:   cab_info.append(empresa_dir)
    if empresa_tel:   cab_info.append(f"Tel.: {empresa_tel}")
    if empresa_email: cab_info.append(f"Email: {empresa_email}")
    if empresa_cif:   cab_info.append(f"CIF: {empresa_cif}")
    if cab_info:
        story.append(Paragraph("  ·  ".join(cab_info), st_sub))
    story.append(HRFlowable(width="100%", thickness=2, color=AZUL, spaceAfter=10))

    # ── Título del documento ──────────────────────────────────────────────────
    story.append(Paragraph("HOJA DE ENCARGO", st_titulo))
    story.append(Paragraph(f"Código de proyecto: {codigo_proyecto}", st_codigo))
    story.append(Spacer(1, 0.3*cm))

    # ── Datos del proyecto ────────────────────────────────────────────────────
    from datetime import datetime
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    tipo_trabajo = oferta.get("tipo_trabajo", "") or oferta.get("titulo", "")

    datos_proyecto = [
        ["Referencia oferta:", oferta.get("referencia", "-"),
         "Fecha:", fecha_hoy],
        ["Tipo de trabajo:", tipo_trabajo, "", ""],
        ["Descripción:", oferta.get("titulo", ""), "", ""],
    ]

    tabla_proyecto = Table(datos_proyecto, colWidths=[3.5*cm, 7*cm, 2*cm, 4.5*cm])
    tabla_proyecto.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), GRIS),
        ("BACKGROUND", (2, 0), (2, -1), GRIS),
        ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",   (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("PADDING",    (0, 0), (-1, -1), 5),
        ("SPAN",       (1, 1), (3, 1)),
        ("SPAN",       (1, 2), (3, 2)),
    ]))
    story.append(tabla_proyecto)
    story.append(Spacer(1, 0.4*cm))

    # ── Datos del cliente ─────────────────────────────────────────────────────
    story.append(Paragraph("DATOS DEL CLIENTE", ParagraphStyle(
        "sec", fontSize=10, fontName="Helvetica-Bold", textColor=AZUL,
        spaceBefore=6, spaceAfter=4
    )))

    nombre_cliente = cliente.get("nombre", "") or ""
    empresa_cliente = cliente.get("empresa", "") or ""
    nombre_completo = f"{nombre_cliente} ({empresa_cliente})" if empresa_cliente else nombre_cliente

    datos_cliente = [
        ["Nombre / Razón social:", nombre_completo,
         "NIF/CIF:", cliente.get("nif", "-") or "-"],
        ["Dirección:",
         f"{cliente.get('direccion', '')} {cliente.get('ciudad', '')} {cliente.get('cp', '')}".strip(),
         "", ""],
        ["Teléfono:", cliente.get("telefono", "-") or "-",
         "Email:", cliente.get("email", "-") or "-"],
    ]

    tabla_cliente = Table(datos_cliente, colWidths=[3.5*cm, 7*cm, 2*cm, 4.5*cm])
    tabla_cliente.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), GRIS),
        ("BACKGROUND", (2, 0), (2, -1), GRIS),
        ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",   (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("PADDING",    (0, 0), (-1, -1), 5),
        ("SPAN",       (1, 1), (3, 1)),
    ]))
    story.append(tabla_cliente)
    story.append(Spacer(1, 0.4*cm))

    # ── Descripción del encargo ───────────────────────────────────────────────
    story.append(Paragraph("DESCRIPCIÓN DEL ENCARGO", ParagraphStyle(
        "sec2", fontSize=10, fontName="Helvetica-Bold", textColor=AZUL,
        spaceBefore=6, spaceAfter=4
    )))
    descripcion = oferta.get("descripcion", "") or oferta.get("titulo", "") or ""
    notas_cliente = oferta.get("notas_cliente", "") or ""
    texto_encargo = descripcion
    if notas_cliente:
        texto_encargo += f"\n{notas_cliente}"
    if not texto_encargo.strip():
        texto_encargo = "(Sin descripción)"

    tabla_desc = Table(
        [[Paragraph(texto_encargo.replace("\n", "<br/>"), st_valor)]],
        colWidths=[17*cm]
    )
    tabla_desc.setStyle(TableStyle([
        ("BOX",      (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("PADDING",  (0, 0), (-1, -1), 8),
        ("MINROWHEIGHTS", (0, 0), (-1, -1), 2.5*cm),
    ]))
    story.append(tabla_desc)
    story.append(Spacer(1, 0.4*cm))

    # ── Condiciones generales ─────────────────────────────────────────────────
    story.append(Paragraph("CONDICIONES GENERALES", ParagraphStyle(
        "sec3", fontSize=10, fontName="Helvetica-Bold", textColor=AZUL,
        spaceBefore=6, spaceAfter=4
    )))
    condiciones = (
        "1. El cliente encarga a {empresa} la realización de los trabajos descritos anteriormente, "
        "según el presupuesto adjunto, aceptando expresamente las condiciones económicas y técnicas "
        "en él indicadas.\n"
        "2. El inicio de los trabajos quedará condicionado a la firma de este documento y, en su caso, "
        "al abono del anticipo acordado.\n"
        "3. {empresa} se compromete a ejecutar los trabajos con la diligencia debida, respetando los "
        "plazos orientativos indicados en el presupuesto, salvo causas ajenas a su voluntad.\n"
        "4. La documentación técnica generada será propiedad del cliente una vez satisfecho el importe "
        "total de los honorarios.\n"
        "5. Cualquier modificación del alcance del encargo deberá acordarse por escrito y podrá "
        "implicar una revisión del presupuesto."
    ).format(empresa=empresa_nombre)

    story.append(Paragraph(condiciones.replace("\n", "<br/>"), st_legal))
    story.append(Spacer(1, 0.6*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=12))

    # ── Firmas ────────────────────────────────────────────────────────────────
    firmas = Table(
        [[
            Paragraph(
                f"<br/><br/><br/>________________________<br/>"
                f"<b>{empresa_nombre}</b><br/>"
                f"Fecha: _______________",
                st_firma
            ),
            Paragraph(
                f"<br/><br/><br/>________________________<br/>"
                f"<b>El Cliente</b><br/>"
                f"Fecha: _______________",
                st_firma
            ),
        ]],
        colWidths=[8.5*cm, 8.5*cm]
    )
    firmas.setStyle(TableStyle([
        ("VALIGN",  (0, 0), (-1, -1), "BOTTOM"),
        ("ALIGN",   (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(firmas)

    doc.build(story)
    return pdf_path
