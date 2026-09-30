"""
Lectura de extractos bancarios en PDF (genérica, para la mayoría de bancos).

Funciona con el PDF que se DESCARGA de la banca online (tiene texto real). No
funciona con un extracto en papel escaneado (es una imagen sin texto).

Cómo reconoce un movimiento: una línea del PDF que tiene una FECHA
(dd/mm/aaaa, dd/mm/aa, dd-mm-aaaa o dd.mm.aaaa) y al menos un IMPORTE con
coma decimal (29,95 / 1.720,00 / -29,95 / 29,95-). Si hay varios importes en
la línea (importe y saldo), el primero es el del movimiento. Las líneas sin
fecha ni importe justo debajo se consideran continuación del concepto.

Signo: si el importe lleva "-" (delante o detrás) es un cargo (dinero que
sale). Si el banco no pone signos, el signo queda como desconocido y se
aceptan igualmente al buscar pagos.
"""
import datetime as dt
import re

import pymupdf

RE_FECHA = re.compile(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4}|\d{2})$")
RE_IMPORTE = re.compile(r"^([-+]?)((?:\d{1,3}(?:\.\d{3})+|\d+),\d{2})([-+]?)€?$")


def euros(v):
    """1234.5 -> '1.234,50'"""
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fecha(txt):
    m = RE_FECHA.match(txt)
    if not m:
        return None
    d, mes, a = (int(x) for x in m.groups())
    if a < 100:
        a += 2000
    try:
        return dt.date(a, mes, d)
    except ValueError:
        return None


def _importe(txt):
    """'-1.720,00' -> (1720.0, True); '29,95' -> (29.95, None)"""
    m = RE_IMPORTE.match(txt)
    if not m:
        return None
    pre, num, post = m.groups()
    valor = float(num.replace(".", "").replace(",", "."))
    signo = pre or post
    return valor, (True if signo == "-" else False if signo == "+" else None)


def _lineas(page):
    """Agrupa las palabras de la página en líneas (por su altura)."""
    # se descarta el texto girado (p. ej. avisos legales en vertical en el margen)
    girado = [pymupdf.Rect(l["bbox"]) for b in page.get_text("dict")["blocks"] for l in b.get("lines", [])
              if abs(l["dir"][1]) > 0.1]
    palabras = [w for w in page.get_text("words")
                if not any(r.contains(pymupdf.Point((w[0] + w[2]) / 2, (w[1] + w[3]) / 2)) for r in girado)]
    palabras.sort(key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    lineas = []
    for w in palabras:
        yc = (w[1] + w[3]) / 2
        if lineas and abs(lineas[-1]["yc"] - yc) < 2.5:
            lineas[-1]["words"].append(w)
        else:
            lineas.append({"yc": yc, "words": [w]})
    for l in lineas:
        l["words"].sort(key=lambda w: w[0])
        l["rect"] = pymupdf.Rect(min(w[0] for w in l["words"]), min(w[1] for w in l["words"]),
                                 max(w[2] for w in l["words"]), max(w[3] for w in l["words"]))
    return lineas


def leer_movimientos(ruta_pdf):
    """Devuelve (movimientos, paginas).
    movimientos: lista de dicts con fecha (date), fecha_txt ('dd/mm/aaaa'),
      concepto, importe (float), cargo (True/False/None), pag (1..n), rect
      (zona de la fila en la página, incluida la continuación del concepto).
    paginas: por página, {'x0','x1'} = anchura de la tabla de movimientos."""
    doc = pymupdf.open(ruta_pdf)
    movimientos, paginas = [], []
    for pno, page in enumerate(doc, 1):
        lineas = _lineas(page)
        bloques = []
        for l in lineas:
            textos = [w[4] for w in l["words"]]
            fecha = next((f for t in textos[:4] if (f := _fecha(t))), None)
            importes = [(i, imp) for i, t in enumerate(textos) if (imp := _importe(t))]
            if fecha and importes:
                i_imp, (valor, cargo) = importes[0]
                i_fecha = next(i for i, t in enumerate(textos) if _fecha(t))
                concepto = " ".join(t for t in textos[i_fecha + 1:i_imp] if not _fecha(t))
                bloques.append({"fecha": fecha, "concepto": concepto, "importe": valor, "cargo": cargo,
                                "pag": pno, "lineas": [l]})
            elif bloques and not importes and not fecha:
                ultima = bloques[-1]["lineas"][-1]
                alto = ultima["rect"].height or 8
                if l["yc"] - ultima["yc"] < 2.2 * alto:  # continuación del concepto
                    bloques[-1]["lineas"].append(l)
                    bloques[-1]["concepto"] += " " + " ".join(w[4] for w in l["words"])
        if not bloques:
            paginas.append(None)
            continue
        x0 = min(l["rect"].x0 for b in bloques for l in b["lineas"]) - 2
        x1 = max(l["rect"].x1 for b in bloques for l in b["lineas"]) + 2
        paginas.append({"x0": x0, "x1": x1})
        # rectángulo de cada movimiento, sin invadir el de al lado
        tops = [min(l["rect"].y0 for l in b["lineas"]) for b in bloques]
        bottoms = [max(l["rect"].y1 for l in b["lineas"]) for b in bloques]
        for i, b in enumerate(bloques):
            pad = 2.5
            if i > 0:
                pad = min(pad, max(0.5, (tops[i] - bottoms[i - 1]) / 2))
            if i + 1 < len(bloques):
                pad = min(pad, max(0.5, (tops[i + 1] - bottoms[i]) / 2))
            b["rect"] = pymupdf.Rect(x0, tops[i] - pad, x1, bottoms[i] + pad)
            b["fecha_txt"] = b["fecha"].strftime("%d/%m/%Y")
            del b["lineas"]
            movimientos.append(b)
    # si el banco marca los cargos con "-" y nunca pone "+", lo que no lleva
    # signo son ingresos
    signos = {m["cargo"] for m in movimientos}
    if True in signos and False not in signos:
        for m in movimientos:
            if m["cargo"] is None:
                m["cargo"] = False
    return movimientos, paginas


def descripcion(m):
    """Texto que se guarda en el checklist para un movimiento."""
    signo = "-" if m["cargo"] is not False else "+"
    return f"{m['fecha_txt']} · {m['concepto'].strip()} · {signo}{euros(m['importe'])} € (pág. {m['pag']})"


RE_DESCRIPCION = re.compile(r"(\d\d/\d\d/\d{4}) · .*? · [-+]([\d.]+,\d\d) € \(pág\. (\d+)\)")


def clave(m):
    return (m["pag"], m["fecha_txt"], euros(m["importe"]))
