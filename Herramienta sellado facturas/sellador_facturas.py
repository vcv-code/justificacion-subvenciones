#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sellador de facturas PDF
=========================
Programa sencillo (con interfaz gráfica) para estampar en cada factura PDF el
texto exigido por una subvención ("ESTA FACTURA ESTA SUBVENCIONADA POR...",
o el que corresponda a tu convocatoria/ayuntamiento), en la posición que
elijas, sin tocar los PDF originales (crea copias nuevas en una carpeta de
salida).

Pensado para que lo use cualquier persona sin conocimientos de programación:
se ejecuta y aparece una ventana.

Opcionalmente añade también una imagen (el sello/logo de tu asociación) junto
al texto, y puede buscar sola un hueco libre de la factura para no tapar nada.

Requisitos (una sola vez):
    pip install -r requirements.txt   (desde la carpeta raíz del proyecto)

Ejecutar:
    python sellador_facturas.py
"""

import io
import os
import sys
import traceback
from dataclasses import dataclass, replace
from functools import lru_cache

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("Falta la librería 'pypdf'. Instala con:  pip install pypdf")
    sys.exit(1)

try:
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.colors import Color
    from reportlab.lib.utils import ImageReader
except ImportError:
    print("Falta la librería 'reportlab'. Instala con:  pip install reportlab")
    sys.exit(1)

try:
    import numpy as np
    import pymupdf
    from PIL import Image
except ImportError:
    print("Faltan librerías. Instala con:  pip install -r requirements.txt")
    sys.exit(1)

MM = 72.0 / 25.4  # puntos por milímetro (reportlab/pypdf usan puntos: 72pt = 1 pulgada)

POS_AUTO = "Automática (buscar hueco libre)"

POSICIONES = [
    POS_AUTO,
    "Abajo derecha",
    "Abajo centro",
    "Abajo izquierda",
    "Arriba derecha",
    "Arriba centro",
    "Arriba izquierda",
    "Centro",
]

COLORES = {
    "Negro": (0.0, 0.0, 0.0),
    "Rojo (típico de sello)": (0.75, 0.0, 0.0),
    "Azul": (0.0, 0.15, 0.55),
}

SEPARACION_LOGO_MM = 3.0  # hueco entre la imagen del sello y el recuadro de texto


# --------------------------------------------------------------------------
# Núcleo: estampar un PDF
# --------------------------------------------------------------------------

def _wrap_text_por_ancho(c, texto, fuente, tam_fuente, ancho_max_pt):
    """Parte el texto en líneas que quepan en ancho_max_pt, respetando saltos
    de línea que el usuario haya escrito a mano."""
    lineas_final = []
    for parrafo in texto.split("\n"):
        palabras = parrafo.split(" ")
        linea_actual = ""
        for palabra in palabras:
            prueba = (linea_actual + " " + palabra).strip()
            if c.stringWidth(prueba, fuente, tam_fuente) <= ancho_max_pt or not linea_actual:
                linea_actual = prueba
            else:
                lineas_final.append(linea_actual)
                linea_actual = palabra
        lineas_final.append(linea_actual)
    return lineas_final


def _calcular_posicion(pos_nombre, page_w, page_h, box_w, box_h, margen_pt):
    """Devuelve (x, y) de la esquina inferior-izquierda del recuadro del
    sello, según el nombre de posición elegido."""
    if pos_nombre == "Abajo derecha":
        x = page_w - box_w - margen_pt
        y = margen_pt
    elif pos_nombre == "Abajo centro":
        x = (page_w - box_w) / 2
        y = margen_pt
    elif pos_nombre == "Abajo izquierda":
        x = margen_pt
        y = margen_pt
    elif pos_nombre == "Arriba derecha":
        x = page_w - box_w - margen_pt
        y = page_h - box_h - margen_pt
    elif pos_nombre == "Arriba centro":
        x = (page_w - box_w) / 2
        y = page_h - box_h - margen_pt
    elif pos_nombre == "Arriba izquierda":
        x = margen_pt
        y = page_h - box_h - margen_pt
    elif pos_nombre == "Centro":
        x = (page_w - box_w) / 2
        y = (page_h - box_h) / 2
    else:
        x = page_w - box_w - margen_pt
        y = margen_pt
    # que nunca se salga de la página
    x = max(margen_pt * 0.3, min(x, page_w - box_w - margen_pt * 0.3))
    y = max(margen_pt * 0.3, min(y, page_h - box_h - margen_pt * 0.3))
    return x, y


@dataclass
class OpcionesSello:
    texto: str
    posicion: str = POS_AUTO
    tam_fuente: float = 9.0
    color_rgb: tuple = (0.0, 0.0, 0.0)
    margen_mm: float = 8.0
    ancho_caja_mm: float = 70.0
    todas_paginas: bool = False
    con_recuadro: bool = True
    x_manual_mm: float = None  # si se rellena, ignora 'posicion' y usa esta X (desde borde izq.)
    y_manual_mm: float = None  # idem para Y (desde borde inferior)
    logo_ruta: str = None      # imagen opcional (sello/logo) que se pone junto al texto
    logo_alto_mm: float = 26.0


# --------------------------------------------------------------------------
# Imagen del sello (logo)
# --------------------------------------------------------------------------

@lru_cache(maxsize=8)
def _cargar_logo(ruta):
    """Carga la imagen y vuelve transparente su fondo blanco, para que se vea
    como tinta estampada y no tape lo que haya debajo. Devuelve
    (ImageReader, ancho/alto)."""
    rgb = np.asarray(Image.open(ruta).convert("RGB")).astype(np.float32)
    # opacidad = lo lejos que está cada píxel del blanco (blanco -> transparente)
    alpha = 255.0 - rgb.min(axis=2)
    alpha[alpha < 25] = 0  # quita el "ruido" de compresión JPG del fondo
    a = np.maximum(alpha / 255.0, 1e-6)[..., None]
    # recupera el color real de los bordes suavizados (des-premultiplicar sobre blanco)
    color = np.clip((rgb - 255.0 * (1.0 - a)) / a, 0, 255)
    rgba = np.dstack([color, alpha]).astype(np.uint8)
    img = Image.fromarray(rgba, "RGBA")
    return ImageReader(img), img.width / img.height


# --------------------------------------------------------------------------
# Búsqueda automática de un hueco libre en la página
# --------------------------------------------------------------------------

def _mapa_tinta(fz_page, dpi=40, umbral=225):
    """Renderiza la página en gris a baja resolución y devuelve la imagen
    integral de los píxeles "con tinta" (texto, líneas, logos, fondos grises),
    más la escala píxeles/punto."""
    pix = fz_page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY, alpha=False)
    gris = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.stride)[:, :pix.width]
    tinta = (gris < umbral).astype(np.int32)
    integral = np.zeros((pix.height + 1, pix.width + 1), dtype=np.int64)
    integral[1:, 1:] = tinta.cumsum(0).cumsum(1)
    return integral, pix.width / fz_page.rect.width


def _buscar_hueco(integral, escala, page_w, page_h, block_w, block_h, margen_pt, holgura_pt):
    """Busca dónde cabe un bloque de block_w x block_h puntos sin tocar tinta
    (dejando 'holgura_pt' alrededor). Entre los sitios libres prefiere el más
    cercano a la esquina inferior derecha. Devuelve (x, y, tinta_tapada) con
    (x, y) = esquina inferior izquierda en puntos PDF, o None si no cabe."""
    H, W = integral.shape[0] - 1, integral.shape[1] - 1
    bw = int(np.ceil((block_w + 2 * holgura_pt) * escala))
    bh = int(np.ceil((block_h + 2 * holgura_pt) * escala))
    m = max(0, int((margen_pt - holgura_pt) * escala))
    if bw > W - 2 * m or bh > H - 2 * m:
        return None
    # tinta dentro de cada posible rectángulo (esquina superior izquierda = [y, x])
    suma = (integral[bh:, bw:] - integral[:-bh, bw:] - integral[bh:, :-bw] + integral[:-bh, :-bw])
    suma = suma[m:H - bh - m + 1, m:W - bw - m + 1]
    ys, xs = np.mgrid[0:suma.shape[0], 0:suma.shape[1]]
    ys, xs = ys + m, xs + m
    dist_abajo = H - (ys + bh)
    dist_derecha = W - (xs + bw)
    coste = suma * 1e6 + dist_abajo + 0.5 * dist_derecha
    iy, ix = np.unravel_index(np.argmin(coste), coste.shape)
    tinta = int(suma[iy, ix])
    x_pt = (xs[iy, ix] / escala) + holgura_pt
    y_top_pt = (ys[iy, ix] / escala) + holgura_pt
    y_pt = page_h - y_top_pt - block_h
    return x_pt, y_pt, tinta


# --------------------------------------------------------------------------
# Núcleo: dibujar el sello y estamparlo
# --------------------------------------------------------------------------

def _disposicion(tipo, box_w, box_h, logo_w, logo_h):
    """Tamaño del bloque completo y posición relativa (dentro del bloque) del
    recuadro de texto y del logo. tipo: 'izquierda' (logo a la izquierda del
    texto) o 'encima' (logo encima del texto)."""
    gap = SEPARACION_LOGO_MM * MM
    if not logo_w:
        return box_w, box_h, (0, 0), None
    if tipo == "izquierda":
        w = logo_w + gap + box_w
        h = max(logo_h, box_h)
        return w, h, (logo_w + gap, (h - box_h) / 2), (0, (h - logo_h) / 2)
    w = max(logo_w, box_w)
    h = logo_h + gap + box_h
    return w, h, ((w - box_w) / 2, 0), ((w - logo_w) / 2, box_h + gap)


def _dibujar_overlay(page_w, page_h, opciones: OpcionesSello, fz_page=None):
    """Crea un PDF de 1 página (en memoria) del mismo tamaño que la página
    original, con solo el sello (recuadro de texto y, si hay, logo) dibujado
    encima. Devuelve (buffer, aviso) — aviso es None si todo fue bien."""
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(page_w, page_h))

    fuente = "Helvetica-Bold"
    tam = opciones.tam_fuente
    margen_pt = opciones.margen_mm * MM
    ancho_max_pt = opciones.ancho_caja_mm * MM
    interlineado = tam * 1.25

    relleno_pt = 7  # espacio interior entre el texto y el borde del recuadro
    lineas = _wrap_text_por_ancho(c, opciones.texto, fuente, tam, ancho_max_pt - relleno_pt * 2)
    alto_texto = len(lineas) * interlineado
    box_w = ancho_max_pt
    box_h = alto_texto + relleno_pt * 2

    logo_img, logo_w, logo_h = None, 0, 0
    if opciones.logo_ruta:
        logo_img, aspecto = _cargar_logo(opciones.logo_ruta)
        logo_h = opciones.logo_alto_mm * MM
        logo_w = logo_h * aspecto

    aviso = None
    tipo = "izquierda"
    if opciones.x_manual_mm is not None and opciones.y_manual_mm is not None:
        # la X/Y manual es la del recuadro de texto; el logo va a su izquierda
        _, _, (dx, dy), _ = _disposicion(tipo, box_w, box_h, logo_w, logo_h)
        bx, by = opciones.x_manual_mm * MM - dx, opciones.y_manual_mm * MM - dy
    elif opciones.posicion == POS_AUTO and fz_page is not None:
        integral, escala = _mapa_tinta(fz_page)
        holgura = 1.5 * MM
        mejor = None
        # si no hay sitio libre con el logo a su tamaño, se prueba a reducirlo
        for reduccion in ((1.0, 0.8, 0.65) if logo_w else (1.0,)):
            for t in (["izquierda", "encima"] if logo_w else ["izquierda"]):
                lw, lh = logo_w * reduccion, logo_h * reduccion
                w, h, _, _ = _disposicion(t, box_w, box_h, lw, lh)
                r = _buscar_hueco(integral, escala, page_w, page_h, w, h, margen_pt, holgura)
                if r and (mejor is None or r[2] < mejor[3]):
                    mejor = (t, r[0], r[1], r[2], lw, lh)
                if mejor and mejor[3] == 0:
                    break  # sitio totalmente libre: no hace falta probar más
            if mejor and mejor[3] == 0:
                break
        if mejor is None:
            aviso = "no hay sitio en la página; puesto abajo a la derecha"
            w, h, _, _ = _disposicion(tipo, box_w, box_h, logo_w, logo_h)
            bx, by = _calcular_posicion("Abajo derecha", page_w, page_h, w, h, margen_pt)
        else:
            tipo, bx, by, tinta, logo_w, logo_h = mejor
            if tinta:
                aviso = "no hay hueco totalmente libre; puede tapar algo de la factura"
    else:
        pos = "Abajo derecha" if opciones.posicion == POS_AUTO else opciones.posicion
        w, h, _, _ = _disposicion(tipo, box_w, box_h, logo_w, logo_h)
        bx, by = _calcular_posicion(pos, page_w, page_h, w, h, margen_pt)

    _, _, (dx, dy), pos_logo = _disposicion(tipo, box_w, box_h, logo_w, logo_h)
    x, y = bx + dx, by + dy

    if logo_img is not None:
        c.drawImage(logo_img, bx + pos_logo[0], by + pos_logo[1], logo_w, logo_h, mask="auto")

    r, g, b = opciones.color_rgb
    color = Color(r, g, b, alpha=0.95)

    if opciones.con_recuadro:
        c.setStrokeColor(color)
        c.setLineWidth(1.1)
        c.roundRect(x, y, box_w, box_h, radius=3, stroke=1, fill=0)

    c.setFillColor(color)
    c.setFont(fuente, tam)
    text_y = y + box_h - interlineado + (interlineado - tam) * 0.3
    for linea in lineas:
        text_x = x + (box_w - c.stringWidth(linea, fuente, tam)) / 2  # centrado dentro del recuadro
        c.drawString(text_x, text_y, linea)
        text_y -= interlineado

    c.save()
    buf.seek(0)
    return buf, aviso


def sellar_pdf(ruta_entrada, ruta_salida, opciones: OpcionesSello):
    """Estampa el sello sobre el PDF de ruta_entrada y guarda el resultado en
    ruta_salida (no toca el original). Devuelve una lista de avisos (vacía si
    todo fue bien)."""
    reader = PdfReader(ruta_entrada)
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            raise RuntimeError("El PDF está protegido/cifrado; no se puede sellar automáticamente.")

    fz_doc = pymupdf.open(ruta_entrada) if opciones.posicion == POS_AUTO else None
    avisos = []
    writer = PdfWriter(clone_from=reader)
    for i, page in enumerate(writer.pages):
        if i == 0 or opciones.todas_paginas:
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            fz_page = None
            if fz_doc is not None:
                fz_page = fz_doc[i]
                # la búsqueda automática solo es fiable en páginas "normales"
                if fz_page.rotation or fz_page.cropbox != fz_page.mediabox or fz_page.mediabox.x0 or fz_page.mediabox.y0:
                    avisos.append(f"pág. {i + 1}: página girada/recortada, sin búsqueda automática")
                    fz_page = None
            overlay_buf, aviso = _dibujar_overlay(w, h, opciones, fz_page)
            if aviso:
                avisos.append(f"pág. {i + 1}: {aviso}")
            overlay_reader = PdfReader(overlay_buf)
            page.merge_page(overlay_reader.pages[0])

    os.makedirs(os.path.dirname(ruta_salida) or ".", exist_ok=True)
    with open(ruta_salida, "wb") as f:
        writer.write(f)
    return avisos


# --------------------------------------------------------------------------
# Procesado de una carpeta / lista de archivos completa
# --------------------------------------------------------------------------

def procesar_lote(rutas_pdf, carpeta_salida, opciones_global, overrides=None, log=print):
    """overrides: dict {ruta_pdf: OpcionesSello} para archivos con texto/posición
    propios; si un archivo no está en overrides se usan las opciones globales."""
    overrides = overrides or {}
    ok, fallos = 0, []
    for ruta in rutas_pdf:
        nombre = os.path.basename(ruta)
        opts = overrides.get(ruta, opciones_global)
        destino = os.path.join(carpeta_salida, nombre)
        try:
            avisos = sellar_pdf(ruta, destino, opts)
            log(f"OK  -> {nombre}" + (f"   (REVISAR: {'; '.join(avisos)})" if avisos else ""))
            ok += 1
        except Exception as e:
            log(f"ERROR -> {nombre}: {e}")
            fallos.append((nombre, str(e)))
    log(f"\nTerminado: {ok} sellados correctamente, {len(fallos)} con error.")
    return ok, fallos


# --------------------------------------------------------------------------
# Interfaz gráfica (tkinter, incluido en Python de forma estándar en Windows/Mac)
# --------------------------------------------------------------------------

def lanzar_gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    TEXTO_POR_DEFECTO = (
        "ESTA FACTURA ESTA SUBVENCIONADA POR EL AYUNTAMIENTO DE FUENLABRADA. "
        "CONVOCATORIA 2024; IMPORTE 100%"
    )

    root = tk.Tk()
    root.title("Sellador de facturas PDF")
    root.geometry("960x700")

    archivos = []          # lista de rutas completas
    overrides = {}         # ruta -> OpcionesSello personalizadas

    # ---------- panel izquierdo: lista de archivos ----------
    frame_izq = ttk.Frame(root, padding=8)
    frame_izq.pack(side="left", fill="both", expand=False)

    ttk.Label(frame_izq, text="Facturas (PDF)", font=("", 10, "bold")).pack(anchor="w")
    lista = tk.Listbox(frame_izq, width=42, height=26, selectmode="extended")
    lista.pack(fill="y", expand=False, pady=4)

    def refrescar_lista():
        lista.delete(0, tk.END)
        for r in archivos:
            marca = " *" if r in overrides else ""
            lista.insert(tk.END, os.path.basename(r) + marca)

    def anadir_pdfs():
        rutas = filedialog.askopenfilenames(
            title="Selecciona las facturas en PDF",
            filetypes=[("PDF", "*.pdf")],
        )
        for r in rutas:
            if r not in archivos:
                archivos.append(r)
        refrescar_lista()

    def anadir_carpeta():
        carpeta = filedialog.askdirectory(title="Selecciona la carpeta con las facturas")
        if not carpeta:
            return
        for nombre in sorted(os.listdir(carpeta)):
            if nombre.lower().endswith(".pdf"):
                ruta = os.path.join(carpeta, nombre)
                if ruta not in archivos:
                    archivos.append(ruta)
        refrescar_lista()

    def quitar_seleccionados():
        sel = list(lista.curselection())
        for idx in reversed(sel):
            ruta = archivos.pop(idx)
            overrides.pop(ruta, None)
        refrescar_lista()

    def vaciar():
        archivos.clear()
        overrides.clear()
        refrescar_lista()

    btns = ttk.Frame(frame_izq)
    btns.pack(fill="x")
    ttk.Button(btns, text="Añadir PDFs...", command=anadir_pdfs).pack(side="left", padx=2)
    ttk.Button(btns, text="Añadir carpeta...", command=anadir_carpeta).pack(side="left", padx=2)
    btns2 = ttk.Frame(frame_izq)
    btns2.pack(fill="x", pady=(2, 8))
    ttk.Button(btns2, text="Quitar seleccionados", command=quitar_seleccionados).pack(side="left", padx=2)
    ttk.Button(btns2, text="Vaciar lista", command=vaciar).pack(side="left", padx=2)

    ttk.Label(frame_izq, text="'*' = este archivo tiene texto/posición\npropios (distintos del general).",
              foreground="#555").pack(anchor="w", pady=(4, 0))

    # ---------- panel derecho: opciones ----------
    frame_der = ttk.Frame(root, padding=8)
    frame_der.pack(side="left", fill="both", expand=True)

    ttk.Label(frame_der, text="Texto del sello (general, para todos los archivos)",
              font=("", 10, "bold")).pack(anchor="w")
    ttk.Label(frame_der, text="Sirve para cualquier ayuntamiento/convocatoria: escribe el texto exacto que te exijan.",
              foreground="#555").pack(anchor="w")
    txt_general = tk.Text(frame_der, height=4, width=70, wrap="word")
    txt_general.insert("1.0", TEXTO_POR_DEFECTO)
    txt_general.pack(fill="x", pady=(2, 10))

    fila_opts = ttk.Frame(frame_der)
    fila_opts.pack(fill="x", pady=2)

    ttk.Label(fila_opts, text="Posición:").grid(row=0, column=0, sticky="w")
    combo_pos = ttk.Combobox(fila_opts, values=POSICIONES, state="readonly", width=30)
    combo_pos.set(POS_AUTO)
    combo_pos.grid(row=0, column=1, padx=6)

    ttk.Label(fila_opts, text="Color:").grid(row=0, column=2, sticky="w")
    combo_color = ttk.Combobox(fila_opts, values=list(COLORES.keys()), state="readonly", width=20)
    combo_color.set("Negro")
    combo_color.grid(row=0, column=3, padx=6)

    ttk.Label(fila_opts, text="Tamaño letra:").grid(row=1, column=0, sticky="w", pady=6)
    spin_tam = ttk.Spinbox(fila_opts, from_=6, to=18, width=5)
    spin_tam.set(9)
    spin_tam.grid(row=1, column=1, sticky="w")

    var_todas = tk.BooleanVar(value=False)
    ttk.Checkbutton(fila_opts, text="Sellar todas las páginas (si no, solo la primera)",
                    variable=var_todas).grid(row=1, column=2, columnspan=2, sticky="w")

    ttk.Label(frame_der, text="Imagen del sello / logo (opcional, se pone junto al texto):",
              font=("", 10, "bold")).pack(anchor="w", pady=(12, 0))
    fila_logo = ttk.Frame(frame_der)
    fila_logo.pack(fill="x", pady=2)
    var_logo = tk.StringVar(value="")
    ttk.Entry(fila_logo, textvariable=var_logo, width=48).pack(side="left", fill="x", expand=True)

    def elegir_logo():
        ruta = filedialog.askopenfilename(
            title="Imagen del sello (el fondo blanco se vuelve transparente)",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif"), ("Todos", "*.*")],
        )
        if ruta:
            var_logo.set(ruta)

    ttk.Button(fila_logo, text="Elegir...", command=elegir_logo).pack(side="left", padx=4)
    ttk.Button(fila_logo, text="Quitar", command=lambda: var_logo.set("")).pack(side="left")
    ttk.Label(fila_logo, text="  Alto (mm):").pack(side="left")
    spin_logo_alto = ttk.Spinbox(fila_logo, from_=10, to=60, width=4)
    spin_logo_alto.set(26)
    spin_logo_alto.pack(side="left")

    ttk.Label(frame_der, text="Carpeta de salida (los originales no se modifican):",
              font=("", 10, "bold")).pack(anchor="w", pady=(12, 0))
    fila_salida = ttk.Frame(frame_der)
    fila_salida.pack(fill="x", pady=2)
    var_salida = tk.StringVar(value="")
    entry_salida = ttk.Entry(fila_salida, textvariable=var_salida, width=60)
    entry_salida.pack(side="left", fill="x", expand=True)

    def elegir_salida():
        carpeta = filedialog.askdirectory(title="Carpeta donde guardar las facturas selladas")
        if carpeta:
            var_salida.set(carpeta)

    ttk.Button(fila_salida, text="Elegir...", command=elegir_salida).pack(side="left", padx=4)

    # ---- personalizar archivo seleccionado ----
    ttk.Separator(frame_der).pack(fill="x", pady=10)
    ttk.Label(frame_der, text="Personalizar el archivo seleccionado en la lista (opcional)",
              font=("", 10, "bold")).pack(anchor="w")

    var_personalizar = tk.BooleanVar(value=False)
    chk_personalizar = ttk.Checkbutton(frame_der, text="Usar texto/posición propios para este archivo",
                                        variable=var_personalizar)
    chk_personalizar.pack(anchor="w")

    txt_custom = tk.Text(frame_der, height=3, width=70, wrap="word", state="disabled")
    txt_custom.pack(fill="x", pady=4)

    fila_custom = ttk.Frame(frame_der)
    fila_custom.pack(fill="x")
    ttk.Label(fila_custom, text="Posición propia:").grid(row=0, column=0, sticky="w")
    combo_pos_custom = ttk.Combobox(fila_custom, values=POSICIONES, state="disabled", width=30)
    combo_pos_custom.grid(row=0, column=1, padx=6)

    def on_seleccion_lista(event=None):
        sel = lista.curselection()
        if not sel:
            return
        ruta = archivos[sel[0]]
        if ruta in overrides:
            o = overrides[ruta]
            var_personalizar.set(True)
            txt_custom.config(state="normal")
            txt_custom.delete("1.0", tk.END)
            txt_custom.insert("1.0", o.texto)
            combo_pos_custom.set(o.posicion)
            combo_pos_custom.config(state="readonly")
        else:
            var_personalizar.set(False)
            txt_custom.delete("1.0", tk.END)
            txt_custom.insert("1.0", txt_general.get("1.0", "end-1c"))
            txt_custom.config(state="disabled")
            combo_pos_custom.set(combo_pos.get())
            combo_pos_custom.config(state="disabled")

    lista.bind("<<ListboxSelect>>", on_seleccion_lista)

    def toggle_personalizar():
        if var_personalizar.get():
            txt_custom.config(state="normal")
            combo_pos_custom.config(state="readonly")
        else:
            sel = lista.curselection()
            if sel:
                ruta = archivos[sel[0]]
                overrides.pop(ruta, None)
                refrescar_lista()
            txt_custom.config(state="disabled")
            combo_pos_custom.config(state="disabled")

    chk_personalizar.config(command=toggle_personalizar)

    def guardar_override(event=None):
        sel = lista.curselection()
        if not sel or not var_personalizar.get():
            return
        ruta = archivos[sel[0]]
        base_general = leer_opciones_generales()
        overrides[ruta] = replace(
            base_general,
            texto=txt_custom.get("1.0", "end-1c").strip(),
            posicion=combo_pos_custom.get() or base_general.posicion,
        )
        refrescar_lista()

    txt_custom.bind("<FocusOut>", guardar_override)
    combo_pos_custom.bind("<<ComboboxSelected>>", guardar_override)

    # ---------- log ----------
    ttk.Separator(frame_der).pack(fill="x", pady=10)
    log_box = tk.Text(frame_der, height=8, width=70, state="disabled", bg="#f4f4f4")
    log_box.pack(fill="both", expand=True)

    def log(msg):
        log_box.config(state="normal")
        log_box.insert(tk.END, str(msg) + "\n")
        log_box.see(tk.END)
        log_box.config(state="disabled")
        root.update_idletasks()

    def leer_opciones_generales():
        return OpcionesSello(
            texto=txt_general.get("1.0", "end-1c").strip(),
            posicion=combo_pos.get(),
            tam_fuente=float(spin_tam.get()),
            color_rgb=COLORES.get(combo_color.get(), (0.0, 0.0, 0.0)),
            todas_paginas=var_todas.get(),
            logo_ruta=var_logo.get().strip() or None,
            logo_alto_mm=float(spin_logo_alto.get()),
        )

    def procesar():
        if not archivos:
            messagebox.showwarning("Sin archivos", "Añade primero una o varias facturas en PDF.")
            return
        carpeta_salida = var_salida.get().strip()
        if not carpeta_salida:
            base = os.path.dirname(archivos[0])
            carpeta_salida = os.path.join(base, "SELLADAS")
            var_salida.set(carpeta_salida)
        log_box.config(state="normal")
        log_box.delete("1.0", tk.END)
        log_box.config(state="disabled")
        opts_general = leer_opciones_generales()
        if not opts_general.texto:
            messagebox.showwarning("Falta texto", "Escribe el texto del sello.")
            return
        if opts_general.logo_ruta and not os.path.isfile(opts_general.logo_ruta):
            messagebox.showwarning("Imagen no encontrada", "No existe la imagen del sello indicada.")
            return
        # los archivos personalizados conservan su texto/posición, pero el resto
        # de opciones (color, logo, tamaño...) se toman de las generales actuales
        overrides_actuales = {r: replace(opts_general, texto=o.texto, posicion=o.posicion)
                              for r, o in overrides.items()}
        log(f"Procesando {len(archivos)} archivo(s) -> {carpeta_salida}\n")
        try:
            ok, fallos = procesar_lote(archivos, carpeta_salida, opts_general, overrides_actuales, log=log)
        except Exception:
            log("ERROR INESPERADO:\n" + traceback.format_exc())
            return
        if fallos:
            messagebox.showwarning("Terminado con avisos",
                                    f"{ok} sellados correctamente.\n{len(fallos)} con error (ver registro).")
        else:
            messagebox.showinfo("Terminado", f"Se sellaron correctamente {ok} facturas en:\n{carpeta_salida}")

    ttk.Button(frame_der, text="Procesar todas", command=procesar).pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    lanzar_gui()
