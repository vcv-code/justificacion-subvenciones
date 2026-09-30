"""
Sella de una vez todas las facturas DIGITALES de un expediente.

Lee el checklist del expediente (una fila por factura), estampa en cada
factura el texto de la columna "TEXTO EXACTO DEL SELLO" junto con la imagen
del sello, y genera hojas de miniaturas para revisarlas por tandas. Las
facturas en papel ("ESCANEADA") se sellan a mano y no se procesan.

    python Scripts/sellar_facturas_lote.py "ALGP 2024 - Fuenlabrada"
    python Scripts/sellar_facturas_lote.py "ALGP 2024 - Fuenlabrada" 1 20   (solo Nº 1 a 20)

Los originales no se tocan: las copias van a la carpeta "facturas_selladas"
del config.json. Si el sello de alguna factura queda mal, se puede fijar su
posición en "ajustes_posicion" del config.json, por ejemplo:
    "ajustes_posicion": {"13": {"posicion": "Arriba derecha"},
                         "20": {"x_manual_mm": 120, "y_manual_mm": 40}}
"""
import os
import sys
from dataclasses import replace

import openpyxl
import pymupdf
from PIL import Image, ImageDraw, ImageFont

import expediente
import sellador_facturas as sf

POR_HOJA = 12  # miniaturas por hoja de revisión (4 x 3)


def euros(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def primer_num(k):
    return int(str(k).split(",")[0])


def leer_lote(checklist):
    """Filas DIGITALES del checklist, localizando las columnas por su título."""
    ws = openpyxl.load_workbook(checklist).worksheets[0]
    filas = ws.iter_rows(values_only=True)
    c = expediente.columnas(next(filas))
    lote = []
    for f in filas:
        if f[c["num"]] and str(f[c["tipo"]] or "").startswith("DIGITAL"):
            if not (f[c["texto"]] and f[c["archivo"]] and f[c["copia"]]):
                print(f"AVISO: a la fila Nº {f[c['num']]} le falta texto, archivo o copia. "
                      "Ejecuta antes 'completar_checklist.py'.")
                continue
            lote.append((str(f[c["num"]]), f[c["proveedor"]], expediente.a_numero(f[c["importe"]]),
                         f[c["texto"]], f[c["archivo"]], f[c["copia"]]))
    return lote


def hoja_revision(items, ruta):
    """items: [(etiqueta, ruta_pdf)] -> PNG con miniaturas de la 1ª página."""
    cols, ancho = 4, 460
    miniaturas = []
    for etiqueta, pdf in items:
        pix = pymupdf.open(pdf)[0].get_pixmap(dpi=55)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        img.thumbnail((ancho, ancho * 1.5))
        miniaturas.append((etiqueta, img))
    alto = max(i.height for _, i in miniaturas) + 30
    filas = (len(miniaturas) + cols - 1) // cols
    hoja = Image.new("RGB", (cols * (ancho + 10) + 10, filas * (alto + 10) + 10), "#cccccc")
    d = ImageDraw.Draw(hoja)
    try:
        fuente = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        fuente = ImageFont.load_default(size=16)
    for n, (etiqueta, img) in enumerate(miniaturas):
        x = 10 + (n % cols) * (ancho + 10)
        y = 10 + (n // cols) * (alto + 10)
        d.rectangle([x, y, x + ancho, y + alto], fill="white")
        d.text((x + 6, y + 5), etiqueta[:52], fill="black", font=fuente)
        hoja.paste(img, (x + (ancho - img.width) // 2, y + 28))
    hoja.save(ruta)


def main():
    if len(sys.argv) not in (2, 4):
        sys.exit(__doc__)
    cfg = expediente.cargar(sys.argv[1])
    desde, hasta = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) == 4 else (0, 10 ** 6)
    salida = cfg["facturas_selladas"]
    revision = os.path.join(salida, "_revision")
    os.makedirs(revision, exist_ok=True)
    if cfg.get("sello") and not os.path.isfile(cfg["sello"]):
        sys.exit(f"No encuentro la imagen del sello: {cfg['sello']}\n"
                 "Ponla con ese nombre en la carpeta del expediente, o cambia \"sello\" en config.json.\n"
                 "Si no quieres imagen, deja la línea así:  \"sello\": \"\",")
    base_opc = sf.OpcionesSello(texto="", logo_ruta=cfg.get("sello"), logo_alto_mm=cfg.get("sello_alto_mm", 26))
    ajustes = cfg.get("ajustes_posicion", {})

    hechos, revisar = [], []
    for num, prov, importe, texto, archivo, nombre in leer_lote(cfg["checklist"]):
        if not desde <= primer_num(num) <= hasta:
            continue
        opc = replace(base_opc, texto=texto, **ajustes.get(num, {}))
        destino = os.path.join(salida, nombre)
        try:
            avisos = sf.sellar_pdf(os.path.join(cfg["facturas_originales"], archivo), destino, opc)
        except Exception as e:
            print(f"ERROR {nombre}: {e}")
            revisar.append(nombre)
            continue
        print(f"OK  {nombre}" + (f"   <-- REVISAR: {'; '.join(avisos)}" if avisos else ""))
        if avisos:
            revisar.append(nombre)
        hechos.append((f"Nº {num} · {euros(importe)} € · {prov}", destino))

    for i in range(0, len(hechos), POR_HOJA):
        grupo = hechos[i:i + POR_HOJA]
        ruta = os.path.join(revision, f"tanda_{i // POR_HOJA + 1:02d}.png")
        hoja_revision(grupo, ruta)
        print(f"Hoja de revisión: {ruta}  ({grupo[0][0].split(' ·')[0]} a {grupo[-1][0].split(' ·')[0]})")
    print(f"\n{len(hechos)} facturas selladas en {salida}")
    if revisar:
        print("Con aviso (mirar con calma):", *revisar, sep="\n  ")


if __name__ == "__main__":
    main()
