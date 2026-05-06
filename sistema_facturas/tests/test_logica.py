"""
Tests unitarios de funciones puras del backend:
  - _fechas_proximas        (app.py)
  - extension_permitida     (app.py)
  - _ocr_es_suficiente      (ocr_processor.py)

No requieren BD ni servidores.
"""
import sys
import os

TESTS_DIR   = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR    = os.path.abspath(os.path.join(TESTS_DIR, '..', '..'))
BACKEND_DIR = os.path.join(ROOT_DIR, 'backend')

for _p in (ROOT_DIR, BACKEND_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

# Las importaciones desde app y ocr_processor se hacen de forma diferida
# dentro de cada clase para evitar que app.py cargue backend/models.py en
# sys.modules['models'] antes de que test_usuarios.py pueda cargar
# sistema_usuarios/models.py con el mismo nombre.

def _get_fechas_proximas():
    from app import _fechas_proximas
    return _fechas_proximas

def _get_extension_permitida():
    from app import extension_permitida
    return extension_permitida

def _get_ocr_suficiente():
    from ocr_processor import _ocr_es_suficiente
    return _ocr_es_suficiente


# ══════════════════════════════════════════════════════════════════════════
# _fechas_proximas
# ══════════════════════════════════════════════════════════════════════════

class TestFechasProximas:

    # ── Casos que deben devolver True ─────────────────────────────────────

    def test_misma_fecha(self):
        assert _get_fechas_proximas()('01/01/2025', '01/01/2025') is True

    def test_diferencia_cero_dias(self):
        assert _get_fechas_proximas()('15/03/2025', '15/03/2025') is True

    def test_diferencia_un_dia(self):
        assert _get_fechas_proximas()('01/01/2025', '02/01/2025') is True

    def test_diferencia_exacta_30_dias(self):
        assert _get_fechas_proximas()('01/01/2025', '31/01/2025') is True

    def test_diferencia_29_dias(self):
        assert _get_fechas_proximas()('01/01/2025', '30/01/2025') is True

    def test_fechas_invertidas_dentro_limite(self):
        """El orden de los argumentos no debe importar."""
        assert _get_fechas_proximas()('31/01/2025', '01/01/2025') is True

    def test_formato_iso_yyyy_mm_dd(self):
        assert _get_fechas_proximas()('2025-01-01', '2025-01-15') is True

    def test_formato_dd_mm_yyyy_guion(self):
        assert _get_fechas_proximas()('01-01-2025', '10-01-2025') is True

    def test_formato_dd_punto_mm_punto_yyyy(self):
        assert _get_fechas_proximas()('01.01.2025', '15.01.2025') is True

    def test_formatos_distintos_compatibles(self):
        """Fechas en formatos distintos deben compararse bien."""
        assert _get_fechas_proximas()('01/01/2025', '2025-01-20') is True

    # ── Casos que deben devolver False ────────────────────────────────────

    def test_diferencia_31_dias(self):
        assert _get_fechas_proximas()('01/01/2025', '01/02/2025') is False

    def test_diferencia_60_dias(self):
        assert _get_fechas_proximas()('01/01/2025', '02/03/2025') is False

    def test_diferencia_un_año(self):
        assert _get_fechas_proximas()('01/01/2024', '01/01/2025') is False

    # ── Casos con valores nulos o inválidos ───────────────────────────────

    def test_primera_fecha_none(self):
        assert _get_fechas_proximas()(None, '01/01/2025') is False

    def test_segunda_fecha_none(self):
        assert _get_fechas_proximas()('01/01/2025', None) is False

    def test_ambas_fechas_none(self):
        assert _get_fechas_proximas()(None, None) is False

    def test_primera_fecha_vacia(self):
        assert _get_fechas_proximas()('', '01/01/2025') is False

    def test_segunda_fecha_vacia(self):
        assert _get_fechas_proximas()('01/01/2025', '') is False

    def test_formato_invalido(self):
        assert _get_fechas_proximas()('no-es-fecha', '01/01/2025') is False

    def test_ambas_invalidas(self):
        assert _get_fechas_proximas()('abc', 'xyz') is False

    def test_limite_personalizado_10_dias_dentro(self):
        assert _get_fechas_proximas()('01/01/2025', '05/01/2025', dias=10) is True

    def test_limite_personalizado_10_dias_fuera(self):
        assert _get_fechas_proximas()('01/01/2025', '15/01/2025', dias=10) is False


# ══════════════════════════════════════════════════════════════════════════
# extension_permitida
# ══════════════════════════════════════════════════════════════════════════

class TestExtensionPermitida:

    # ── Extensiones válidas ───────────────────────────────────────────────

    def test_pdf_minusculas(self):
        assert _get_extension_permitida()('factura.pdf') is True

    def test_pdf_mayusculas(self):
        assert _get_extension_permitida()('factura.PDF') is True

    def test_png(self):
        assert _get_extension_permitida()('imagen.png') is True

    def test_jpg(self):
        assert _get_extension_permitida()('foto.jpg') is True

    def test_jpeg(self):
        assert _get_extension_permitida()('foto.jpeg') is True

    def test_tiff(self):
        assert _get_extension_permitida()('scan.tiff') is True

    def test_tif(self):
        assert _get_extension_permitida()('scan.tif') is True

    def test_bmp(self):
        assert _get_extension_permitida()('imagen.bmp') is True

    def test_extension_mixta_mayusculas(self):
        assert _get_extension_permitida()('imagen.PNG') is True

    def test_ruta_con_directorios(self):
        assert _get_extension_permitida()('/tmp/uploads/factura.pdf') is True

    # ── Extensiones no válidas ────────────────────────────────────────────

    def test_exe(self):
        assert _get_extension_permitida()('virus.exe') is False

    def test_docx(self):
        assert _get_extension_permitida()('documento.docx') is False

    def test_txt(self):
        assert _get_extension_permitida()('notas.txt') is False

    def test_xls(self):
        assert _get_extension_permitida()('reporte.xls') is False

    def test_gif(self):
        assert _get_extension_permitida()('animacion.gif') is False

    def test_sin_extension(self):
        assert _get_extension_permitida()('archivo_sin_extension') is False

    def test_extension_vacia(self):
        assert _get_extension_permitida()('archivo.') is False

    def test_nombre_vacio(self):
        assert _get_extension_permitida()('') is False


# ══════════════════════════════════════════════════════════════════════════
# _ocr_es_suficiente
# ══════════════════════════════════════════════════════════════════════════

class TestOcrEsSuficiente:

    # ── Debe devolver True ────────────────────────────────────────────────

    def test_contiene_factura(self):
        texto = 'A' * 50 + ' factura '
        assert _get_ocr_suficiente()(texto) is True

    def test_contiene_albaran(self):
        texto = 'A' * 50 + ' albaran algo más texto para llegar al mínimo de caracteres requerido'
        assert _get_ocr_suficiente()(texto) is True

    def test_contiene_albarán_con_tilde(self):
        texto = 'A' * 50 + ' albarán número 123 importe total'
        assert _get_ocr_suficiente()(texto) is True

    def test_contiene_total(self):
        texto = 'Empresa SA  CIF B12345678  fecha 01/01/2025  total 1.500,00 EUR'
        assert _get_ocr_suficiente()(texto) is True

    def test_contiene_iva(self):
        texto = 'Base imponible 1000 IVA 21% total 1210 ' + 'x' * 30
        assert _get_ocr_suficiente()(texto) is True

    def test_contiene_importe(self):
        texto = 'Concepto: Servicios  importe 500  ' + 'y' * 30
        assert _get_ocr_suficiente()(texto) is True

    def test_contiene_fecha(self):
        texto = 'Número: 001  fecha 15/03/2025  proveedor empresa SL total 100'
        assert _get_ocr_suficiente()(texto) is True

    def test_contiene_numero(self):
        texto = 'Documento numero FAC-001 emitido por empresa SA total 500 euros base'
        assert _get_ocr_suficiente()(texto) is True

    def test_contiene_invoice(self):
        texto = 'invoice number 2025-001 date 01/01/2025 total amount 500 EUR texto'
        assert _get_ocr_suficiente()(texto) is True

    # ── Debe devolver False ───────────────────────────────────────────────

    def test_texto_vacio(self):
        assert _get_ocr_suficiente()('') is False

    def test_texto_none(self):
        assert _get_ocr_suficiente()(None) is False

    def test_texto_muy_corto(self):
        assert _get_ocr_suficiente()('hola') is False

    def test_texto_49_caracteres(self):
        assert _get_ocr_suficiente()('a' * 49) is False

    def test_texto_50_sin_palabras_clave(self):
        texto = 'x' * 50
        assert _get_ocr_suficiente()(texto) is False

    def test_texto_largo_sin_palabras_clave(self):
        texto = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor.'
        assert _get_ocr_suficiente()(texto) is False

    def test_texto_solo_espacios(self):
        assert _get_ocr_suficiente()('   ' * 30) is False
