"""Lectura de importes, fechas y extractos bancarios."""
import datetime as dt

import pytest

import banco
import expediente
from conftest import pdf_extracto


@pytest.mark.parametrize("texto, esperado", [
    ("61,93", 61.93),
    ("1.720,00", 1720.0),
    ("61.93", 61.93),       # escrito con punto decimal
    ("1.720", 1720.0),      # punto de miles
    ("84,81 €", 84.81),
    (12, 12.0),
    (None, None),
    ("", None),
])
def test_importes_del_checklist(texto, esperado):
    assert expediente.a_numero(texto) == esperado


@pytest.mark.parametrize("texto, esperado", [
    ("29,95-", (29.95, True)),
    ("-1.720,00", (1720.0, True)),
    ("216,00+", (216.0, False)),
    ("50,00", (50.0, None)),
    ("1234", None),          # no es un importe (sin decimales)
    ("12/03/2024", None),
])
def test_importes_del_extracto(texto, esperado):
    assert banco._importe(texto) == esperado


@pytest.mark.parametrize("texto, esperado", [
    ("14/06/2024", dt.date(2024, 6, 14)),
    ("14/06/24", dt.date(2024, 6, 14)),
    ("14-06-2024", dt.date(2024, 6, 14)),
    ("14.06.2024", dt.date(2024, 6, 14)),
    ("31/02/2024", None),    # fecha imposible
    ("hola", None),
])
def test_fechas_del_extracto(texto, esperado):
    assert banco._fecha(texto) == esperado


FILAS = [
    ("01/03/2025", "DONANTE ABONO BIZUM", "25,00", "2.025,00"),
    ("03/03/2025", "ZOOPLUS TPV", "-84,81", "1.940,19"),
    ("05/03/2025", "CLINICA TPV", "-113,00", "1.827,19"),
]


def test_extracto_formato_pueyo(tmp_path):
    ruta = tmp_path / "ext.pdf"
    pdf_extracto(ruta, FILAS, formato="pueyo")
    movs, paginas = banco.leer_movimientos(ruta)
    assert [(m["fecha_txt"], m["importe"], m["cargo"]) for m in movs] == [
        ("01/03/2025", 25.0, False), ("03/03/2025", 84.81, True), ("05/03/2025", 113.0, True)]
    assert "ZOOPLUS" in movs[1]["concepto"]


def test_extracto_otro_banco_dos_fechas_y_concepto_en_dos_lineas(tmp_path):
    ruta = tmp_path / "ext.pdf"
    filas = [("03/03/2025", "COMPRA TARJ. 1234 ZOOPLUS|FACTURA 367316231", "-84,81", "1.940,19"),
             ("04/03/2025", "TRANSF. DE DONANTE", "50,00", "1.990,19")]
    pdf_extracto(ruta, filas, formato="otro")
    movs, _ = banco.leer_movimientos(ruta)
    assert len(movs) == 2
    assert movs[0]["importe"] == 84.81 and movs[0]["cargo"] is True
    assert "FACTURA 367316231" in movs[0]["concepto"]        # continuación del concepto
    assert movs[1]["cargo"] is False                          # sin signo = ingreso
    assert movs[0]["rect"].y1 <= movs[1]["rect"].y0 + 0.01     # filas sin solaparse


def test_descripcion_y_clave_coinciden(tmp_path):
    """El texto que se guarda en el checklist debe poder leerse de vuelta."""
    ruta = tmp_path / "ext.pdf"
    pdf_extracto(ruta, FILAS)
    movs, _ = banco.leer_movimientos(ruta)
    m = movs[2]
    fecha, importe, pag = banco.RE_DESCRIPCION.search(banco.descripcion(m)).groups()
    assert (int(pag), fecha, importe) == banco.clave(m)
