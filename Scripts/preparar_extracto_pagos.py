"""
Prepara el extracto bancario de un expediente para acreditar los pagos.

A partir del extracto indicado en el config.json genera una COPIA en la que:
  - solo quedan visibles los movimientos que pagan facturas del checklist
    (los anotados en su columna "Pago localizado...", que rellena
    completar_checklist.py);
  - el resto de movimientos se BORRAN de verdad (el texto desaparece del PDF,
    no solo se tapa), para no enseñar datos de terceros (donantes, socios...);
  - cada movimiento visible lleva un recuadro rojo y, en el margen, el
    nº de justificante al que corresponde.

    python Scripts/preparar_extracto_pagos.py "NOMBRE DEL EXPEDIENTE"

El extracto original no se toca. La copia se guarda en "extracto_salida".
Necesita el PDF descargado de la banca online (no sirve uno escaneado).
"""
import os
import sys

import openpyxl
import pymupdf

import banco
import expediente

ROJO = (0.8, 0, 0)
GRIS = (0.82, 0.82, 0.82)
NOTA_POR_DEFECTO = ("Se muestran solo los movimientos que pagan las facturas justificadas. "
                    "El resto se ha ocultado por protección de datos. En el margen: nº de justificante.")


def pagos_a_mostrar(checklist):
    """{(pág, fecha, importe): [nº justificante, ...]} leído del checklist."""
    ws = openpyxl.load_workbook(checklist).worksheets[0]
    filas = ws.iter_rows(values_only=True)
    c = expediente.columnas(next(filas))
    mostrar = {}
    for f in filas:
        if not f[c["num"]] or not f[c["pago"]]:
            continue
        nums = str(f[c["num"]]).split(", ")
        lineas = [l for l in str(f[c["pago"]]).split("\n") if banco.RE_DESCRIPCION.search(l)]
        # si hay tantos pagos como números (una factura pagada en dos veces), van emparejados
        for i, linea in enumerate(lineas):
            fecha, importe, pag = banco.RE_DESCRIPCION.search(linea).groups()
            propios = [nums[i]] if len(lineas) == len(nums) else nums
            lista = mostrar.setdefault((int(pag), fecha, importe), [])
            lista += [n for n in propios if n not in lista]
    return mostrar


def escribir_ajustado(page, rect, texto, tam_max):
    """Escribe 'texto' dentro de rect reduciendo la letra si no cabe."""
    tam = tam_max
    while tam > 3.5 and pymupdf.get_text_length(texto, "hebo", tam) > rect.width:
        tam -= 0.3
    page.insert_text((rect.x0, rect.y0 + min(rect.height, tam + 1.5)), texto, fontsize=tam,
                     fontname="hebo", color=ROJO)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    cfg = expediente.cargar(sys.argv[1])
    nota = cfg.get("nota_extracto") or NOTA_POR_DEFECTO
    salida = cfg["extracto_salida"]
    if not cfg.get("extracto") or not os.path.isfile(cfg["extracto"]):
        sys.exit(f"No encuentro el extracto bancario: {cfg.get('extracto')}\n"
                 "Comprueba que está en la carpeta del expediente y que su nombre coincide con "
                 "\"extracto\" en config.json.")
    mostrar = pagos_a_mostrar(cfg["checklist"])
    if not mostrar:
        sys.exit("El checklist no tiene pagos localizados. Ejecuta antes 'completar_checklist.py'.")

    movimientos, paginas = banco.leer_movimientos(cfg["extracto"])
    if not movimientos:
        sys.exit("No se ha reconocido ningún movimiento en el extracto. ¿Es el PDF descargado del banco "
                 "(no escaneado)? Ver README, apartado 'Si algo falla'.")
    doc = pymupdf.open(cfg["extracto"])
    encontrados = set()
    for pno, page in enumerate(doc, 1):
        movs = [m for m in movimientos if m["pag"] == pno]
        visibles = []
        for m in movs:
            k = banco.clave(m)
            if k in mostrar and m["cargo"] is not False:
                visibles.append((m["rect"], mostrar[k]))
                encontrados.add(k)
            else:
                page.add_redact_annot(m["rect"], fill=GRIS)
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)

        tabla = paginas[pno - 1]
        if visibles and tabla and page.rect.x1 - tabla["x1"] < 25 and tabla["x0"] - page.rect.x0 < 25:
            # la tabla ocupa todo el ancho: se ensancha la página por la derecha
            # para que el nº de justificante no tape nada
            if page.rotation == 0 and page.mediabox == page.cropbox:
                page.set_mediabox(pymupdf.Rect(page.mediabox.x0, page.mediabox.y0,
                                               page.mediabox.x1 + 50, page.mediabox.y1))
        for rect, nums in visibles:
            page.draw_rect(rect, color=ROJO, width=0.9)
            etiqueta = "Nº " + ", ".join(nums)
            if tabla and page.rect.x1 - tabla["x1"] >= 25:      # margen derecho
                zona = pymupdf.Rect(tabla["x1"] + 2, rect.y0, page.rect.x1 - 2, rect.y1)
            elif tabla and tabla["x0"] - page.rect.x0 >= 25:    # margen izquierdo
                zona = pymupdf.Rect(page.rect.x0 + 2, rect.y0, tabla["x0"] - 2, rect.y1)
            else:                                               # último recurso: dentro de la fila
                zona = pymupdf.Rect(rect.x1 - 45, rect.y0, rect.x1 - 2, rect.y1)
            escribir_ajustado(page, zona, etiqueta, 6.5)

        # nota explicativa arriba (o abajo si arriba hay texto del banco)
        palabras = page.get_text("words")
        if not any(w[1] < 26 for w in palabras):
            zona_nota = pymupdf.Rect(30, 6, page.rect.x1 - 30, 26)
        else:
            zona_nota = pymupdf.Rect(30, page.rect.y1 - 24, page.rect.x1 - 30, page.rect.y1 - 4)
        page.insert_textbox(zona_nota, nota, fontsize=6.5, fontname="helv", color=ROJO,
                            align=pymupdf.TEXT_ALIGN_CENTER)

    os.makedirs(os.path.dirname(salida), exist_ok=True)
    doc.save(salida, garbage=4, deflate=True)
    print(f"{len(encontrados)} movimientos visibles -> {salida}")
    faltan = set(mostrar) - encontrados
    if faltan:
        print("\nAVISO: estos pagos del checklist NO se han encontrado en el extracto:")
        for pag, fecha, importe in sorted(faltan):
            print(f"  pág. {pag}  {fecha}  {importe} €  (Nº {', '.join(mostrar[(pag, fecha, importe)])})")
        print("Vuelve a ejecutar completar_checklist.py o revisa la columna 'Pago localizado'.")
    print("\nAbre el PDF y compruébalo antes de enviarlo.")


if __name__ == "__main__":
    main()
