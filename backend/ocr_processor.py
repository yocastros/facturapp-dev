import os
import re
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Intentar importar librerías OCR opcionales
try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
    OCR_DISPONIBLE = True

    # Configurar rutas de Tesseract multiplataforma
    import platform
    _so = platform.system()

    # Usar variable de entorno si está definida (establecida por start.py)
    _cmd_env = os.environ.get('TESSERACT_CMD', '')
    if _cmd_env and os.path.exists(_cmd_env):
        pytesseract.pytesseract.tesseract_cmd = _cmd_env
    elif _so == 'Windows':
        _cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'
        if os.path.exists(_cmd):
            pytesseract.pytesseract.tesseract_cmd = _cmd
        _data = 'C:/Program Files/Tesseract-OCR/tessdata'
        if os.path.exists(_data):
            os.environ['TESSDATA_PREFIX'] = _data
    elif _so == 'Darwin':  # macOS
        for _cmd in ['/usr/local/bin/tesseract', '/opt/homebrew/bin/tesseract']:
            if os.path.exists(_cmd):
                pytesseract.pytesseract.tesseract_cmd = _cmd
                break
    # Linux: tesseract normalmente en PATH, no necesita configuración extra

except ImportError:
    OCR_DISPONIBLE = False
    logger.warning("Tesseract/OpenCV no disponible.")

try:
    from pdf2image import convert_from_path
    PDF_DISPONIBLE = True
except ImportError:
    PDF_DISPONIBLE = False
    logger.warning("pdf2image no disponible.")


def _ocr_es_suficiente(texto):
    """Devuelve True si el texto OCR tiene contenido útil de factura o albarán."""
    if not texto or len(texto.strip()) < 50:
        return False
    palabras_clave = ['factura', 'albaran', 'albarán', 'invoice', 'total', 'iva', 'importe', 'fecha', 'numero']
    return any(p in texto.lower() for p in palabras_clave)


def _ocr_imagen(ruta_imagen):
    """Aplica OCR probando varios modos PSM y preprocesamiento hasta obtener un resultado útil."""
    img = Image.open(str(ruta_imagen))
    mejor = ""

    for psm in ('3', '6', '11'):
        texto = pytesseract.image_to_string(img, lang='spa', config=f'--psm {psm}')
        if _ocr_es_suficiente(texto):
            return texto
        if len(texto.strip()) > len(mejor.strip()):
            mejor = texto

    # Último recurso: preprocesamiento + PSM 3
    img_proc = preprocesar_imagen(ruta_imagen)
    if img_proc is not None:
        texto_proc = pytesseract.image_to_string(img_proc, lang='spa', config='--psm 3')
        if _ocr_es_suficiente(texto_proc):
            return texto_proc
        if len(texto_proc.strip()) > len(mejor.strip()):
            mejor = texto_proc

    return mejor


def preprocesar_imagen(ruta_imagen):
    """Preprocesa imagen para mejorar precisión OCR."""
    if not OCR_DISPONIBLE:
        return None
    img = cv2.imread(str(ruta_imagen))
    if img is None:
        logger.warning(f"No se pudo cargar la imagen: {ruta_imagen}")
        return None
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Umbral adaptativo gaussiano
    umbral = cv2.adaptiveThreshold(
        gris, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    # Reducción de ruido
    kernel = np.ones((2, 2), np.uint8)
    procesada = cv2.morphologyEx(umbral, cv2.MORPH_CLOSE, kernel)
    return procesada


def _get_poppler_path():
    """Detecta la ruta de Poppler en Windows automáticamente."""
    rutas_posibles = [
        r"C:\poppler\Library\bin",
        r"C:\poppler\bin",
        r"C:\Program Files\poppler\Library\bin",
        r"C:\Program Files (x86)\poppler\Library\bin",
    ]
    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            return ruta
    return None  # En Linux/Mac no hace falta


def extraer_texto_pdf(ruta_pdf):
    """Convierte PDF a imágenes y extrae texto OCR."""
    if not PDF_DISPONIBLE or not OCR_DISPONIBLE:
        return None

    poppler_path = _get_poppler_path()

    try:
        kwargs = {'dpi': 300}
        if poppler_path:
            kwargs['poppler_path'] = poppler_path

        paginas = convert_from_path(str(ruta_pdf), **kwargs)
        texto_total = ""

        for i, pagina in enumerate(paginas):
            # Usar carpeta temporal del sistema (funciona en Windows y Linux)
            with tempfile.NamedTemporaryFile(suffix=f'_pag{i}.png', delete=False) as tmp:
                img_path = tmp.name
            try:
                pagina.save(img_path, "PNG")
                texto_total += _ocr_imagen(img_path) + "\n"
            finally:
                if os.path.exists(img_path):
                    os.remove(img_path)

        return texto_total
    except Exception as e:
        logger.error(f"Error procesando PDF: {e}")
        return None


def extraer_texto_imagen(ruta_imagen):
    """Extrae texto de imagen con estrategia de doble intento."""
    if not OCR_DISPONIBLE:
        return None
    try:
        return _ocr_imagen(ruta_imagen)
    except Exception as e:
        logger.error(f"Error procesando imagen: {e}")
        return None


# Modo simulación eliminado — el sistema solo acepta documentos reales


def detectar_tipo_documento(texto):
    """Detecta si es factura o albarán por análisis de patrones."""
    texto_lower = texto.lower()
    patrones_albaran = [
        r'\balbaran\b', r'\balbar[aá]n\b', r'\bdelivery note\b',
        r'\bnota de entrega\b', r'\bpart[eé] de entrega\b',
        r'\bnº\s*alb', r'\bnumero\s*alb'
    ]
    patrones_factura = [
        r'\bfactura\b', r'\binvoice\b', r'\bfra\b',
        r'\bnº\s*fac', r'\bnumero\s*fac', r'\bfactura\s+n[uú]mero\b'
    ]
    score_albaran = sum(1 for p in patrones_albaran if re.search(p, texto_lower))
    score_factura = sum(1 for p in patrones_factura if re.search(p, texto_lower))

    if score_albaran > score_factura:
        return 'albaran'
    elif score_factura > 0:
        return 'factura'
    else:
        return 'factura'  # Default


def extraer_numero_documento(texto):
    """Extrae número de documento del texto OCR."""
    patrones = [
        r'(?:factura|fra|albar[aá]n|albaran)[^\d]*[:\s#Nº°nNº.]*\s*([A-Z]{0,5}[-/]?\d{2,4}[-/]?\d{2,6})',
        r'(?:n[uú]mero|n[°º]|num|no\.?)[:\s]*([A-Z]{0,5}[-/]?\d{2,4}[-/]?\d{2,6})',
        r'\b([A-Z]{2,5}[-/]\d{4}[-/]\d{2,6})\b',
        r'\b([A-Z]{1,3}\d{4,10})\b',
    ]
    for patron in patrones:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


_MESES_ES = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
}


def _normalizar_fecha(fecha_str):
    """Convierte una fecha extraída a formato ISO 8601 (YYYY-MM-DD)."""
    fecha_str = fecha_str.strip()
    m = re.match(r'(\d{1,2})\s+(?:de\s+)?(\w+)\s+(?:de\s+)?(\d{4})', fecha_str, re.IGNORECASE)
    if m:
        dia, mes_str, anio = m.groups()
        mes = _MESES_ES.get(mes_str.lower())
        if mes:
            return f"{anio}-{mes:02d}-{int(dia):02d}"
    partes = re.split(r'[/\-\.]', fecha_str)
    if len(partes) == 3:
        a, b, c = partes
        if len(c) == 4:
            return f"{c}-{int(b):02d}-{int(a):02d}"
        if len(a) == 4:
            return f"{a}-{int(b):02d}-{int(c):02d}"
        if len(c) == 2:
            return f"20{c}-{int(b):02d}-{int(a):02d}"
    return fecha_str


def extraer_fecha(texto):
    """Extrae fecha del documento y la normaliza a ISO 8601 (YYYY-MM-DD)."""
    patrones = [
        r'(?:fecha|date)[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
        r'\b(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})\b',
        r'\b(\d{1,2}\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+\d{4})\b',
        r'\b(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})\b',
    ]
    for patron in patrones:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            return _normalizar_fecha(match.group(1))
    return None


def extraer_proveedor(texto):
    """Extrae nombre del proveedor."""
    patrones = [
        # Lookbehind (?<=[,\s\.]) evita que "sa" al final de palabras como "empresa" active el sufijo
        r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ ,\.]{4,60}(?<=[,\s\.])(?:S\.?L\.?U?\.?|S\.?A\.?U?\.?|S\.?C\.?|S\.?L\.?P\.))\b',
        r'(?:proveedor|raz[oó]n social|emisor)[:\s]+([^\n\r]{5,80})',
        r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ ,]{4,40}(?<=[,\s])(?:S\.L\.|S\.A\.))\b',
    ]
    for patron in patrones:
        match = re.search(patron, texto, re.IGNORECASE | re.MULTILINE)
        if match:
            nombre = match.group(1).strip()
            if len(nombre) > 3:
                return nombre[:100]
    return None


def extraer_cif(texto):
    """Extrae CIF/NIF del proveedor."""
    patron = r'\b([A-HJ-NP-SUVW]\d{7}[0-9A-J]|[0-9]{8}[A-Z]|\d{8}[A-Z])\b'
    patrones_contexto = [
        r'(?:CIF|NIF|C\.I\.F|N\.I\.F)[:\s.]*([A-Z]\d{7}[0-9A-J]|\d{8}[A-Z])',
        patron
    ]
    for p in patrones_contexto:
        match = re.search(p, texto, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return None


def _parsear_importe(importe_str):
    """Convierte string de importe a float detectando formato español (1.234,56) e inglés (1,234.56)."""
    tiene_punto = '.' in importe_str
    tiene_coma = ',' in importe_str

    if tiene_punto and tiene_coma:
        # El separador que aparece en última posición es el decimal
        if importe_str.rfind('.') > importe_str.rfind(','):
            importe_str = importe_str.replace(',', '')           # inglés: "1,234.56"
        else:
            importe_str = importe_str.replace('.', '').replace(',', '.')  # español: "1.234,56"
    elif tiene_coma:
        importe_str = importe_str.replace(',', '.')             # "1234,56"
    # Solo punto o ninguno: ya es float válido ("1234.56", "1234")

    return float(importe_str)


def extraer_importe(texto, tipo='total'):
    """Extrae importes del documento."""
    patrones_total = [
        r'total\s+(?:a\s+pagar|factura|albar[aá]n)[:\s]*([0-9]{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'(?:importe\s+total|total\s+iva\s+incluido)[:\s]*([0-9]{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'total\s*\([^)]*\)\s*([0-9]{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'total[:\s€$]*\s*([0-9]{1,3}(?:[.,]\d{3})*[.,]\d{2})',
    ]
    patrones_base = [
        r'base\s+imponible[:\s]*([0-9]{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'base[:\s€]*\s*([0-9]{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'subtotal[:\s€]*\s*([0-9]{1,3}(?:[.,]\d{3})*[.,]\d{2})',
    ]
    patrones_iva = [
        r'(?:iva|i\.v\.a\.?)\s*(?:\d{1,2}%)?[:\s]*([0-9]{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'(?:impuesto)[:\s]*([0-9]{1,3}(?:[.,]\d{3})*[.,]\d{2})',
    ]

    if tipo == 'total':
        patrones = patrones_total
    elif tipo == 'base':
        patrones = patrones_base
    elif tipo == 'iva':
        patrones = patrones_iva
    else:
        patrones = patrones_total

    if tipo == 'total':
        # Recogemos TODOS los candidatos de todos los patrones y devolvemos el máximo.
        # Un patrón genérico puede capturar líneas de detalle (ej. "Total\n12,50") antes
        # que el total real; el total siempre es el valor más alto del documento.
        candidatos = []
        for patron in patrones_total:
            for m in re.finditer(patron, texto, re.IGNORECASE):
                try:
                    candidatos.append(_parsear_importe(m.group(1)))
                except ValueError:
                    pass
        # Importes con símbolo € como fuente adicional (facturas en formato tabla)
        for m in re.finditer(r'([0-9]{1,3}(?:[.,]\d{3})*[.,]\d{2})\s*€', texto, re.IGNORECASE):
            try:
                candidatos.append(_parsear_importe(m.group(1)))
            except ValueError:
                pass
        return max(candidatos) if candidatos else 0.0
    else:
        for patron in patrones:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                try:
                    return _parsear_importe(match.group(1))
                except ValueError:
                    continue
        return 0.0


def extraer_porcentaje_iva(texto):
    """Detecta el tipo de IVA aplicado (4, 10 o 21) desde el texto del documento."""
    patrones = [
        r'(?:iva|i\.v\.a\.?)\s*[:\s]?\s*(4|10|21)\s*%',
        r'(4|10|21)\s*%\s*(?:iva|i\.v\.a\.?)',
        r'tipo\s+(?:de\s+)?iva[:\s]*\s*(4|10|21)',
    ]
    for patron in patrones:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def extraer_numeros_albaranes_referenciados(texto):
    """Extrae números de albaranes mencionados en una factura."""
    patrones = [
        r'albaran[es]*[:\s#Nº°.]*\s*([A-Z]{0,5}[-/]?\d{2,4}[-/]?\d{2,6})',
        r'albar[aá]n[es]*[:\s#Nº°.]*\s*([A-Z]{0,5}[-/]?\d{2,4}[-/]?\d{2,6})',
        r'ref(?:erencia)?[.\s]*alb[:\s]*([A-Z0-9/-]{4,20})',
        r'seg[uú]n\s+albar[aá]n[:\s]*([A-Z0-9/-]{4,20})',
    ]
    numeros = []
    for patron in patrones:
        for match in re.finditer(patron, texto, re.IGNORECASE):
            num = match.group(1).strip()
            if num and num not in numeros:
                numeros.append(num)
    return numeros


def extraer_lineas_detalle(texto: str) -> list:
    """Extrae líneas de detalle del cuerpo del documento usando 3 estrategias."""
    keywords_inicio = ['descripcion', 'concepto', 'detalle', 'articulo', 'producto',
                       'referencia', 'denominacion']
    keywords_fin = ['base imponible', 'subtotal', 'total neto', 'importe total',
                    'total factura', 'total a pagar']

    texto_lower = texto.lower()

    pos_inicio = None
    for kw in keywords_inicio:
        idx = texto_lower.find(kw)
        if idx != -1 and (pos_inicio is None or idx < pos_inicio):
            pos_inicio = idx

    pos_fin = None
    for kw in keywords_fin:
        idx = texto_lower.find(kw)
        if idx != -1 and (pos_fin is None or idx < pos_fin):
            pos_fin = idx

    if pos_inicio is not None and pos_fin is not None and pos_inicio < pos_fin:
        bloque = texto[pos_inicio:pos_fin]
    elif pos_inicio is not None:
        bloque = texto[pos_inicio:]
    elif pos_fin is not None:
        bloque = texto[:pos_fin]
    else:
        bloque = texto

    PALABRAS_EXCLUIR = [
        'total', 'subtotal', 'base imponible', 'i.v.a', 'iva', 'descuento',
        'forma de pago', 'vencimiento', 'banco', 'iban', 'swift', 'cuenta',
        'observacion', 'nota', 'gracias', 'plazo',
    ]

    def es_valida(desc, importe):
        if len(desc.strip()) < 3:
            return False
        if importe <= 0:
            return False
        desc_lower = desc.lower()
        return not any(kw in desc_lower for kw in PALABRAS_EXCLUIR)

    def limpiar(desc):
        return re.sub(r'\s{2,}', ' ', desc.strip())[:500]

    lineas = []

    # Estrategia A — 4 columnas numéricas: descripcion cantidad precio importe
    patron_a = r'^\s*(.+?)\s{2,}(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d{1,2})?)\s+(\d+(?:[.,]\d{1,2})?)\s*$'
    for m in re.finditer(patron_a, bloque, re.MULTILINE):
        try:
            desc = limpiar(m.group(1))
            cantidad = _parsear_importe(m.group(2))
            precio = _parsear_importe(m.group(3))
            importe = _parsear_importe(m.group(4))
            if es_valida(desc, importe):
                lineas.append({'descripcion': desc, 'cantidad': cantidad, 'unidad': None,
                               'precio_unitario': precio, 'importe_linea': importe, 'orden': len(lineas)})
        except (ValueError, IndexError):
            continue
    if lineas:
        return lineas

    # Estrategia B — descripcion + importe al final de línea
    patron_b = r'^\s*(.{5,80}?)\s{2,}(\d+(?:[.,]\d{1,2})?)\s*€?\s*$'
    for m in re.finditer(patron_b, bloque, re.MULTILINE):
        try:
            desc = limpiar(m.group(1))
            importe = _parsear_importe(m.group(2))
            if es_valida(desc, importe):
                lineas.append({'descripcion': desc, 'cantidad': 1.0, 'unidad': None,
                               'precio_unitario': importe, 'importe_linea': importe, 'orden': len(lineas)})
        except (ValueError, IndexError):
            continue
    if lineas:
        return lineas

    # Estrategia C — cantidad + unidad + descripcion + importe
    patron_c = (r'^\s*(\d+(?:[.,]\d+)?)\s*'
                r'(kg|gr|g|ud|uds|u|caja|cajas|l|litro|litros|pcs?|pack)\s+'
                r'(.+?)\s+(\d+(?:[.,]\d{1,2})?)\s*€?\s*$')
    for m in re.finditer(patron_c, bloque, re.MULTILINE | re.IGNORECASE):
        try:
            cantidad = _parsear_importe(m.group(1))
            unidad = m.group(2).strip()
            desc = limpiar(m.group(3))
            importe = _parsear_importe(m.group(4))
            precio = round(importe / cantidad, 4) if cantidad > 0 else 0.0
            if es_valida(desc, importe):
                lineas.append({'descripcion': desc, 'cantidad': cantidad, 'unidad': unidad,
                               'precio_unitario': precio, 'importe_linea': importe, 'orden': len(lineas)})
        except (ValueError, IndexError):
            continue

    return lineas


def procesar_documento(ruta_archivo):
    """Función principal: procesa un documento y retorna datos extraídos."""
    ruta = Path(ruta_archivo)
    extension = ruta.suffix.lower()

    # Extraer texto según tipo de archivo
    if extension == '.pdf':
        texto = extraer_texto_pdf(ruta)
    elif extension in ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp']:
        texto = extraer_texto_imagen(ruta)
    else:
        return {'error': f'Formato no soportado: {extension}', 'estado': 'ERROR'}

    if not texto or len(texto.strip()) < 10:
        return {'error': 'No se pudo extraer texto del documento. Comprueba que el archivo no está vacío o protegido.', 'estado': 'ERROR'}

    logger.info("=== OCR DEBUG (primeros 1200 chars) ===\n%s\n=== FIN OCR DEBUG ===", texto[:1200])

    # Extraer campos
    tipo = detectar_tipo_documento(texto)
    numero = extraer_numero_documento(texto)
    fecha = extraer_fecha(texto)
    proveedor = extraer_proveedor(texto)
    cif = extraer_cif(texto)
    base_imponible = extraer_importe(texto, 'base')
    iva_importe = extraer_importe(texto, 'iva')
    total = extraer_importe(texto, 'total')

    # ── VALIDACIÓN ESTRICTA ────────────────────────────────────────────────
    texto_lower = texto.lower()

    # 1. El documento debe mencionar "factura" o "albarán"
    tiene_palabra_clave = any(p in texto_lower for p in [
        'factura', 'albarán', 'albaran', 'albarán', 'fra.', 'fra ',
        'invoice', 'nota de entrega', 'delivery note'
    ])

    # 2. Debe tener al menos un importe económico real
    tiene_importe = total > 0 or base_imponible > 0 or iva_importe > 0

    # 3. Debe tener CIF o número de documento
    tiene_identificador = bool(cif) or bool(numero)

    # Construir mensaje de error detallado si falla
    errores = []
    if not tiene_palabra_clave:
        errores.append('no contiene la palabra "factura" ni "albarán"')
    if not tiene_importe:
        errores.append('no se han encontrado importes económicos (base, IVA, total)')
    if not tiene_identificador:
        errores.append('no se ha encontrado número de documento ni CIF')

    # Rechazar si falla la palabra clave Y al menos otro criterio
    if not tiene_palabra_clave or (not tiene_importe and not tiene_identificador):
        return {
            'error': (
                'El documento no es una factura ni un albarán: ' +
                ', '.join(errores) + '. '
                'Por favor sube únicamente facturas o albaranes.'
            ),
            'estado': 'ERROR',
        }
    # ─────────────────────────────────────────────────────────────────────────

    # Si el total extraído es menor que la base, el total es incorrecto — descartarlo
    if total > 0 and base_imponible > 0 and total < base_imponible:
        logger.warning(f"Total extraído ({total}) menor que base ({base_imponible}): descartado.")
        total = 0.0

    # Si tenemos base y total pero no IVA → calcularlo por diferencia
    if base_imponible > 0 and total > 0 and iva_importe == 0:
        iva_importe = round(total - base_imponible, 2)

    # Si solo tenemos total → calcular base e IVA según el tipo detectado
    if total > 0 and base_imponible == 0:
        pct_detectado = extraer_porcentaje_iva(texto)
        if pct_detectado is None:
            pct_detectado = 21.0
            logger.warning(
                "No se detectó el tipo de IVA en el documento; "
                "se asume 21%%. Los importes calculados pueden ser incorrectos."
            )
        divisor = 1 + pct_detectado / 100
        base_imponible = round(total / divisor, 2)
        iva_importe = round(total - base_imponible, 2)

    # Si tenemos base e IVA pero no total → calcularlo
    if base_imponible > 0 and iva_importe > 0 and total == 0:
        total = round(base_imponible + iva_importe, 2)

    # Calcular % IVA
    porcentaje_iva = 21.0
    if base_imponible > 0 and iva_importe > 0:
        porcentaje_iva = round((iva_importe / base_imponible) * 100, 1)

    # Validación cruzada: comparar % IVA del documento con el calculado
    pct_en_documento = extraer_porcentaje_iva(texto)
    if pct_en_documento and base_imponible > 0:
        if abs(porcentaje_iva - pct_en_documento) > 1.5:
            logger.warning(
                f"Discrepancia en IVA: el documento indica {pct_en_documento}% "
                f"pero los importes extraídos implican {porcentaje_iva}%. "
                "Posible error de OCR en algún importe."
            )

    # Albaranes referenciados (si es factura)
    albaranes_ref = []
    if tipo == 'factura':
        albaranes_ref = extraer_numeros_albaranes_referenciados(texto)

    lineas = extraer_lineas_detalle(texto)

    return {
        'tipo': tipo,
        'numero': numero,
        'fecha': fecha,
        'proveedor': proveedor,
        'cif': cif,
        'base_imponible': base_imponible,
        'iva': iva_importe,
        'total': total,
        'porcentaje_iva': porcentaje_iva,
        'texto_ocr': texto,
        'albaranes_referenciados': albaranes_ref,
        'lineas': lineas,
        'num_lineas': len(lineas),
        'estado': 'PROCESADO',
    }
