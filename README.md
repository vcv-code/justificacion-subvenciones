# Justificación de subvenciones — guía completa

Herramientas para preparar la justificación de una subvención pública:

- **sellar las facturas en PDF** con el texto obligatorio ("ESTA FACTURA ESTA
  SUBVENCIONADA POR…; IMPORTE…€") y el sello de la asociación;
- **preparar el extracto bancario** para demostrar los pagos, dejando a la
  vista solo los pagos de las facturas, con su número de justificante al
  lado, y borrando lo demás;
- llevar un **checklist** (Excel) con todo controlado.

Está pensado para usarse **sin saber programar**: todo se maneja desde un
menú con doble clic en `INICIAR.bat`.

---

## Índice

1. [Qué hay en esta carpeta](#1-qué-hay-en-esta-carpeta)
2. [Instalar (una sola vez por ordenador)](#2-instalar-una-sola-vez-por-ordenador)
3. [Paso a paso para justificar una subvención](#3-paso-a-paso-para-justificar-una-subvención)
4. [Lista de cosas que NO se pueden olvidar](#4-lista-de-cosas-que-no-se-pueden-olvidar)
5. [Si algo falla](#5-si-algo-falla)
6. [Preguntas frecuentes](#6-preguntas-frecuentes)
7. [Para quien quiera saber más (uso avanzado)](#7-para-quien-quiera-saber-más-uso-avanzado)

---

## 1. Qué hay en esta carpeta

```text
justificacionSubv/
├─ INICIAR.bat                    ← DOBLE CLIC AQUÍ para abrir el menú
├─ README.md                      ← esta guía
├─ Expedientes/                   ← una carpeta por cada justificación (asociación + año)
│  ├─ _PLANTILLA/                 ← modelo vacío (el menú la copia al crear uno nuevo)
│  └─ (tus expedientes)           ← p. ej. "ALGP 2025 - Fuenlabrada" (NUNCA se suben a GitHub)
├─ Scripts/                       ← los programas que usa el menú (no hace falta tocarlos)
├─ Herramienta sellado facturas/  ← programa con ventana para sellar facturas sueltas
├─ tests/                         ← pruebas automáticas (solo para quien modifique el código)
├─ requirements.txt               ← librerías de Python necesarias
└─ LICENSE                        ← licencia MIT (uso libre)
```

Cada **expediente** (por ejemplo `ALGP 2025 - Fuenlabrada`) tiene siempre lo mismo:

| Dentro del expediente | Qué es |
|---|---|
| `facturas/` | Todas las facturas en PDF, **tal como las tienes**. Nunca se modifican. |
| `facturas SELLADAS/` | Aquí salen las copias selladas. Dentro, `_revision/` tiene hojas con miniaturas para revisarlas rápido. |
| `Documentacion/` | El extracto bancario (PDF) y los papeles del ayuntamiento. |
| `Justificantes de pago/` | Aquí sale el extracto "limpio" y van los recibos de pagos en efectivo. |
| `Checklist.xlsx` | La lista de facturas: la rellenas tú en parte y el programa completa el resto. |
| `config.json` | Los ajustes del expediente: texto del sello, nombres de archivos, etc. |
| `sello.jpg` | La imagen del sello de la asociación (la pones tú). |

---

## 2. Instalar (una sola vez por ordenador)

1. **Instala Python.** Descárgalo de <https://www.python.org/downloads/> (botón
   amarillo "Download Python"). Al instalarlo:
   - ⚠️ **marca la casilla "Add python.exe to PATH"**, que está abajo en la
     primera pantalla. Si no la marcas, nada funcionará;
   - pulsa "Install Now" y espera.
2. **Haz doble clic en `INICIAR.bat`.** La primera vez te dirá que faltan
   librerías y preguntará si instalarlas: escribe `s` y pulsa Enter. Necesita
   internet y tarda uno o dos minutos. Luego se abre el menú.

Si Windows muestra "Windows protegió su PC" al abrir `INICIAR.bat`, pulsa
"Más información" y luego "Ejecutar de todas formas". Es normal con archivos
`.bat` descargados o copiados.

---

## 3. Paso a paso para justificar una subvención

### Paso 0 — Reúne esto antes de empezar

- [ ] **Las facturas** que se justificaron, en PDF. Las que solo tengas en
  papel, **escanéalas en color** a PDF (con el móvil sirve: apps como
  "Adobe Scan" o la cámara de Google Drive).
- [ ] **La relación de justificantes** que se entregó al ayuntamiento (en
  Fuenlabrada, el "Anexo 8"): nº de justificante, proveedor, nº de factura,
  importe, fecha y forma de pago de cada factura. Mejor si la tienes en Excel.
- [ ] **El extracto bancario en PDF descargado de la banca online** (no
  escaneado), que cubra todo el periodo de los pagos. En la web o app del
  banco suele estar en "Movimientos → Descargar / Exportar → PDF".
- [ ] **La imagen del sello** de la asociación: estampa el sello en un folio
  blanco, hazle una foto o escanéalo, y recórtalo dejando poco blanco
  alrededor. Vale JPG o PNG.
- [ ] **El texto exacto** que exige la convocatoria. Suele venir en las bases
  o en el requerimiento.

### Paso 1 — Crea el expediente

1. Doble clic en `INICIAR.bat`.
2. Escribe `N` y Enter ("Crear un expediente nuevo").
3. Escribe el nombre, por ejemplo `ALGP 2025 - Fuenlabrada`, y Enter.
4. Se abre la carpeta nueva. Deja la ventana negra del menú abierta.

### Paso 2 — Mete las facturas

Copia todas las facturas en PDF dentro de `facturas/`. Puedes usar
subcarpetas (por ejemplo `comida`, `veterinarios`…) y **no hace falta
cambiarles el nombre**. Puedes borrar el archivo `PON AQUI LAS FACTURAS.txt`.

### Paso 3 — Mete el extracto bancario

Copia el PDF del extracto en `Documentacion/` y **cámbiale el nombre a
`extracto bancario.pdf`**. Si tienes varios extractos (varios meses), lee
[la pregunta frecuente](#tengo-el-extracto-en-varios-pdf).

### Paso 4 — Pon la imagen del sello

Copia la imagen en la carpeta del expediente (no en una subcarpeta) y
llámala `sello.jpg`. Si es PNG, llámala `sello.png` y cámbialo también en
`config.json` (paso 5). Si no quieres poner imagen, en el paso 5 deja la
línea así: `"sello": "",`

No te preocupes por el fondo blanco: el programa lo vuelve transparente.

### Paso 5 — Revisa `config.json` (el texto del sello)

Clic derecho en `config.json` → "Abrir con" → **Bloc de notas**. Verás algo así:

```json
  "texto_sello": "ESTA FACTURA ESTA SUBVENCIONADA POR EL AYUNTAMIENTO DE ....... CONVOCATORIA 20XX; IMPORTE: {importe} € ({porcentaje})",
```

- Cambia `.......` y `20XX` por lo que diga tu convocatoria. **Copia el texto
  exacto** de las bases o del requerimiento.
- **No borres `{importe}` ni `{porcentaje}`**, con sus llaves: ahí el
  programa pone el importe de cada factura (61,93) y el porcentaje (100%).
- Respeta las comillas `"` y la coma del final de la línea.
- Si has cambiado algún nombre de carpeta o archivo, cámbialo también aquí.
- Guarda con Ctrl+G (o Archivo → Guardar) y cierra.

### Paso 6 — Rellena el checklist (solo las columnas amarillas)

Abre `Checklist.xlsx`. **Una fila por factura.** Los títulos tienen colores:

| Color del título | Quién lo rellena |
|---|---|
| 🟨 **Amarillo** | **Tú.** Puedes copiar y pegar desde tu Excel de la relación de justificantes. |
| ⬜ **Gris** | **El programa** (paso 7). Déjalo vacío. |
| 🟩 **Verde** | **Tú, al final**, cuando revises. |

Pasa el ratón por encima de cada título para ver qué poner. La pestaña
"Cómo rellenarlo" tiene un ejemplo. Lo imprescindible:

- **Nº justificante**: el número de la factura en la relación entregada.
- **Proveedor**, **Nº factura** (tal cual aparece en la factura) e
  **Importe (€)**, con coma decimal: `61,93`.
- **Forma de pago**: se elige de una lista.
- **Fecha pago**: `dd/mm/aaaa`.

Casos especiales:

- **Una factura pagada en dos veces** (ocupa dos líneas en la relación):
  una sola fila con Nº justificante `38, 48`, Fecha pago
  `02/09/2024; 08/10/2024` e Importe de cada pago `347,00; 436,80`. En
  Importe (€) va el total.
- **Varias facturas pagadas juntas** en un solo cobro: no hagas nada
  especial. El programa lo detecta si tienen el mismo proveedor y la misma
  fecha de pago.

⚠️ **Guarda y CIERRA el Excel** antes del paso siguiente.

### Paso 7 — "Completar checklist" (menú, opción 1)

En el menú, elige el expediente y luego la **opción 1**. El programa:

- busca el PDF de cada factura por su número;
- mira si cada PDF es **digital** o **escaneado (papel)**;
- escribe el **texto del sello** con el importe de cada factura;
- pone el **nombre de la copia sellada**;
- **busca cada pago en el extracto**.

Antes de tocar nada, guarda una copia del checklist anterior por si acaso
(`Checklist (copia antes de completar).xlsx`).

Al terminar muestra un resumen. Qué hacer con cada aviso:

| Aviso | Qué hacer |
|---|---|
| "no encuentro el PDF de la factura…" | Pasa sobre todo con las escaneadas, que no tienen texto. Abre el Excel y escribe en **Archivo original** la ruta dentro de `facturas/`, por ejemplo `veterinarios\factura farmacia mayo.pdf`. Truco: en el Explorador, Mayús + clic derecho sobre el archivo → "Copiar como ruta", pégalo y borra el principio hasta `facturas\` incluido. |
| Pagos NO localizados (en rojo) | Busca tú el pago en el extracto y escríbelo en esa celda con el formato `14/06/2024 · CONCEPTO · -74,00 € (pág. 2)`. Las causas típicas: una fecha mal puesta, que se pagó desde otra cuenta, o que el importe cobrado es distinto del de la factura. |
| "PDF de la carpeta que no están en el checklist" | Normalmente albaranes, justificantes o duplicados. Échales un vistazo por si falta alguna factura en el checklist. |
| Notas `[auto]` en el Excel | Comprueba que el archivo encontrado es la factura correcta. |

Cuando corrijas cosas, **guarda, cierra el Excel y vuelve a ejecutar la
opción 1**. Solo rellena lo que siga vacío; no borra lo que hayas escrito.
Si has cambiado importes o fechas y quieres que recalcule todo, responde `s`
cuando pregunte "¿Recalcular también lo que ya estaba relleno?".

### Paso 8 — "Sellar las facturas digitales" (menú, opción 2)

Crea en `facturas SELLADAS/` una copia sellada de cada factura **DIGITAL**,
con el texto y la imagen del sello **colocados solos en un hueco libre** de
la factura. Empiezan por el nº de justificante (`01 - …`, `02 - …`), así que
quedan en orden.

**Revisa el resultado**: en `facturas SELLADAS/_revision/` hay imágenes
`tanda_01.png`, `tanda_02.png`… con 12 miniaturas cada una. Mira que ningún
sello tape nada importante (importe, fecha, nº de factura). Si en el menú
alguna salió con "REVISAR", ábrela con más calma. Para mover el sello de una
factura concreta, lee [la pregunta frecuente](#el-sello-de-una-factura-tapa-algo).

### Paso 9 — Las facturas en papel (a mano)

Las marcadas como **ESCANEADA (papel)** (filas en amarillo) no las sella el
programa, porque lo que vale es el **papel original**:

1. Coge el **papel original** de la factura.
2. Estampa el **sello** de la asociación y escribe a mano (o pega impreso) el
   **texto exacto** de la columna "TEXTO EXACTO DEL SELLO", con su importe.
3. **Escanéalo en color** a PDF.
4. Guárdalo en `facturas SELLADAS/` con **el nombre de la columna "Copia
   sellada"** (así queda en su sitio en el orden).

### Paso 10 — "Preparar el extracto bancario" (menú, opción 3)

Crea en `Justificantes de pago/` una copia del extracto en la que:

- solo se ven los movimientos que pagan las facturas, **recuadrados en rojo y
  con su nº de justificante al lado**;
- **todo lo demás se borra de verdad** (sale en gris). Así no se ven donantes,
  socios ni otras compras.

**Ábrelo y revísalo página a página**: que estén todos los pagos y que no se
vea nada que no deba verse. El extracto original no se toca: **guárdalo**, por
si el ayuntamiento pide el completo.

### Paso 11 — Pagos en efectivo

Los pagos en efectivo no salen en el banco. Para cada uno, pide al proveedor
un **recibo firmado** ("recibí de la Asociación X la cantidad de… por la
factura nº…") y guárdalo escaneado en `Justificantes de pago/`.

### Paso 12 — Revisa y entrega

- Repasa el checklist fila a fila y marca las columnas verdes (**¿Sellada?**,
  **¿Pago acreditado?**).
- Lo que se entrega normalmente:
  1. todas las facturas selladas de `facturas SELLADAS/` (sin la carpeta
     `_revision`);
  2. el extracto limpio de `Justificantes de pago/` y los recibos de
     efectivo.
- Guarda una copia de todo el expediente (por ejemplo, comprimido en ZIP)
  cuando lo envíes.

---

## 4. Lista de cosas que NO se pueden olvidar

### Antes de empezar

- [ ] Mirar el **plazo** del requerimiento (suelen ser 10 días hábiles) y
  apuntarlo.
- [ ] Usar la **numeración de la relación de justificantes que se
  entregó** (la versión definitiva, si hubo subsanación), no la de un
  borrador.
- [ ] Copiar el **texto del sello exacto** de las bases o del requerimiento.
- [ ] Pedir el **extracto en PDF descargado** (no una foto ni un escaneo) que
  cubra **todas** las fechas de pago.

### Mientras trabajas

- [ ] **Cerrar el Excel** antes de usar las opciones del menú.
- [ ] Las facturas **en papel se sellan a mano sobre el original** y se
  escanean **en color**. Las digitales las sella el programa.
- [ ] Si una factura ocupa **dos números** en la relación (se pagó en dos
  veces), **se sella una sola vez con el total** y se escribe `38, 48`.
- [ ] Una factura **no puede justificarse en dos subvenciones distintas**:
  para eso sirve el sello.
- [ ] Pagos en **efectivo**: recibo firmado por el proveedor. Y ojo: muchas
  convocatorias **no admiten pagos en efectivo de 1.000 € o más** al mismo
  proveedor.
- [ ] Revisar las **miniaturas** (`_revision`) y el **extracto limpio** antes
  de enviarlos.
- [ ] Apuntar en la columna **Notas** cualquier cosa rara (erratas en la
  relación, importes que no cuadran por céntimos…). Así no se olvida si
  preguntan.

### Al terminar

- [ ] Guardar el **extracto completo** (sin tapar) por si lo piden.
- [ ] Guardar una **copia de seguridad** de todo el expediente (ZIP).
- [ ] **No subir nunca** facturas, extractos ni checklists a internet (GitHub,
  etc.): tienen datos personales.

---

## 5. Si algo falla

| Qué pasa | Solución |
|---|---|
| Al abrir `INICIAR.bat`: "No encuentro Python" | Instala Python ([apartado 2](#2-instalar-una-sola-vez-por-ordenador)) **marcando "Add python.exe to PATH"**. Si ya estaba instalado sin esa casilla, vuelve a ejecutar el instalador → "Modify" → siguiente → marca "Add Python to environment variables". |
| "Faltan librerías" y la instalación da error | Comprueba la conexión a internet y vuelve a abrir `INICIAR.bat`. |
| "No puedo abrir / guardar el checklist" | El Excel está abierto: **ciérralo** (mira también la barra de tareas) y repite. |
| "config.json tiene un error de escritura en la línea X" | Falta o sobra una coma o unas comillas en esa línea. Compáralo con `Expedientes/_PLANTILLA/config.json`. |
| "No encuentro la imagen del sello" | La imagen no está en la carpeta del expediente o tiene otro nombre. Revisa la línea `"sello"` de `config.json`. |
| "No reconozco movimientos en el extracto" | El extracto es un escaneo o una foto, no el PDF descargado. Descárgalo de la banca online. Si aun así no funciona, el formato de ese banco es muy raro: ver el [apartado 7](#7-para-quien-quiera-saber-más-uso-avanzado). |
| Muchos pagos "NO LOCALIZADO" | Comprueba que el extracto cubre esas fechas y que las fechas de pago del checklist son correctas. El programa busca hasta 10 días antes o después. |
| En el extracto limpio se ve algo que no debería | **No lo envíes.** Puede pasar si el banco pone movimientos en un formato raro. Tapa esa parte con otro programa o avisa a quien mantenga esto. |
| Una factura sale con "ERROR" al sellar | Puede ser un PDF dañado o protegido con contraseña. Ábrela, "Imprimir → Microsoft Print to PDF" para hacer una copia limpia, usa esa copia y repite. |
| Una factura digital salió como ESCANEADA (o al revés) | Corrige a mano la columna **Tipo** en el Excel (`DIGITAL` o `ESCANEADA (papel)`) y repite la opción 1 con "recalcular" = `n`. |

---

## 6. Preguntas frecuentes

### El sello de una factura tapa algo

Abre `config.json` y, en `ajustes_posicion`, indica el nº de justificante y
dónde ponerlo:

```json
  "ajustes_posicion": {"13": {"posicion": "Arriba derecha"}}
```

Posiciones posibles: `Abajo derecha`, `Abajo centro`, `Abajo izquierda`,
`Arriba derecha`, `Arriba centro`, `Arriba izquierda`, `Centro`. También
vale una posición exacta en milímetros desde la esquina inferior izquierda:
`{"20": {"x_manual_mm": 120, "y_manual_mm": 40}}`. Para varias facturas,
sepáralas con comas: `{"13": {...}, "20": {...}}`. Luego repite la opción 2.

### Tengo el extracto en varios PDF

Lo más fácil es juntarlos en uno solo con cualquier herramienta de "unir
PDF" (por ejemplo, <https://www.ilovepdf.com/es/unir_pdf> o PDF24) y
llamarlo `extracto bancario.pdf`. Ojo: el extracto tiene datos privados;
mejor una herramienta que funcione en tu ordenador, como PDF24 Creator.

### ¿Vale el extracto como justificante de pago?

Sí. Un cargo en la cuenta de la asociación con fecha, comercio e importe es
la prueba habitual, sobre todo para los pagos con tarjeta sin ticket. Tapar
los movimientos que no tienen que ver es razonable, porque contienen datos
de terceros. Pero guarda siempre el extracto completo por si lo piden.

### ¿Por qué hay que sellar las facturas?

Lo exige la normativa de subvenciones (art. 73.2 del RD 887/2006): cada
factura se marca indicando a qué subvención se imputa y si es total o
parcialmente. Así no se puede presentar la misma factura en dos
subvenciones. Por eso el texto lleva el importe y el porcentaje.

### ¿Puedo sellar una sola factura suelta?

Sí: en el menú, `S` abre el programa con ventana (explicado en
`Herramienta sellado facturas/LEEME.txt`).

### ¿Puedo cambiar algo del checklist?

Puedes añadir columnas y escribir en Notas. **No cambies los títulos** de las
columnas existentes: el programa las encuentra por su título.

---

## 7. Para quien quiera saber más (uso avanzado)

**Comandos** (sin menú), desde esta carpeta:

```powershell
python Scripts\completar_checklist.py "ALGP 2025 - Fuenlabrada" [--rehacer]
python Scripts\sellar_facturas_lote.py "ALGP 2025 - Fuenlabrada" [desde hasta]
python Scripts\preparar_extracto_pagos.py "ALGP 2025 - Fuenlabrada"
```

**Qué hace cada script** (`Scripts/`):

| Script | Función |
|---|---|
| `menu.py` | El menú de `INICIAR.bat`. |
| `completar_checklist.py` | Rellena las columnas grises del checklist. |
| `sellar_facturas_lote.py` | Sella las facturas DIGITALES con el texto de su fila. |
| `preparar_extracto_pagos.py` | Genera el extracto limpio. |
| `banco.py` | Lee los movimientos de un extracto en PDF (cualquier banco, en principio). |
| `expediente.py` | Lee el `config.json` y localiza las columnas del checklist. |

**Cómo reconoce el extracto** (`banco.py`): busca líneas que tengan una
fecha (`dd/mm/aaaa`, `dd/mm/aa`, `dd-mm-aaaa`…) y un importe con coma
decimal. El primer importe de la línea es el del movimiento (el siguiente
suele ser el saldo). Si lleva `-` es un cargo. Si el banco solo pone `-` en
los cargos, lo que no lleva signo se toma como ingreso. Las líneas justo
debajo sin fecha ni importe se consideran continuación del concepto. Se ha
probado con Banca Pueyo y con un formato típico de otros bancos (dos
fechas, signo delante, conceptos en dos líneas). **Con un banco nuevo,
revisa siempre el primer extracto limpio.** Si no reconoce bien las filas, el
ajuste se hace en `banco.py`.

**Detección digital / escaneada**: una factura se considera escaneada si
alguna página es una imagen que ocupa casi toda la hoja y no tiene texto
real (o lo ha creado un escáner).

**Colocación del sello**: el programa dibuja la página en pequeño, busca la
zona en blanco más cercana a la esquina inferior derecha donde quepan el
texto y la imagen, y si no cabe prueba con la imagen encima o más pequeña.

**`config.json`**, todas las opciones:

| Clave | Significado |
|---|---|
| `checklist` | Nombre del Excel del checklist. |
| `facturas_originales` / `facturas_selladas` | Carpetas de facturas originales y de copias selladas. |
| `sello`, `sello_alto_mm` | Imagen del sello (`""` = sin imagen) y su alto en mm (26 va bien en A4). |
| `texto_sello` | Texto del sello, con `{importe}` y `{porcentaje}`. |
| `extracto`, `extracto_salida` | Extracto original y dónde guardar el limpio. |
| `nota_extracto` | Frase que se escribe arriba del extracto limpio. |
| `ajustes_posicion` | Posición del sello forzada para facturas concretas. |

**Pruebas automáticas** (`tests/`): comprueban con datos **inventados**
(facturas y extractos de mentira que se crean al momento) la lectura de
importes, fechas y extractos, la búsqueda de pagos y archivos, el sellado y el
flujo completo de un expediente. Si modificas algo, sobre todo `banco.py`
para adaptarlo a otro banco, ejecútalas para ver que no se ha roto nada:

```powershell
python -m pip install pytest     # una vez
python -m pytest                 # desde la carpeta raíz; deben salir todas "passed"
```

**Privacidad**: los expedientes tienen datos personales y no se publican. El
`.gitignore` excluye `Expedientes/` (salvo la plantilla vacía) y cualquier
PDF, hoja de cálculo o imagen, para que no se suban por error a GitHub.

**Subir cambios a GitHub** (solo si has modificado el código o las guías),
desde PowerShell en la carpeta raíz:

```powershell
git status                          # revisa: ningún archivo de un expediente real
git add -A
git commit -m "Qué has cambiado"
git push                            # ya no pide contraseña: la sesión quedó guardada
```

⚠️ **Nunca uses `git add -f`**: se salta el `.gitignore` y podría subir
facturas o extractos reales. Si algo real se sube por error, borrarlo después
no basta, porque queda en el historial: habría que limpiar el historial o borrar
el repositorio.

---

## Licencia y origen

Hecho por la **Asociación La Gata Pirata** (protección animal, Fuenlabrada)
para su justificación de la subvención municipal de 2024, y compartido por si
sirve a otras entidades. Licencia MIT (ver [LICENSE](LICENSE)): puedes usarlo,
copiarlo y modificarlo libremente. Sin garantía: revisa siempre el resultado
antes de entregarlo.
