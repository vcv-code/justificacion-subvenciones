"""
Menú sencillo para usar las herramientas sin escribir comandos.
Se abre con doble clic en INICIAR.bat (carpeta raíz del proyecto).
"""
import importlib.util
import os
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
EXPEDIENTES = os.path.join(RAIZ, "Expedientes")
PLANTILLA = os.path.join(EXPEDIENTES, "_PLANTILLA")
HERRAMIENTA = os.path.join(RAIZ, "Herramienta sellado facturas")


def preguntar(texto):
    """input() que ignora caracteres invisibles y cierra limpio si no hay teclado."""
    try:
        return input(texto).replace("\ufeff", "").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)


def linea():
    print("-" * 70)


def comprobar_librerias():
    necesarias = ("numpy", "openpyxl", "PIL", "pymupdf", "pypdf", "reportlab", "cryptography")
    if all(importlib.util.find_spec(m) for m in necesarias):
        return True
    print("Faltan librerías de Python (es normal la primera vez en un ordenador).")
    if preguntar("¿Instalarlas ahora? Necesita internet. (s/n): ").strip().lower() != "s":
        return False
    subprocess.call([sys.executable, "-m", "pip", "install", "-r", os.path.join(RAIZ, "requirements.txt")])
    print("\nInstalación terminada. Si ha salido algún error en rojo, avisa a quien mantenga esto.")
    return True


def lista_expedientes():
    return sorted(d for d in os.listdir(EXPEDIENTES)
                  if not d.startswith("_") and os.path.isfile(os.path.join(EXPEDIENTES, d, "config.json")))


def crear_expediente():
    print("\nNombre del expediente nuevo. Recomendado: SIGLAS AÑO - AYUNTAMIENTO")
    print("Ejemplo: ALGP 2025 - Fuenlabrada")
    nombre = preguntar("Nombre: ").strip()
    if not nombre:
        return None
    if any(ch in nombre for ch in '\\/:*?"<>|'):
        print('El nombre no puede llevar ninguno de estos caracteres: \\ / : * ? " < > |')
        return None
    destino = os.path.join(EXPEDIENTES, nombre)
    if os.path.exists(destino):
        print("Ya existe un expediente con ese nombre.")
        return None
    shutil.copytree(PLANTILLA, destino)
    print(f"\nCreado: {destino}")
    print("Ahora, siguiendo el README (apartado 'Paso a paso'):")
    print("  1. Mete las facturas en la carpeta 'facturas'.")
    print("  2. Mete el extracto bancario en 'Documentacion' con el nombre 'extracto bancario.pdf'.")
    print("  3. Pon la imagen del sello como 'sello.jpg' (o borra la línea del sello en config.json).")
    print("  4. Edita config.json: cambia el texto del sello (texto_sello).")
    print("  5. Rellena lo AMARILLO del Checklist.xlsx.")
    abrir(destino)
    return nombre


def abrir(ruta):
    try:
        os.startfile(ruta)  # Windows
    except AttributeError:
        subprocess.call(["open" if sys.platform == "darwin" else "xdg-open", ruta])


def ejecutar(script, *args):
    linea()
    codigo = subprocess.call([sys.executable, os.path.join(AQUI, script), *args])
    linea()
    if codigo != 0:
        print("Ha terminado con un problema: lee los mensajes de arriba.")
    preguntar("Pulsa Enter para volver al menú...")


def menu_expediente(nombre):
    carpeta = os.path.join(EXPEDIENTES, nombre)
    while True:
        print(f"\n=== Expediente: {nombre} ===")
        print("  1. Completar checklist (buscar archivos, tipo, texto del sello y pagos)")
        print("  2. Sellar las facturas digitales")
        print("  3. Preparar el extracto bancario (solo los pagos, con nº de justificante)")
        print("  4. Preparar la entrega: un solo PDF con índice, facturas y justificantes")
        print("  5. Abrir la carpeta del expediente")
        print("  6. Abrir el checklist (Excel)")
        print("  0. Volver")
        op = preguntar("Elige una opción: ").strip()
        if op == "1":
            print("\nRecuerda: el Excel del checklist tiene que estar CERRADO.")
            print("Normalmente solo se rellena lo que esté vacío. Si cambiaste importes o fechas, puedes")
            print("RECALCULAR: se sobrescriben las columnas grises (tipo, texto, copia, pagos), también")
            print("lo que hubieras corregido a mano en ellas. Antes se guarda una copia del checklist.")
            rehacer = preguntar("¿Recalcular? (s/N): ").strip().lower() == "s"
            ejecutar("completar_checklist.py", carpeta, *(["--rehacer"] if rehacer else []))
        elif op == "2":
            ejecutar("sellar_facturas_lote.py", carpeta)
            print("Revisa las hojas de miniaturas en la subcarpeta '_revision' de las selladas.")
        elif op == "3":
            ejecutar("preparar_extracto_pagos.py", carpeta)
        elif op == "4":
            ejecutar("preparar_entrega.py", carpeta)
        elif op == "5":
            abrir(carpeta)
        elif op == "6":
            sys.path.insert(0, AQUI)
            import expediente
            abrir(expediente.cargar(carpeta)["checklist"])
        elif op == "0":
            return
        else:
            print("Opción no válida.")


def main():
    print("=" * 70)
    print("  JUSTIFICACIÓN DE SUBVENCIONES - menú")
    print("=" * 70)
    if not comprobar_librerias():
        return
    while True:
        exps = lista_expedientes()
        print("\nExpedientes:")
        for i, e in enumerate(exps, 1):
            print(f"  {i}. {e}")
        print("  N. Crear un expediente nuevo (a partir de la plantilla)")
        print("  S. Abrir el programa de sellado con ventana (facturas sueltas)")
        print("  0. Salir")
        op = preguntar("Elige una opción: ").strip().lower()
        if op == "0":
            return
        if op == "n":
            nuevo = crear_expediente()
            if nuevo:
                preguntar("\nCuando hayas preparado todo, pulsa Enter para ir a su menú...")
                menu_expediente(nuevo)
        elif op == "s":
            subprocess.Popen([sys.executable, os.path.join(HERRAMIENTA, "sellador_facturas.py")])
        elif op.isdigit() and 1 <= int(op) <= len(exps):
            menu_expediente(exps[int(op) - 1])
        else:
            print("Opción no válida.")


if __name__ == "__main__":
    main()
