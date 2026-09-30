"""Búsqueda de pagos en el extracto y de archivos de factura."""
import datetime as dt

import completar_checklist as cc


def mov(fecha, importe, cargo=True, concepto="X"):
    return {"fecha": dt.date.fromisoformat(fecha), "fecha_txt": dt.date.fromisoformat(fecha).strftime("%d/%m/%Y"),
            "importe": importe, "cargo": cargo, "concepto": concepto, "pag": 1}


def pend(num, importe, fecha, proveedor="P"):
    return {"num": num, "importe": importe, "fecha": dt.date.fromisoformat(fecha), "proveedor": proveedor}


def test_pago_exacto_y_no_confunde_con_ingreso_del_mismo_importe():
    movs = [mov("2024-04-17", 109.39, cargo=False, concepto="SOCIA REEMBOLSO"),
            mov("2024-04-19", 109.39, cargo=True, concepto="ZOOPLUS")]
    r = cc.buscar_pagos([pend("1", 109.39, "2024-04-16")], movs, set())
    assert "ZOOPLUS" in r["1"]


def test_fuera_de_la_ventana_de_dias_no_se_acepta():
    movs = [mov("2024-06-30", 50.0)]
    r = cc.buscar_pagos([pend("1", 50.0, "2024-06-01")], movs, set())
    assert r["1"] is None


def test_un_movimiento_no_se_usa_para_dos_facturas():
    movs = [mov("2024-10-14", 64.14), mov("2024-11-08", 64.14)]
    r = cc.buscar_pagos([pend("1", 64.14, "2024-10-14"), pend("2", 64.14, "2024-11-06")], movs, set())
    assert "14/10/2024" in r["1"] and "08/11/2024" in r["2"]


def test_cobro_conjunto_de_varias_facturas():
    movs = [mov("2024-06-14", 74.0, concepto="CLINICA")]
    r = cc.buscar_pagos([pend("13", 3, "2024-06-14", "Clínica"), pend("14", 68, "2024-06-14", "Clínica"),
                         pend("15", 3, "2024-06-14", "Clínica")], movs, set())
    assert all("cobro conjunto de nº 13 + 14 + 15" in r[n] for n in ("13", "14", "15"))


def test_diferencia_de_un_centimo_se_acepta_con_aviso():
    movs = [mov("2024-10-22", 207.12)]
    r = cc.buscar_pagos([pend("1", 207.13, "2024-10-21")], movs, set())
    assert "OJO: difiere 0,01 €" in r["1"]


def idx(**archivos):
    return {nombre: {"tipo": "DIGITAL", "tokens": cc.tokens(texto), "tokens_nombre": cc.tokens(nombre.split(".")[0])}
            for nombre, texto in archivos.items()}


def test_buscar_archivo_no_confunde_numeros_cortos_dentro_de_otros():
    """El nº de factura '468' no debe encontrarse dentro de '346864444'."""
    indice = idx(**{"zooplus 346864444.pdf": "Factura 346864444", "jaula.pdf": "FACTURA 468 Trampas y jaulas"})
    assert cc.buscar_archivo("468", indice)[0] == "jaula.pdf"


def test_buscar_archivo_prefiere_la_factura_al_justificante():
    indice = idx(**{"justificante pedido 402102.pdf": "Pedido 402102", "nutralgape mayo.pdf": "Factura 402102"})
    assert cc.buscar_archivo("402102", indice)[0] == "nutralgape mayo.pdf"


def test_buscar_archivo_con_barras_y_guiones():
    indice = idx(**{"avanzada rubita.pdf": "Nº: FRAR/41091 Fecha 17/05/24"})
    assert cc.buscar_archivo("FRAR/41091", indice)[0] == "avanzada rubita.pdf"
