# Pipeline OCR

Documentación del motor de procesamiento de documentos: `backend/ocr_processor.py`.

---

## Visión general

El pipeline OCR transforma un fichero (PDF, imagen) en datos estructurados
listos para guardar en base de datos. Se ejecuta en el momento de la subida,
dentro del endpoint `POST /api/escanear`.

```
Fichero subido
      │
      ▼
┌─────────────────┐
│ ¿Es PDF?        │──Sí──► Conversión PDF → imágenes (pdf2image, 300 DPI)
└─────────────────┘              │
      │ No                       ▼
      │                 ┌─────────────────────┐
      └────────────────►│  Extracción de texto │
                        │  con Tesseract OCR   │
                        │  (idioma: español)   │
                        └─────────────────────┘
                                 │
                          ¿Texto suficiente?
                         /                \
                       No                 Sí
                        │                  │
                Preprocesamiento    Extracción de campos
                 OpenCV (escala       (regex por campo)
                 grises + umbral           │
                 adaptativo +             ▼
                 reducción ruido)  Validación estricta
                        │         /              \
                        │       Falla            Pasa
                        │         │                │
                        └────────►│         Neteo automático
                                  │                │
                                ERROR          PROCESADO
```

---

## Dependencias y modo sin Tesseract

El módulo detecta en el arranque si las librerías OCR están disponibles:

```python
OCR_DISPONIBLE = True   # pytesseract + Pillow + OpenCV + numpy instalados
PDF_DISPONIBLE = True   # pdf2image + Poppler instalados
```

Si Tesseract **no está instalado**, `OCR_DISPONIBLE = False` y el sistema
rechaza cualquier subida con un error claro. No hay modo simulación.

La ruta del ejecutable de Tesseract se configura automáticamente según el SO:

| Sistema | Ruta por defecto |
|---------|-----------------|
| Windows | `C:/Program Files/Tesseract-OCR/tesseract.exe` |
| macOS Intel | `/usr/local/bin/tesseract` |
| macOS Apple Silicon | `/opt/homebrew/bin/tesseract` |
| Linux | En `PATH` del sistema (no necesita configuración) |

También se puede sobreescribir con la variable de entorno `TESSERACT_CMD`.

---

## Función principal: `procesar_documento(ruta_archivo)`

Punto de entrada del pipeline. Recibe la ruta del fichero y devuelve un
diccionario con todos los campos extraídos, o `{'estado': 'ERROR', 'error': '...'}`.

```python
resultado = procesar_documento('/ruta/al/fichero.pdf')
# → {'tipo': 'factura', 'numero': 'F-2024-0123', 'total': 1210.0, ...}
```

---

## Paso 1 — Extracción de texto

### PDFs: `extraer_texto_pdf(ruta_pdf)`

1. Convierte cada página a imagen PNG a **300 DPI** usando `pdf2image`
2. Guarda cada imagen en un fichero temporal del sistema (`tempfile`)
3. Aplica `_ocr_imagen()` a cada página
4. Concatena el texto de todas las páginas
5. Elimina los ficheros temporales

En Windows, detecta automáticamente la ruta de Poppler en varias ubicaciones
estándar (`C:\poppler\Library\bin`, `C:\Program Files\poppler\...`).

### Imágenes: `extraer_texto_imagen(ruta_imagen)`

Llama directamente a `_ocr_imagen()`.

### Estrategia de OCR: `_ocr_imagen(ruta_imagen)`

Prueba varios modos PSM de Tesseract en orden hasta obtener un resultado útil:

| Intento | PSM | Descripción |
|---------|-----|-------------|
| 1 | `3` | Segmentación automática de página completa |
| 2 | `6` | Bloque de texto uniforme |
| 3 | `11` | Texto disperso sin orden |
| 4 | `3` + preprocesamiento OpenCV | Último recurso si los anteriores fallan |

Un resultado se considera "suficiente" (`_ocr_es_suficiente`) si tiene más
de 50 caracteres y contiene al menos una palabra clave de documento
(factura, albarán, invoice, total, iva, importe, fecha, numero).

---

## Paso 2 — Preprocesamiento de imagen (fallback)

`preprocesar_imagen(ruta_imagen)` — Solo se ejecuta si los intentos directos fallan.

Aplica esta cadena de transformaciones con OpenCV:

```
Imagen original
      │
      ▼
Escala de grises (cvtColor BGR→GRAY)
      │
      ▼
Umbral adaptativo gaussiano
(ADAPTIVE_THRESH_GAUSSIAN_C, blockSize=11, C=2)
      │
      ▼
Reducción de ruido morfológico
(MORPH_CLOSE con kernel 2×2)
      │
      ▼
Imagen procesada → Tesseract PSM 3
```

---

## Paso 3 — Extracción de campos por regex

Cada campo tiene su propia función de extracción. Todas operan sobre el
texto completo extraído por OCR.

### `detectar_tipo_documento(texto)`

Puntúa patrones de factura y albarán, gana el de mayor puntuación:

```
Patrones albarán: albaran, albarán, delivery note, nota de entrega,
                  parte de entrega, nº alb, numero alb

Patrones factura: factura, invoice, fra, nº fac, numero fac,
                  factura número

Por defecto si hay empate: 'factura'
```

### `extraer_numero_documento(texto)`

Prueba 4 patrones regex en orden de especificidad:

1. Número precedido de "factura/fra/albarán" + separador
2. Número precedido de "número/nº/num/no."
3. Formato `AA-YYYY-NNNNNN` (ej: `F-2024-0123`)
4. Formato `AANNNNNNNN` (ej: `FA202400123`)

### `extraer_fecha(texto)`

Detecta fechas en múltiples formatos y las normaliza a **ISO 8601 (YYYY-MM-DD)**:

| Formato de entrada | Ejemplo | Resultado |
|-------------------|---------|-----------|
| `DD/MM/YYYY` | `15/03/2024` | `2024-03-15` |
| `DD-MM-YYYY` | `15-03-2024` | `2024-03-15` |
| `YYYY-MM-DD` | `2024-03-15` | `2024-03-15` |
| `DD de mes de YYYY` | `15 de marzo de 2024` | `2024-03-15` |
| `DD mes YYYY` | `15 marzo 2024` | `2024-03-15` |

Meses reconocidos en español: enero–diciembre.

### `extraer_cif(texto)`

Busca el patrón de CIF/NIF español:
- Formato: letra + 7 dígitos + dígito/letra (ej: `B12345678`, `A87654321`)
- Regex: `[A-Z]\d{7}[A-Z0-9]`

### `extraer_proveedor(texto)`

Busca el nombre del proveedor buscando líneas que contengan:
- "S.L.", "S.A.", "S.L.U.", "S.A.U.", "S.C.", "S.COOP."
- o que sigan a palabras como "proveedor:", "empresa:", "razón social:"

### `extraer_importe(texto, tipo)`

Extrae importes según el tipo solicitado (`'base'`, `'iva'`, `'total'`).
Soporta formatos numéricos europeos y americanos:

| Formato | Ejemplo |
|---------|---------|
| Europeo (punto millar, coma decimal) | `1.210,00 €` |
| Americano (coma millar, punto decimal) | `1,210.00` |
| Sin separador de millar | `1210.00` |

---

## Paso 4 — Extracción de líneas de detalle

`extraer_lineas_detalle(texto)` — Intenta extraer la tabla de artículos/servicios.

Se prueban 3 estrategias en orden, la primera que encuentre líneas válidas gana:

**Estrategia A** — 4 columnas: `descripción · cantidad · precio · importe`
```
Aceite oliva 5L    10    12,50    125,00
```

**Estrategia B** — 2 columnas: `descripción · importe al final de línea`
```
Aceite oliva virgen extra 5L          125,00
```

**Estrategia C** — Cantidad + unidad al inicio: `cant · unidad · descripción · importe`
```
10 ud Aceite oliva 5L    125,00
```

Unidades reconocidas en estrategia C: `kg, gr, g, ud, uds, u, caja, cajas, l, litro, litros, pcs, pack`

Una línea se considera válida si la descripción tiene más de 3 caracteres y el importe es mayor que 0.

---

## Paso 5 — Validación estricta

Antes de aceptar el documento se verifican 3 criterios:

| Criterio | Condición |
|----------|-----------|
| Palabra clave | El texto contiene "factura", "albarán", "invoice", "fra.", "nota de entrega" o "delivery note" |
| Importe económico | Al menos uno de: total, base imponible o IVA es mayor que 0 |
| Identificador | Tiene número de documento O CIF |

**Regla de rechazo:** Se rechaza si falla la palabra clave, O si fallan tanto el importe como el identificador.

Adicionalmente, si el total extraído es menor que la base imponible (lo que indica un error de OCR), el total se descarta y queda a 0.

---

## Paso 6 — Neteo automático (en `app.py`)

Tras guardar el documento en BD, se intenta asociarlo automáticamente:

**Prioridad 1 — Por número de albarán en factura:**
Si es una factura, se busca en su texto OCR cualquier número que coincida
con el campo `numero` de un albarán existente. Si hay coincidencia, se asocian.

**Prioridad 2 — Por proveedor + proximidad de fecha:**
Si es una factura sin albarán, se buscan albaranes del mismo proveedor
cuya fecha esté dentro de un margen de ±30 días.

---

## Referencia de funciones públicas

| Función | Descripción |
|---------|-------------|
| `procesar_documento(ruta)` | Punto de entrada. Devuelve dict con todos los campos o error |
| `extraer_texto_pdf(ruta)` | Extrae texto OCR de todas las páginas de un PDF |
| `extraer_texto_imagen(ruta)` | Extrae texto OCR de una imagen |
| `preprocesar_imagen(ruta)` | Preprocesa imagen con OpenCV para mejorar OCR |
| `detectar_tipo_documento(texto)` | Devuelve `'factura'` o `'albaran'` |
| `extraer_numero_documento(texto)` | Devuelve número de documento o `None` |
| `extraer_fecha(texto)` | Devuelve fecha en formato ISO 8601 o `None` |
| `extraer_cif(texto)` | Devuelve CIF/NIF o `None` |
| `extraer_proveedor(texto)` | Devuelve nombre del proveedor o `None` |
| `extraer_importe(texto, tipo)` | Devuelve importe float o `0.0` |
| `extraer_lineas_detalle(texto)` | Devuelve lista de líneas de detalle o `[]` |

---

## Consideraciones para mejorar el OCR

- **Documentos escaneados de baja calidad:** El preprocesamiento OpenCV mejora notablemente el resultado. Si aún falla, aumentar la resolución del escáner a 300+ DPI.
- **PDFs con texto nativo (no escaneados):** Tesseract los procesa directamente sin necesidad de preprocesamiento. El resultado suele ser muy preciso.
- **Documentos en otros idiomas:** El modelo está configurado para español (`lang='spa'`). Para otros idiomas habría que instalar el paquete de idioma correspondiente y modificar el parámetro `lang`.
- **Líneas de detalle no extraídas:** Las 3 estrategias regex cubren los formatos más comunes, pero documentos con tablas muy complejas o mal formateadas pueden no extraer líneas. En ese caso los campos de importes globales (base, IVA, total) sí se extraen correctamente.
- **Pendiente:** Fallback con Claude API para documentos donde Tesseract no extrae líneas de detalle (ver `CLAUDE.md` → Estado del proyecto).
