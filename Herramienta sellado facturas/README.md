# Sellador de facturas PDF / PDF Invoice Stamper

🇪🇸 [Español](#español) · 🇬🇧 [English](#english)

---

## Español

Programa con ventana (no hace falta saber programar) para **estampar el texto
que exige una subvención** —por ejemplo *"ESTA FACTURA ESTA SUBVENCIONADA POR
EL AYUNTAMIENTO DE…; IMPORTE …€"*— y, si quieres, **el sello o logo de tu
entidad**, sobre un lote de facturas en PDF.

**Nunca modifica los PDF originales**: crea copias selladas en otra carpeta.

Nació para que una asociación de protección animal justificara una subvención
municipal (Ayuntamiento de Fuenlabrada, España), pero el texto y la imagen los
eliges tú, así que sirve para cualquier convocatoria, administración o país.

### ¿Por qué hay que sellar las facturas?

La normativa española de subvenciones (art. 73.2 del RD 887/2006) obliga a
marcar los justificantes con una estampilla que indique a qué subvención se
imputan y si lo hacen total o parcialmente. Así se evita que la misma factura
se presente en dos subvenciones distintas. Muchas convocatorias fijan además el
texto exacto que debe figurar.

- **Facturas digitales** (PDF recibido por correo o descargado): se sellan con
  este programa.
- **Facturas en papel**: lo que vale es el original, así que se sellan a mano
  y después se escanean.

### Características

- Carga PDFs sueltos o una carpeta entera.
- Texto del sello libre, con salto de línea automático, dentro de un recuadro.
- **Imagen del sello opcional** (PNG/JPG). El fondo blanco se vuelve
  transparente para que parezca tinta y no tape lo que hay debajo.
- **Colocación automática**: analiza cada página y busca un hueco en blanco
  (preferiblemente abajo a la derecha) donde el sello no tape texto, tablas
  ni logos de la factura. Primero prueba con la imagen a la izquierda del
  texto; si no cabe, con la imagen encima, y en último caso con la imagen
  más pequeña. Si no hay hueco libre, lo indica en el registro para que
  revises esa factura.
- También puedes elegir una posición fija: abajo/arriba × izquierda/centro/
  derecha, o el centro de la página.
- Texto y posición distintos para un archivo concreto (por ejemplo, para
  poner el importe de cada factura).
- Color (negro, rojo o azul) y tamaño de letra configurables.
- Sella solo la primera página o todas.
- Abre también PDFs protegidos sin contraseña de apertura (habitual en algunos
  programas de facturación).

### Instalación

Necesitas **Python 3.9 o superior** con tkinter. Viene incluido en los
instaladores de Windows y macOS de [python.org](https://www.python.org/downloads/).
En Windows, marca "Add python.exe to PATH" al instalar. En Linux puede hacer
falta el paquete `python3-tk`.

Luego, en una terminal y dentro de la **carpeta raíz del proyecto** (la de arriba):

```bash
pip install -r requirements.txt
```

Si `pip` no se reconoce, usa `python -m pip install -r requirements.txt`.

### Uso

```bash
python sellador_facturas.py
```

(En Windows también puedes hacer doble clic en `sellador_facturas.py`.)

1. **Añadir PDFs…** o **Añadir carpeta…** para cargar las facturas.
2. Escribe el **texto del sello** tal como lo exige tu convocatoria.
3. Deja la posición en **"Automática (buscar hueco libre)"** o elige una fija.
   Ajusta el color y el tamaño de letra si lo necesitas.
4. Opcional: en **"Imagen del sello / logo"** pulsa *Elegir…*, selecciona la
   imagen de tu sello e indica su alto en mm (26 mm va bien para A4).
5. Si una factura necesita otro texto (por ejemplo su importe) u otra
   posición, selecciónala en la lista, marca **"Usar texto/posición propios
   para este archivo"** y cámbialos. Aparecerá marcada con `*`.
6. Elige la carpeta de salida. Si no eliges ninguna, se crea `SELLADAS/` junto
   a las facturas.
7. Pulsa **Procesar todas**. El registro indica "REVISAR" en las facturas donde
   el sello no ha encontrado un hueco totalmente libre.

Abre siempre el resultado y revísalo antes de presentarlo.

### Uso desde Python (lotes grandes)

Si cada factura lleva un importe distinto, es más cómodo preparar los textos
en una hoja de cálculo y sellar desde un pequeño script:

```python
from sellador_facturas import OpcionesSello, sellar_pdf

opciones = OpcionesSello(
    texto="ESTA FACTURA ESTA SUBVENCIONADA POR ...; IMPORTE: 61,93 € (100%)",
    logo_ruta="mi_sello.jpg",   # opcional
    logo_alto_mm=26,
)                               # posición automática y color negro por defecto
avisos = sellar_pdf("factura.pdf", "SELLADAS/factura.pdf", opciones)
print(avisos or "OK")
```

### Privacidad

El programa funciona sin conexión: nada sale de tu ordenador. El `.gitignore`
del proyecto impide subir por error PDFs, hojas de cálculo, imágenes o expedientes.

### Licencia

MIT. Ver [LICENSE](../LICENSE).

---

## English

A small program with a graphical interface (no coding needed) that **stamps
the wording a grant requires** (e.g. *"This invoice was funded by…; amount
…€"*) and, optionally, **your organisation's stamp or logo** onto a batch of
PDF invoices.

**It never modifies the original PDFs**: it writes stamped copies to a
separate folder.

It was built for an animal-welfare association justifying a municipal grant
(Fuenlabrada City Council, Spain). The text and image are up to you, so it
works for any grant scheme, public body or country.

### Features

- Add individual PDFs or a whole folder.
- Free-form stamp text inside a box, with automatic line wrapping.
- **Optional stamp image** (PNG/JPG). The white background is made
  transparent, so it looks like ink and does not hide what is underneath.
- **Automatic placement**: each page is analysed to find a blank area
  (preferably bottom-right) where the stamp does not cover the invoice's
  text, tables or logos. It first tries the image to the left of the text,
  then the image above it, and finally a smaller image. If no fully free spot
  exists, the log flags that invoice for review.
- Fixed positions are also available: bottom/top × left/centre/right, or
  page centre.
- Per-file text and position overrides (e.g. each invoice's own amount).
- Configurable colour (black, red or blue) and font size.
- Stamp the first page only, or every page.
- Also opens PDFs that are protected but need no password to open (common
  with some invoicing software).

### Installation

Requires **Python 3.9+** with tkinter. It is bundled with the Windows and
macOS installers from [python.org](https://www.python.org/downloads/). On
Linux you may need the `python3-tk` package.

```bash
pip install -r requirements.txt   # from the project root folder
```

### Usage

```bash
python sellador_facturas.py
```

1. *Añadir PDFs…* / *Añadir carpeta…* (add PDFs / add folder).
2. Type the stamp text.
3. Keep the position on *"Automática (buscar hueco libre)"* (automatic) or
   pick a fixed one.
4. Optional: under *"Imagen del sello / logo"*, click *Elegir…* (choose) to
   select your stamp image and set its height in mm.
5. To give one file its own text or position, select it, tick *"Usar
   texto/posición propios para este archivo"* and edit them.
6. Choose the output folder (defaults to `SELLADAS/` next to the invoices).
7. Click *Procesar todas* (process all). Invoices marked "REVISAR" in the log
   need a manual check.

For large batches with a different amount on each invoice, call
`sellar_pdf()` from a script (see the Python example in the Spanish section).

### Privacy

Everything runs offline. The project's `.gitignore` prevents PDFs,
spreadsheets, images and case folders from being committed by mistake.

### License

MIT. See [LICENSE](../LICENSE).
