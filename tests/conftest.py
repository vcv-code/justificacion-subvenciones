"""
Utilidades comunes de los tests. Todos los datos son INVENTADOS: se generan
PDF de facturas y extractos de mentira en carpetas temporales. Nunca se usan
facturas ni extractos reales.
"""
import json
import os
import shutil
import sys

import pymupdf
import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "Scripts"))
sys.path.insert(0, os.path.join(RAIZ, "Herramienta sellado facturas"))


def pdf_factura(ruta, numero, importe, lineas_extra=12):
    """Factura digital de mentira: texto real repartido por la página."""
    doc = pymupdf.open()
    p = doc.new_page(width=595, height=842)
    p.insert_text((50, 60), "PROVEEDOR DE PRUEBA S.L.", fontsize=14)
    p.insert_text((50, 90), f"FACTURA Nº {numero}", fontsize=12)
    for i in range(lineas_extra):
        p.insert_text((50, 140 + i * 18), f"Articulo de prueba {i + 1} ........ 1,00 €", fontsize=10)
    p.insert_text((380, 400), f"TOTAL: {importe} €", fontsize=12)
    p.insert_text((50, 810), "Pie de página con datos registrales del proveedor", fontsize=8)
    doc.save(ruta)


def pdf_escaneado(ruta):
    """Factura "escaneada": una imagen a página completa, sin texto."""
    doc = pymupdf.open()
    p = doc.new_page(width=595, height=842)
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 60, 85), False)
    pix.set_rect(pix.irect, (240, 240, 235))
    p.insert_image(p.rect, pixmap=pix)
    doc.save(ruta)


def pdf_extracto(ruta, filas, formato="pueyo"):
    """Extracto bancario de mentira.
    filas: [(fecha 'dd/mm/aaaa', concepto, importe con signo '-84,81' , saldo)]
    formato 'pueyo': fecha | concepto | importe con signo detrás (84,81-) | saldo
    formato 'otro' : fecha | fecha valor | concepto | importe con signo delante | saldo,
                     sin margen lateral y con conceptos de dos líneas."""
    doc = pymupdf.open()
    p = doc.new_page(width=595, height=842)
    p.insert_text((60, 40), "BANCO DE PRUEBA - Consulta de movimientos", fontsize=10)
    p.insert_text((60, 80), "Fecha Operación   Concepto          Importe      Saldo", fontsize=8)
    y = 100
    for fecha, concepto, importe, saldo in filas:
        if formato == "pueyo":
            imp = importe.lstrip("-") + ("-" if importe.startswith("-") else "+")
            p.insert_text((56, y), fecha, fontsize=7)
            p.insert_text((98, y), concepto, fontsize=7)
            p.insert_text((470 - len(imp) * 4, y), imp, fontsize=7)
            p.insert_text((545 - len(saldo) * 4, y), saldo + "+", fontsize=7)
            y += 12
        else:
            p.insert_text((20, y), fecha, fontsize=8)
            p.insert_text((75, y), fecha, fontsize=8)
            partes = concepto.split("|")
            p.insert_text((130, y), partes[0], fontsize=8)
            p.insert_text((470 - len(importe) * 4.4, y), importe, fontsize=8)
            p.insert_text((575 - len(saldo) * 4.4, y), saldo, fontsize=8)
            for extra in partes[1:]:
                y += 10
                p.insert_text((130, y), extra, fontsize=8)
            y += 14
    doc.save(ruta)


@pytest.fixture
def expediente_prueba(tmp_path):
    """Crea un expediente completo a partir de la plantilla, con 3 facturas
    digitales, 1 escaneada y un extracto. Devuelve la ruta de la carpeta."""
    carpeta = tmp_path / "EXP PRUEBA"
    shutil.copytree(os.path.join(RAIZ, "Expedientes", "_PLANTILLA"), carpeta)
    fact = carpeta / "facturas"
    (fact / "veterinario").mkdir()
    pdf_factura(fact / "zooplus marzo.pdf", "367316231", "84,81")
    pdf_factura(fact / "veterinario" / "clinica CR-647.pdf", "CR/647", "18,00")
    pdf_factura(fact / "veterinario" / "clinica CR-758.pdf", "CR/758", "95,00")
    pdf_escaneado(fact / "veterinario" / "farmacia papel.pdf")
    pdf_factura(fact / "justificante pedido 367316231.pdf", "367316231", "84,81")  # no es la factura
    pdf_extracto(carpeta / "Documentacion" / "extracto bancario.pdf", [
        ("01/03/2025", "MARIA DONANTE PRIVADA ABONO BIZUM", "25,00", "2.025,00"),
        ("03/03/2025", "zooplus DE 36731623-Munchen TPV", "-84,81", "1.940,19"),
        ("04/03/2025", "SOCIA EJEMPLO TRANSFERENCIA", "84,81", "2.025,00"),
        ("05/03/2025", "C.VET.CLINICA/FUENLABRADA TPV", "-113,00", "1.912,00"),
        ("06/03/2025", "FARMACIA CENTRO TPV", "-12,50", "1.899,50"),
        ("07/03/2025", "TIENDA PERSONAL SIN RELACION TPV", "-40,00", "1.859,50"),
    ])
    # sin imagen de sello para no depender de archivos externos
    cfg_ruta = carpeta / "config.json"
    cfg = json.loads(cfg_ruta.read_text(encoding="utf-8"))
    cfg["sello"] = ""
    cfg["texto_sello"] = "ESTA FACTURA ESTA SUBVENCIONADA. CONVOCATORIA 2025; IMPORTE: {importe} € ({porcentaje})"
    cfg_ruta.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

    import openpyxl
    wb = openpyxl.load_workbook(carpeta / "Checklist.xlsx")
    ws = wb.worksheets[0]
    filas = [
        ["1", "Alimentación", "Zooplus SE", "367316231", "84,81", None, "Tarjeta", "03/03/2025"],
        ["2", "Veterinario", "Clínica Vet", "CR/647", 18, None, "Tarjeta", "05/03/2025"],
        ["3", "Veterinario", "Clínica Vet", "CR/758", "95,00", None, "Tarjeta", "05/03/2025"],
        ["4", "Veterinario", "Farmacia Centro", "A-55", "12,50", None, "Tarjeta", "06/03/2025",
         None, "veterinario\\farmacia papel.pdf"],
        ["5", "Veterinario", "Clínica Otra", "B-77", 40, None, "Efectivo", "08/03/2025"],
    ]
    for r, fila in enumerate(filas, 2):
        for c, v in enumerate(fila, 1):
            ws.cell(r, c).value = v
    wb.save(carpeta / "Checklist.xlsx")
    return carpeta
