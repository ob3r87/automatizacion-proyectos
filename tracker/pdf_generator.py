# -*- coding: utf-8 -*-
"""
Generador de PDFs para presupuestos de Phican Ingenieros.
Requiere reportlab; se auto-instala si falta.
"""
import subprocess
import sys

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether,
    )
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether,
    )

from datetime import datetime, timedelta
from pathlib import Path

# ─── Colores corporativos ────────────────────────────────────────
AZUL_CORP = colors.HexColor("#1565c0")
AZUL_CLARO = colors.HexColor("#e3f2fd")
GRIS_CLARO = colors.HexColor("#f5f5f5")
NEGRO = colors.HexColor("#212121")
GRIS_TEXTO = colors.HexColor("#616161")


def _fmt_date(iso_str):
    """Convierte fecha ISO a formato DD/MM/YYYY."""
    if not iso_str:
        return ""
    try:
        d = datetime.fromisoformat(iso_str[:10])
        return d.strftime("%d/%m/%Y")
    except Exception:
        return iso_str


def _fmt_euro(valor):
    """Formatea valor monetario."""
    try:
        return f"{float(valor):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00 €"


def generar_pdf_oferta(offer_data: dict, lines_data: list, client_data: dict, output_path: str) -> str:
    """
    Genera un PDF de presupuesto profesional.

    Args:
        offer_data: Diccionario con datos de la oferta.
        lines_data: Lista de dicts con las líneas del presupuesto.
        client_data: Diccionario con datos del cliente.
        output_path: Ruta donde guardar el PDF.

    Returns:
        Ruta del PDF generado.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # Estilos personalizados
    st_titulo_empresa = ParagraphStyle(
        "TituloEmpresa",
        parent=styles["Normal"],
        fontSize=22,
        textColor=AZUL_CORP,
        fontName="Helvetica-Bold",
        spaceAfter=2,
    )
    st_subtitulo_empresa = ParagraphStyle(
        "SubtituloEmpresa",
        parent=styles["Normal"],
        fontSize=10,
        textColor=GRIS_TEXTO,
        fontName="Helvetica",
        spaceAfter=1,
    )
    st_datos_empresa = ParagraphStyle(
        "DatosEmpresa",
        parent=styles["Normal"],
        fontSize=8,
        textColor=GRIS_TEXTO,
        fontName="Helvetica",
    )
    st_seccion = ParagraphStyle(
        "Seccion",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.white,
        fontName="Helvetica-Bold",
        backColor=AZUL_CORP,
        leftIndent=4,
        spaceBefore=6,
        spaceAfter=4,
    )
    st_normal = ParagraphStyle(
        "NormalCustom",
        parent=styles["Normal"],
        fontSize=9,
        textColor=NEGRO,
        fontName="Helvetica",
        leading=13,
    )
    st_negrita = ParagraphStyle(
        "NegritaCustom",
        parent=styles["Normal"],
        fontSize=9,
        textColor=NEGRO,
        fontName="Helvetica-Bold",
    )
    st_pie = ParagraphStyle(
        "Pie",
        parent=styles["Normal"],
        fontSize=8,
        textColor=GRIS_TEXTO,
        fontName="Helvetica-Oblique",
        alignment=TA_CENTER,
    )
    st_notas = ParagraphStyle(
        "Notas",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=NEGRO,
        fontName="Helvetica",
        leading=13,
        leftIndent=6,
    )

    story = []

    # ── CABECERA ──────────────────────────────────────────────────
    logo_cell = [
        Paragraph("PHICAN INGENIEROS", st_titulo_empresa),
        Paragraph("Ingeniería Técnica", st_subtitulo_empresa),
        Paragraph(
            "C/ Ejemplo 1, Santa Úrsula, S/C de Tenerife<br/>"
            "Tel: 922 000 000 | phican@phican.es | CIF: B00000000",
            st_datos_empresa,
        ),
    ]

    ref = offer_data.get("referencia", "")
    fecha_creacion = _fmt_date(offer_data.get("fecha_creacion", ""))
    validez_dias = int(offer_data.get("validez_dias", 30))
    fecha_venc = offer_data.get("fecha_vencimiento", "")
    if not fecha_venc and offer_data.get("fecha_creacion"):
        try:
            d_ini = datetime.fromisoformat(offer_data["fecha_creacion"][:10])
            fecha_venc = (d_ini + timedelta(days=validez_dias)).isoformat()
        except Exception:
            fecha_venc = ""

    doc_cell = [
        Paragraph("PRESUPUESTO", ParagraphStyle(
            "DocType", parent=styles["Normal"],
            fontSize=18, textColor=AZUL_CORP, fontName="Helvetica-Bold",
            alignment=TA_RIGHT,
        )),
        Spacer(1, 4),
        Paragraph(f"<b>Referencia:</b> {ref}", ParagraphStyle(
            "RefStyle", parent=styles["Normal"],
            fontSize=9, fontName="Helvetica", alignment=TA_RIGHT,
        )),
        Paragraph(f"<b>Fecha:</b> {fecha_creacion}", ParagraphStyle(
            "FechaStyle", parent=styles["Normal"],
            fontSize=9, fontName="Helvetica", alignment=TA_RIGHT,
        )),
        Paragraph(f"<b>Válido hasta:</b> {_fmt_date(fecha_venc)}", ParagraphStyle(
            "ValidStyle", parent=styles["Normal"],
            fontSize=9, fontName="Helvetica", alignment=TA_RIGHT,
        )),
    ]

    header_table = Table(
        [[logo_cell, doc_cell]],
        colWidths=[10 * cm, 7 * cm],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=AZUL_CORP))
    story.append(Spacer(1, 0.4 * cm))

    # ── BLOQUE CLIENTE ────────────────────────────────────────────
    nombre_cliente = client_data.get("nombre", "")
    empresa_cliente = client_data.get("empresa", "")
    nif_cliente = client_data.get("nif", "")
    dir_cliente = client_data.get("direccion", "")
    ciudad_cliente = client_data.get("ciudad", "")
    cp_cliente = client_data.get("cp", "")
    email_cliente = client_data.get("email", "")
    tel_cliente = client_data.get("telefono", "")

    dir_completa = " ".join(filter(None, [dir_cliente, cp_cliente, ciudad_cliente]))

    cliente_rows = []
    if nombre_cliente:
        cliente_rows.append([Paragraph(f"<b>Cliente:</b>", st_normal), Paragraph(nombre_cliente, st_negrita)])
    if empresa_cliente:
        cliente_rows.append([Paragraph("<b>Empresa:</b>", st_normal), Paragraph(empresa_cliente, st_normal)])
    if nif_cliente:
        cliente_rows.append([Paragraph("<b>NIF/CIF:</b>", st_normal), Paragraph(nif_cliente, st_normal)])
    if dir_completa:
        cliente_rows.append([Paragraph("<b>Dirección:</b>", st_normal), Paragraph(dir_completa, st_normal)])
    if email_cliente:
        cliente_rows.append([Paragraph("<b>Email:</b>", st_normal), Paragraph(email_cliente, st_normal)])
    if tel_cliente:
        cliente_rows.append([Paragraph("<b>Teléfono:</b>", st_normal), Paragraph(tel_cliente, st_normal)])

    if cliente_rows:
        story.append(Paragraph("DATOS DEL CLIENTE", st_seccion))
        cliente_table = Table(cliente_rows, colWidths=[3.5 * cm, 13.5 * cm])
        cliente_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, GRIS_CLARO]),
        ]))
        story.append(cliente_table)
        story.append(Spacer(1, 0.3 * cm))

    # ── DATOS OFERTA ──────────────────────────────────────────────
    titulo = offer_data.get("titulo", "")
    tipo_trabajo = offer_data.get("tipo_trabajo", "")
    descripcion = offer_data.get("descripcion", "")

    story.append(Paragraph("OBJETO DEL PRESUPUESTO", st_seccion))
    oferta_rows = []
    if titulo:
        oferta_rows.append([Paragraph("<b>Objeto:</b>", st_normal), Paragraph(titulo, st_negrita)])
    if tipo_trabajo:
        oferta_rows.append([Paragraph("<b>Tipo:</b>", st_normal), Paragraph(tipo_trabajo, st_normal)])
    if descripcion:
        oferta_rows.append([Paragraph("<b>Descripción:</b>", st_normal), Paragraph(descripcion, st_normal)])

    if oferta_rows:
        oferta_table = Table(oferta_rows, colWidths=[3.5 * cm, 13.5 * cm])
        oferta_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(oferta_table)
    story.append(Spacer(1, 0.3 * cm))

    # ── TABLA DE LÍNEAS ───────────────────────────────────────────
    story.append(Paragraph("DESGLOSE DE PARTIDAS", st_seccion))

    st_th = ParagraphStyle("TH", parent=styles["Normal"],
                            fontSize=8.5, textColor=colors.white,
                            fontName="Helvetica-Bold", alignment=TA_CENTER)
    st_td = ParagraphStyle("TD", parent=styles["Normal"],
                            fontSize=8.5, textColor=NEGRO, fontName="Helvetica")
    st_td_right = ParagraphStyle("TDR", parent=styles["Normal"],
                                  fontSize=8.5, textColor=NEGRO,
                                  fontName="Helvetica", alignment=TA_RIGHT)
    st_td_center = ParagraphStyle("TDC", parent=styles["Normal"],
                                   fontSize=8.5, textColor=NEGRO,
                                   fontName="Helvetica", alignment=TA_CENTER)

    lines_header = [
        Paragraph("Concepto", st_th),
        Paragraph("Descripción", st_th),
        Paragraph("Cant.", st_th),
        Paragraph("Precio unit.", st_th),
        Paragraph("Total", st_th),
    ]
    lines_rows = [lines_header]

    for line in lines_data:
        concepto = line.get("concepto", "")
        desc = line.get("descripcion", "")
        cantidad = float(line.get("cantidad", 1))
        precio = float(line.get("precio_unitario", 0))
        total_linea = cantidad * precio
        lines_rows.append([
            Paragraph(concepto, st_td),
            Paragraph(desc, st_td),
            Paragraph(f"{cantidad:g}", st_td_center),
            Paragraph(_fmt_euro(precio), st_td_right),
            Paragraph(_fmt_euro(total_linea), st_td_right),
        ])

    lines_table = Table(
        lines_rows,
        colWidths=[4 * cm, 6.5 * cm, 1.5 * cm, 2.5 * cm, 2.5 * cm],
        repeatRows=1,
    )
    lines_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_CORP),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (1, -1), "LEFT"),
        ("ALIGN", (2, 1), (2, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, AZUL_CLARO]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(lines_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── TOTALES ───────────────────────────────────────────────────
    subtotal = sum(float(l.get("cantidad", 1)) * float(l.get("precio_unitario", 0)) for l in lines_data)
    descuento_pct = float(offer_data.get("descuento_pct", 0))
    iva_pct = float(offer_data.get("iva_pct", 7))

    descuento_importe = subtotal * descuento_pct / 100
    base_imponible = subtotal - descuento_importe
    iva_importe = base_imponible * iva_pct / 100
    total_final = base_imponible + iva_importe

    st_tot_label = ParagraphStyle("TotLabel", parent=styles["Normal"],
                                   fontSize=9, fontName="Helvetica", alignment=TA_RIGHT)
    st_tot_value = ParagraphStyle("TotValue", parent=styles["Normal"],
                                   fontSize=9, fontName="Helvetica-Bold", alignment=TA_RIGHT)
    st_tot_total_label = ParagraphStyle("TotTotalLabel", parent=styles["Normal"],
                                         fontSize=11, fontName="Helvetica-Bold",
                                         textColor=colors.white, alignment=TA_RIGHT)
    st_tot_total_value = ParagraphStyle("TotTotalValue", parent=styles["Normal"],
                                         fontSize=11, fontName="Helvetica-Bold",
                                         textColor=colors.white, alignment=TA_RIGHT)

    totales_rows = [
        [Paragraph("Subtotal:", st_tot_label), Paragraph(_fmt_euro(subtotal), st_tot_value)],
    ]
    if descuento_pct > 0:
        totales_rows.append([
            Paragraph(f"Descuento ({descuento_pct:g}%):", st_tot_label),
            Paragraph(f"- {_fmt_euro(descuento_importe)}", st_tot_value),
        ])
        totales_rows.append([
            Paragraph("Base imponible:", st_tot_label),
            Paragraph(_fmt_euro(base_imponible), st_tot_value),
        ])
    totales_rows.append([
        Paragraph(f"IGIC ({iva_pct:g}%):", st_tot_label),
        Paragraph(_fmt_euro(iva_importe), st_tot_value),
    ])
    totales_rows.append([
        Paragraph("TOTAL:", st_tot_total_label),
        Paragraph(_fmt_euro(total_final), st_tot_total_value),
    ])

    n_rows = len(totales_rows)
    totales_table = Table(totales_rows, colWidths=[12 * cm, 5 * cm], hAlign="RIGHT")
    style_totales = [
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEABOVE", (0, n_rows - 1), (-1, n_rows - 1), 1.5, AZUL_CORP),
        ("BACKGROUND", (0, n_rows - 1), (-1, n_rows - 1), AZUL_CORP),
    ]
    totales_table.setStyle(TableStyle(style_totales))
    story.append(totales_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── NOTAS PARA EL CLIENTE ─────────────────────────────────────
    notas_cliente = offer_data.get("notas_cliente", "")
    if notas_cliente:
        story.append(Paragraph("CONDICIONES Y NOTAS", st_seccion))
        story.append(Paragraph(notas_cliente, st_notas))
        story.append(Spacer(1, 0.3 * cm))

    # ── PIE ───────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=AZUL_CORP))
    story.append(Spacer(1, 0.2 * cm))

    fecha_valido = _fmt_date(fecha_venc) if fecha_venc else f"{validez_dias} días desde la fecha de emisión"
    story.append(Paragraph(
        f"Presupuesto válido hasta {fecha_valido}. "
        "Forma de pago: 50% a la firma, 50% a la entrega.",
        st_pie,
    ))
    story.append(Paragraph(
        "Phican Ingenieros — C/ Ejemplo 1, Santa Úrsula, 38390 S/C de Tenerife — "
        "Tel: 922 000 000 — phican@phican.es",
        st_pie,
    ))

    doc.build(story)
    return output_path
