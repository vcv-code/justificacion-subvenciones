"""
Lectura de la configuración de un expediente (una asociación + un año).

Cada expediente es una carpeta dentro de "Expedientes/" con un config.json
que indica dónde está cada cosa (rutas relativas a la carpeta del expediente).
Ver "Expedientes/ALGP 2024 - Fuenlabrada/config.json" como ejemplo.
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_EXPEDIENTES = os.path.join(RAIZ, "Expedientes")
RUTAS = ("checklist", "facturas_originales", "facturas_selladas", "sello", "extracto", "extracto_salida")

# el módulo del sellador vive en la carpeta de la herramienta (repositorio de GitHub)
sys.path.insert(0, os.path.join(RAIZ, "Herramienta sellado facturas"))


def cargar(nombre_o_ruta):
    """Acepta el nombre de la carpeta del expediente ("ALGP 2024 - Fuenlabrada")
    o una ruta a ella. Devuelve el config con las rutas ya absolutas."""
    carpeta = nombre_o_ruta
    if not os.path.isdir(carpeta):
        carpeta = os.path.join(CARPETA_EXPEDIENTES, nombre_o_ruta)
    ruta_config = os.path.join(carpeta, "config.json")
    if not os.path.isfile(ruta_config):
        disponibles = [d for d in os.listdir(CARPETA_EXPEDIENTES)
                       if os.path.isfile(os.path.join(CARPETA_EXPEDIENTES, d, "config.json"))]
        sys.exit(f"No encuentro '{ruta_config}'.\nExpedientes disponibles: {', '.join(disponibles)}")
    try:
        with open(ruta_config, encoding="utf-8") as f:
            cfg = json.load(f)
    except json.JSONDecodeError as e:
        sys.exit(f"El archivo config.json tiene un error de escritura en la línea {e.lineno}.\n"
                 "Suele ser una coma o unas comillas que faltan o sobran. Compáralo con el de "
                 "Expedientes/_PLANTILLA/config.json: cada línea es  \"nombre\": \"valor\",  "
                 "y la última línea antes de } no lleva coma.")
    for clave in ("checklist", "facturas_originales", "facturas_selladas"):
        if not cfg.get(clave):
            sys.exit(f"Al config.json le falta \"{clave}\". Cópialo de Expedientes/_PLANTILLA/config.json.")
    cfg["carpeta"] = os.path.abspath(carpeta)
    for clave in RUTAS:
        if cfg.get(clave):
            cfg[clave] = os.path.normpath(os.path.join(cfg["carpeta"], cfg[clave]))
    return cfg


# Títulos de columna del checklist que usan los scripts. Cada columna se busca
# por el principio de su título; "|" separa alternativas (títulos antiguos).
COL = {
    "num": "Nº justificante|Nº Anexo",
    "concepto": "Concepto",
    "proveedor": "Proveedor",
    "nfactura": "Nº factura",
    "importe": "Importe (€)|Importe sellado",
    "porcentaje": "% imputado",
    "texto": "TEXTO EXACTO DEL SELLO",
    "tipo": "Tipo",
    "que_hacer": "Qué hacer",
    "archivo": "Archivo original",
    "copia": "Copia sellada",
    "forma_pago": "Forma de pago",
    "fecha_pago": "Fecha pago",
    "importes_pagos": "Importe de cada pago",
    "pago": "Pago localizado",
    "sellada": "¿Sellada?",
    "notas": "Notas",
}


def columnas(cabecera):
    """{clave: índice de columna (0..n) o None si el checklist no la tiene}."""
    cab = [str(c or "").strip() for c in cabecera]
    res = {}
    for clave, titulos in COL.items():
        res[clave] = next((i for i, c in enumerate(cab) for t in titulos.split("|") if c.startswith(t)), None)
    return res


def a_numero(v):
    """Importe de una celda: admite número o texto con coma ('1.720,00', '61,93 €')."""
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace("€", "").replace(" ", "").strip()
    if "," in s:                              # 1.720,00 -> 1720.00
        return float(s.replace(".", "").replace(",", "."))
    if re.fullmatch(r"\d+\.\d{1,2}", s):      # 61.93 escrito con punto decimal
        return float(s)
    return float(s.replace(".", ""))          # 1.720 -> 1720
