"""
Junta toda la documentación de un expediente en UN solo PDF para enviarlo.

Crea en la carpeta "ENTREGA" del expediente:
    "Documentacion justificativa.pdf", con:
      1. una página de ÍNDICE: cada factura con su nº, proveedor, importe y
         la página donde está;
      2. todas las facturas selladas, en orden de nº de justificante;
      3. los justificantes de pago (el extracto limpio primero y luego los
         demás PDF de la carpeta de justificantes).
    Cada factura y justificante lleva un MARCADOR (el panel lateral del lector
    de PDF), para ir directo a cualquiera.

Para que pese poco: quita lo repetido (fuentes, la imagen del sello…) y
reduce las imágenes escaneadas a una resolución suficiente para leerlas.
Si aun así pasa del límite (config.json → "limite_mb_entrega", 10 por
defecto), lo parte en varios archivos ("parte 1 de 2"...).

El escrito (Word/PDF firmado) NO se incluye: se presenta aparte, como
documento principal de la entrega.

    python Scripts/preparar_entrega.py "NOMBRE DEL EXPEDIENTE"
"""
import html
import os
import sys

import openpyxl
import pymupdf

import expediente

LIMITE_MB_POR_DEFECTO = 10


def leer_facturas(cfg):
    """[(nº, proveedor, nº factura, importe, ruta del PDF sellado)] en orden."""
    ws = openpyxl.load_workbook(cfg["checklist"]).worksheets[0]
    filas = ws.iter_rows(values_only=True)
    c = expediente.columnas(next(filas))
    res = []
    for f in filas:
        if not f[c["num"]] or not f[c["copia"]]:
            continue
        num = str(f[c["num"]])
        res.append((num, f[c["proveedor"]], f[c["nfactura"]], expediente.a_numero(f[c["importe"]]),
                    os.path.join(cfg["facturas_selladas"], str(f[c["copia"]]))))
    res.sort(key=lambda x: int(x[0].split(",")[0]) if x[0].split(",")[0].strip().isdigit() else 10 ** 6)
    return res


def euros(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €" if v is not None else ""


def pagina_indice(doc, titulo, filas_indice, total):
    """Añade al principio una o varias páginas con la tabla índice."""
    por_pagina = 38
    trozos = [filas_indice[i:i + por_pagina] for i in range(0, len(filas_indice), por_pagina)] or [[]]
    for n, trozo in enumerate(trozos):
        page = doc.new_page(pno=n, width=595, height=842)
        filas_html = "".join(
            f"<tr><td>{html.escape(a)}</td><td>{html.escape(b)}</td><td>{html.escape(c)}</td>"
            f"<td class='d'>{html.escape(d)}</td><td class='d'>{e}</td></tr>" for a, b, c, d, e in trozo)
        cabecera = f"<h1>{html.escape(titulo)}</h1>" if n == 0 else ""
        pie = (f"<p><b>Total: {euros(total)}</b> · {len(filas_indice)} documentos</p>"
               if n == len(trozos) - 1 else "<p>(continúa)</p>")
        page.insert_htmlbox(pymupdf.Rect(40, 40, 555, 810), f"""
            {cabecera}
            <table><tr><th>Nº</th><th>Proveedor / documento</th><th>Nº factura</th><th class='d'>Importe</th>
            <th class='d'>Pág.</th></tr>{filas_html}</table>{pie}""", css="""
            * {font-family: sans-serif; font-size: 8.5pt;}
            h1 {font-size: 12pt; margin-bottom: 8px;}
            table {border-collapse: collapse; width: 100%;}
            th, td {border-bottom: 0.5px solid #999; padding: 2px 4px; text-align: left;}
            th {background: #ddd;}
            .d {text-align: right;}""")
    return len(trozos)


def construir(cfg, facturas, justificantes):
    """Devuelve (documento, avisos). Las páginas del índice se calculan al final."""
    doc = pymupdf.open()
    marcadores, filas_indice, avisos = [], [], []
    total = 0.0
    for num, prov, nfac, importe, ruta in facturas:
        if not os.path.isfile(ruta):
            avisos.append(f"Falta la factura sellada nº {num}: {os.path.basename(ruta)}")
            continue
        inicio = doc.page_count
        with pymupdf.open(ruta) as src:
            doc.insert_pdf(src)
        etiqueta = f"Nº {num} - {prov} - {euros(importe)}"
        marcadores.append([2, etiqueta, inicio])
        filas_indice.append((num, str(prov or ""), str(nfac or ""), euros(importe), inicio))
        total += importe or 0
    if justificantes:
        marcadores.append([1, "JUSTIFICANTES DE PAGO", doc.page_count])
        for ruta in justificantes:
            inicio = doc.page_count
            with pymupdf.open(ruta) as src:
                doc.insert_pdf(src)
            nombre = os.path.splitext(os.path.basename(ruta))[0]
            marcadores.append([2, nombre, inicio])
            filas_indice.append(("Pago", nombre, "", "", inicio))
    # índice delante: se desplazan todas las páginas
    n_indice = pagina_indice(doc, cfg.get("descripcion", "Documentación justificativa"),
                             [(a, b, c, d, "") for a, b, c, d, _ in filas_indice], total)
    doc.delete_pages(from_page=0, to_page=n_indice - 1)
    filas_indice = [(a, b, c, d, str(p + n_indice + 1)) for a, b, c, d, p in filas_indice]
    pagina_indice(doc, cfg.get("descripcion", "Documentación justificativa"), filas_indice, total)
    toc = [[1, "ÍNDICE", 1], [1, "FACTURAS SELLADAS", n_indice + 1]]
    toc += [[nivel, t, p + n_indice + 1] for nivel, t, p in marcadores]
    doc.set_toc(toc)
    return doc, avisos


def comprimir(doc):
    """Reduce las imágenes grandes (escaneos) a 150 ppp, suficiente para leerlas."""
    try:
        doc.rewrite_images(dpi_threshold=180, dpi_target=150, quality=75, lossy=True, lossless=True)
    except Exception as e:  # versiones antiguas de PyMuPDF
        print(f"  (no se han podido reducir las imágenes: {e})")


def guardar(doc, ruta):
    doc.save(ruta, garbage=4, deflate=True, deflate_images=True, deflate_fonts=True, clean=True)
    return os.path.getsize(ruta) / 1024 / 1024


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    cfg = expediente.cargar(sys.argv[1])
    limite = float(cfg.get("limite_mb_entrega", LIMITE_MB_POR_DEFECTO))
    carpeta = os.path.join(cfg["carpeta"], "ENTREGA")
    os.makedirs(carpeta, exist_ok=True)
    # se borran los de una ejecución anterior (p. ej. partes que ya no hacen falta)
    for viejo in os.listdir(carpeta):
        if viejo.startswith("Documentacion justificativa") and viejo.lower().endswith(".pdf"):
            try:
                os.remove(os.path.join(carpeta, viejo))
            except PermissionError:
                sys.exit(f"No puedo sustituir '{viejo}': ciérralo si lo tienes abierto y repite.")

    facturas = leer_facturas(cfg)
    just_dir = os.path.dirname(cfg["extracto_salida"]) if cfg.get("extracto_salida") else None
    justificantes = []
    if just_dir and os.path.isdir(just_dir):
        todos = sorted(os.path.join(just_dir, f) for f in os.listdir(just_dir) if f.lower().endswith(".pdf"))
        extracto = os.path.normpath(cfg["extracto_salida"])
        justificantes = [r for r in todos if os.path.normpath(r) == extracto] + \
                        [r for r in todos if os.path.normpath(r) != extracto]

    print(f"Uniendo {len(facturas)} facturas y {len(justificantes)} justificantes...")
    doc, avisos = construir(cfg, facturas, justificantes)
    comprimir(doc)
    salida = os.path.join(carpeta, "Documentacion justificativa.pdf")
    mb = guardar(doc, salida)
    print(f"Creado: {salida}  ({doc.page_count} páginas, {mb:.1f} MB)")

    if mb > limite:
        partes = int(mb // limite) + 1
        print(f"Pasa del límite de {limite:g} MB: se parte en {partes} archivos.")
        por_parte = -(-doc.page_count // partes)
        for i in range(partes):
            parte = pymupdf.open()
            parte.insert_pdf(doc, from_page=i * por_parte, to_page=min((i + 1) * por_parte, doc.page_count) - 1)
            r = os.path.join(carpeta, f"Documentacion justificativa - parte {i + 1} de {partes}.pdf")
            print(f"  {os.path.basename(r)}: {guardar(parte, r):.1f} MB")
        print("Envía las partes (o el archivo completo si la sede lo admite).")

    for a in avisos:
        print("AVISO:", a)
    print("\nAbre el PDF y repásalo: índice, marcadores (panel lateral) y que se lean bien los escaneos.")


if __name__ == "__main__":
    main()
