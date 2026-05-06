"""
Genera docs/pruebas_tecnico.pdf con la guía completa para ejecutar
los tests unitarios del proyecto FacturApp.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import os

# ── Rutas ──────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(ROOT, 'docs', 'pruebas_tecnico.pdf')
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# ── Paleta de colores ───────────────────────────────────────────────────────
AZUL_OSCURO  = colors.HexColor('#1a2744')
AZUL_MEDIO   = colors.HexColor('#2563eb')
AZUL_CLARO   = colors.HexColor('#dbeafe')
VERDE        = colors.HexColor('#166534')
VERDE_CLARO  = colors.HexColor('#dcfce7')
GRIS_OSCURO  = colors.HexColor('#374151')
GRIS_CLARO   = colors.HexColor('#f3f4f6')
GRIS_BORDE   = colors.HexColor('#d1d5db')
ROJO         = colors.HexColor('#991b1b')
ROJO_CLARO   = colors.HexColor('#fee2e2')
AMARILLO     = colors.HexColor('#92400e')
AMARILLO_CL  = colors.HexColor('#fef3c7')

# ── Estilos ─────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def estilo(nombre, padre='Normal', **kw):
    s = ParagraphStyle(nombre, parent=base[padre], **kw)
    return s

S = {
    'portada_titulo': estilo('portada_titulo', 'Title',
        fontSize=28, textColor=colors.white, alignment=TA_CENTER,
        spaceAfter=6, leading=34),
    'portada_sub': estilo('portada_sub', 'Normal',
        fontSize=14, textColor=colors.HexColor('#93c5fd'),
        alignment=TA_CENTER, spaceAfter=4),
    'portada_meta': estilo('portada_meta', 'Normal',
        fontSize=10, textColor=colors.HexColor('#bfdbfe'),
        alignment=TA_CENTER),
    'h1': estilo('h1', 'Heading1',
        fontSize=16, textColor=AZUL_OSCURO, spaceBefore=18, spaceAfter=6,
        borderPadding=(0, 0, 4, 0), leading=20),
    'h2': estilo('h2', 'Heading2',
        fontSize=12, textColor=AZUL_MEDIO, spaceBefore=12, spaceAfter=4,
        leading=16),
    'h3': estilo('h3', 'Heading3',
        fontSize=10, textColor=GRIS_OSCURO, spaceBefore=8, spaceAfter=3,
        fontName='Helvetica-Bold', leading=14),
    'body': estilo('body', 'Normal',
        fontSize=9.5, textColor=GRIS_OSCURO, leading=14, spaceAfter=4,
        alignment=TA_JUSTIFY),
    'bullet': estilo('bullet', 'Normal',
        fontSize=9.5, textColor=GRIS_OSCURO, leading=14,
        leftIndent=14, firstLineIndent=-10, spaceAfter=2),
    'code': estilo('code', 'Code',
        fontSize=8.5, fontName='Courier', textColor=colors.HexColor('#1e293b'),
        backColor=colors.HexColor('#f8fafc'), leading=12,
        borderPadding=6, leftIndent=8),
    'nota': estilo('nota', 'Normal',
        fontSize=8.5, textColor=AMARILLO, leading=12),
    'exito': estilo('exito', 'Normal',
        fontSize=9, textColor=VERDE, leading=13, fontName='Helvetica-Bold'),
    'error_txt': estilo('error_txt', 'Normal',
        fontSize=9, textColor=ROJO, leading=13),
    'tabla_header': estilo('tabla_header', 'Normal',
        fontSize=9, fontName='Helvetica-Bold', textColor=colors.white,
        alignment=TA_CENTER),
    'tabla_celda': estilo('tabla_celda', 'Normal',
        fontSize=8.5, textColor=GRIS_OSCURO, leading=12),
    'tabla_mono': estilo('tabla_mono', 'Normal',
        fontSize=8, fontName='Courier', textColor=colors.HexColor('#1e293b'),
        leading=11),
    'pie': estilo('pie', 'Normal',
        fontSize=7.5, textColor=colors.HexColor('#9ca3af'), alignment=TA_CENTER),
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def hr():
    return HRFlowable(width='100%', thickness=1, color=GRIS_BORDE,
                      spaceAfter=6, spaceBefore=4)

def sp(h=6):
    return Spacer(1, h)

def p(texto, estilo_key='body'):
    return Paragraph(texto, S[estilo_key])

def h1(texto):
    return p(f'<b>{texto}</b>', 'h1')

def h2(texto):
    return p(texto, 'h2')

def h3(texto):
    return p(texto, 'h3')

def bullet(texto):
    return p(f'• {texto}', 'bullet')

def code(texto):
    # Escapar caracteres especiales para XML de ReportLab
    texto = texto.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return p(f'<font name="Courier">{texto}</font>', 'code')

def caja(contenido_flowables, color_fondo=GRIS_CLARO, color_borde=GRIS_BORDE):
    """Envuelve flowables en una tabla con fondo de color."""
    inner = [[c] for c in contenido_flowables]
    # Usamos un flowable compuesto dentro de tabla de 1 celda
    datos = [[contenido_flowables]]
    t = Table([[p(' ', 'body')]], colWidths=['100%'])  # placeholder
    return contenido_flowables  # devolvemos tal cual; se maneja con tabla

def bloque_codigo(lineas):
    """Crea una tabla de fondo oscuro con código monoespacio."""
    texto = '<br/>'.join(
        l.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        for l in lineas
    )
    celda = Paragraph(f'<font name="Courier" color="#e2e8f0">{texto}</font>',
                      ParagraphStyle('code_dark', parent=base['Normal'],
                                     fontSize=8.5, leading=13,
                                     textColor=colors.HexColor('#e2e8f0'),
                                     backColor=colors.HexColor('#1e293b')))
    t = Table([[celda]], colWidths=[16.5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,-1), colors.HexColor('#1e293b')),
        ('TOPPADDING',  (0,0), (-1,-1), 10),
        ('BOTTOMPADDING',(0,0),(-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING',(0,0), (-1,-1), 12),
        ('ROUNDEDCORNERS', [4]),
    ]))
    return t

def bloque_nota(texto, tipo='info'):
    """Caja resaltada para notas, advertencias o errores."""
    cfg = {
        'info':    ('ℹ ', AZUL_CLARO,   AZUL_MEDIO,   AZUL_MEDIO),
        'ok':      ('✓ ', VERDE_CLARO,  VERDE,         VERDE),
        'warn':    ('⚠ ', AMARILLO_CL,  AMARILLO,      AMARILLO),
        'error':   ('✗ ', ROJO_CLARO,   ROJO,          ROJO),
    }
    icono, fondo, borde, tcolor = cfg.get(tipo, cfg['info'])
    st = ParagraphStyle(f'nota_{tipo}', parent=base['Normal'],
                        fontSize=9, textColor=tcolor, leading=13)
    celda = Paragraph(f'<b>{icono}</b>{texto}', st)
    t = Table([[celda]], colWidths=[16.5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), fondo),
        ('LINEABOVE',    (0,0), (-1,0),  2, borde),
        ('TOPPADDING',   (0,0), (-1,-1), 8),
        ('BOTTOMPADDING',(0,0), (-1,-1), 8),
        ('LEFTPADDING',  (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    return t

def tabla_datos(cabeceras, filas, anchos=None):
    """Tabla estilizada con cabecera azul oscuro."""
    datos = [[Paragraph(c, S['tabla_header']) for c in cabeceras]]
    for fila in filas:
        datos.append([Paragraph(str(c), S['tabla_celda']) for c in fila])
    if anchos is None:
        n = len(cabeceras)
        anchos = [16.5*cm/n]*n
    t = Table(datos, colWidths=anchos, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  AZUL_OSCURO),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, GRIS_CLARO]),
        ('GRID',          (0,0), (-1,-1), 0.5, GRIS_BORDE),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('RIGHTPADDING',  (0,0), (-1,-1), 6),
        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
    ]))
    return t

# ── Encabezado y pie de página ───────────────────────────────────────────────

def header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4

    # Encabezado — banda azul
    canvas.setFillColor(AZUL_OSCURO)
    canvas.rect(0, h - 1.5*cm, w, 1.5*cm, fill=True, stroke=False)
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawString(1.5*cm, h - 1.0*cm, 'FacturApp · Guía de Pruebas para Técnico')
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#93c5fd'))
    canvas.drawRightString(w - 1.5*cm, h - 1.0*cm, 'CONFIDENCIAL')

    # Pie de página
    canvas.setFillColor(GRIS_BORDE)
    canvas.rect(0, 0, w, 1*cm, fill=True, stroke=False)
    canvas.setFillColor(colors.HexColor('#6b7280'))
    canvas.setFont('Helvetica', 7.5)
    canvas.drawString(1.5*cm, 0.35*cm, 'FacturApp v1.2  ·  Sistema de Gestión Documental')
    canvas.drawCentredString(w/2, 0.35*cm, f'Página {doc.page}')
    canvas.drawRightString(w - 1.5*cm, 0.35*cm, 'Uso interno — no distribuir')
    canvas.restoreState()

# ── Portada ───────────────────────────────────────────────────────────────────

def portada():
    flowables = []

    # Bloque de portada como tabla de fondo azul oscuro
    titulo_p  = Paragraph('FacturApp', S['portada_titulo'])
    sub_p     = Paragraph('Guía Técnica de Pruebas Unitarias', S['portada_sub'])
    ver_p     = Paragraph('Versión 1.2  ·  Mayo 2026', S['portada_meta'])
    conf_p    = Paragraph('Documento de uso interno', S['portada_meta'])

    portada_tabla = Table(
        [[titulo_p], [sp(4)], [sub_p], [sp(2)], [ver_p], [sp(2)], [conf_p]],
        colWidths=[16.5*cm]
    )
    portada_tabla.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), AZUL_OSCURO),
        ('TOPPADDING',   (0,0), (-1,-1), 8),
        ('BOTTOMPADDING',(0,0), (-1,-1), 8),
        ('LEFTPADDING',  (0,0), (-1,-1), 20),
        ('RIGHTPADDING', (0,0), (-1,-1), 20),
        ('ROUNDEDCORNERS', [6]),
    ]))

    flowables.append(sp(40))
    flowables.append(portada_tabla)
    flowables.append(sp(20))

    # Recuadro de resumen en portada
    resumen_datos = [
        [Paragraph('<b>Cobertura</b>', S['tabla_header']),
         Paragraph('<b>Tests</b>', S['tabla_header']),
         Paragraph('<b>Requiere servidor</b>', S['tabla_header'])],
        [p('Funciones lógicas puras', 'tabla_celda'),
         p('56', 'tabla_celda'), p('No', 'tabla_celda')],
        [p('API REST Flask (backend)', 'tabla_celda'),
         p('134', 'tabla_celda'), p('No', 'tabla_celda')],
        [p('API FastAPI (usuarios)', 'tabla_celda'),
         p('69', 'tabla_celda'), p('No', 'tabla_celda')],
        [Paragraph('<b>TOTAL</b>', S['tabla_header']),
         Paragraph('<b>259</b>', S['tabla_header']),
         Paragraph('<b>—</b>', S['tabla_header'])],
    ]
    t = Table(resumen_datos, colWidths=[8*cm, 4*cm, 4.5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  AZUL_OSCURO),
        ('BACKGROUND',    (0,4), (-1,4),  AZUL_MEDIO),
        ('ROWBACKGROUNDS',(0,1), (-1,3),  [colors.white, GRIS_CLARO]),
        ('GRID',          (0,0), (-1,-1), 0.5, GRIS_BORDE),
        ('TOPPADDING',    (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('ALIGN',         (1,0), (2,-1),  'CENTER'),
    ]))
    flowables.append(t)
    flowables.append(PageBreak())
    return flowables

# ── Contenido ─────────────────────────────────────────────────────────────────

def contenido():
    E = []  # lista de flowables

    # ══════════════════════════════════════════════════════════════════
    # 1. INTRODUCCIÓN
    # ══════════════════════════════════════════════════════════════════
    E.append(h1('1. Introducción'))
    E.append(hr())
    E.append(p(
        'Este documento describe el procedimiento completo para instalar las '
        'dependencias, ejecutar y verificar la suite de <b>259 tests unitarios</b> '
        'del sistema FacturApp. Las pruebas cubren los dos microservicios Python '
        'del proyecto y no requieren que los servidores estén en ejecución: '
        'utilizan clientes de prueba con bases de datos SQLite en memoria.'
    ))
    E.append(sp(4))
    E.append(bloque_nota(
        'Todos los tests son independientes del entorno de producción. '
        'Se pueden ejecutar en cualquier máquina con Python 3.8+ instalado.',
        'ok'
    ))
    E.append(sp(8))

    # ══════════════════════════════════════════════════════════════════
    # 2. REQUISITOS PREVIOS
    # ══════════════════════════════════════════════════════════════════
    E.append(h1('2. Requisitos previos'))
    E.append(hr())

    E.append(h2('2.1  Software requerido'))
    reqs = [
        ['Componente', 'Versión mínima', 'Notas'],
        ['Python', '3.8', 'Verificar con: python --version'],
        ['pip', '21.0', 'Incluido con Python 3.8+'],
        ['Git', 'Cualquiera', 'Para clonar el repositorio'],
        ['Tesseract OCR', 'No requerido', 'Solo para pruebas de integración real'],
        ['Poppler', 'No requerido', 'Solo para pruebas de integración real'],
    ]
    E.append(tabla_datos(reqs[0], reqs[1:], anchos=[5*cm, 4*cm, 7.5*cm]))
    E.append(sp(6))

    E.append(h2('2.2  Verificar Python'))
    E.append(p('Abrir una terminal y ejecutar:'))
    E.append(bloque_codigo(['python --version', '# o en algunos sistemas:', 'python3 --version']))
    E.append(sp(4))
    E.append(bloque_nota(
        'En Windows usar <font name="Courier">python</font>. '
        'En Linux/macOS puede ser necesario usar '
        '<font name="Courier">python3</font>.',
        'info'
    ))
    E.append(sp(8))

    # ══════════════════════════════════════════════════════════════════
    # 3. ESTRUCTURA DEL PROYECTO
    # ══════════════════════════════════════════════════════════════════
    E.append(h1('3. Estructura del proyecto'))
    E.append(hr())
    E.append(p(
        'El repositorio contiene dos microservicios y una carpeta dedicada a los tests:'
    ))
    E.append(sp(4))
    E.append(bloque_codigo([
        'facturapp-dev/',
        '├── backend/                  ← Microservicio Flask (puerto 5000)',
        '│   ├── app.py',
        '│   ├── models.py',
        '│   ├── ocr_processor.py',
        '│   └── requirements.txt',
        '├── sistema_usuarios/         ← Microservicio FastAPI (puerto 8000)',
        '│   ├── main.py',
        '│   ├── models.py',
        '│   ├── database.py',
        '│   └── requirements.txt',
        '└── sistema_facturas/',
        '    └── tests/                ← Suite de tests unitarios',
        '        ├── conftest.py       ← Fixtures compartidas',
        '        ├── test_logica.py    ← Funciones puras (56 tests)',
        '        ├── test_backend.py   ← API Flask (134 tests)',
        '        └── test_usuarios.py  ← API FastAPI (69 tests)',
    ]))
    E.append(sp(8))

    # ══════════════════════════════════════════════════════════════════
    # 4. INSTALACIÓN DE DEPENDENCIAS
    # ══════════════════════════════════════════════════════════════════
    E.append(h1('4. Instalación de dependencias'))
    E.append(hr())
    E.append(p(
        'Ejecutar los siguientes comandos desde la <b>raíz del repositorio</b>. '
        'Se recomienda usar un entorno virtual para no afectar a los paquetes '
        'del sistema.'
    ))
    E.append(sp(6))

    E.append(h2('4.1  Crear entorno virtual (recomendado)'))
    E.append(bloque_codigo([
        '# Crear entorno virtual',
        'python -m venv .venv',
        '',
        '# Activar en Linux / macOS',
        'source .venv/bin/activate',
        '',
        '# Activar en Windows (CMD)',
        '.venv\\Scripts\\activate.bat',
        '',
        '# Activar en Windows (PowerShell)',
        '.venv\\Scripts\\Activate.ps1',
    ]))
    E.append(sp(6))

    E.append(h2('4.2  Instalar dependencias del backend Flask'))
    E.append(bloque_codigo([
        'cd backend',
        'pip install -r requirements.txt',
        'cd ..',
    ]))
    E.append(sp(6))

    E.append(h2('4.3  Instalar dependencias del sistema de usuarios'))
    E.append(bloque_codigo([
        'cd sistema_usuarios',
        'pip install -r requirements.txt',
        'cd ..',
    ]))
    E.append(sp(6))

    E.append(h2('4.4  Instalar dependencias adicionales para los tests'))
    E.append(p(
        'Los tests necesitan paquetes que no están en los requirements de producción:'
    ))
    E.append(bloque_codigo([
        'pip install pytest httpx',
        '',
        '# bcrypt debe ser la versión 4.x para compatibilidad con passlib',
        'pip install "bcrypt==4.0.1" --force-reinstall',
    ]))
    E.append(sp(4))
    E.append(bloque_nota(
        '<b>Importante:</b> bcrypt 5.x es incompatible con passlib. '
        'Si ya está instalado bcrypt 5.x, el comando anterior lo reemplazará '
        'por la versión correcta.',
        'warn'
    ))
    E.append(sp(6))

    E.append(h2('4.5  Verificar la instalación'))
    E.append(bloque_codigo([
        'python -m pytest --version',
        '# Debe mostrar algo como: pytest 8.x.x',
    ]))
    E.append(sp(8))

    # ══════════════════════════════════════════════════════════════════
    # 5. DESCRIPCIÓN DE LOS TESTS
    # ══════════════════════════════════════════════════════════════════
    E.append(h1('5. Descripción de los archivos de test'))
    E.append(hr())

    # conftest
    E.append(h2('5.1  conftest.py — Fixtures compartidas'))
    E.append(p(
        'Archivo de configuración de pytest que proporciona fixtures reutilizables '
        'para el resto de tests del backend Flask. No contiene tests ejecutables.'
    ))
    E.append(sp(4))
    filas_conftest = [
        ['Fixture / Helper', 'Alcance', 'Descripción'],
        ['flask_app', 'Sesión', 'Crea la app Flask con BD SQLite temporal'],
        ['client', 'Por test', 'TestClient con tablas vaciadas en cada test'],
        ['token_valido()', '—', 'Genera JWT firmado con el secreto real de la app'],
        ['token_expirado()', '—', 'Genera JWT con fecha de expiración en el pasado'],
        ['auth_admin()', '—', 'Cabeceras HTTP con token de rol admin'],
        ['auth_basico()', '—', 'Cabeceras HTTP con token de rol básico'],
        ['crear_proveedor()', '—', 'Crea proveedor mediante la API (POST)'],
        ['crear_documento()', '—', 'Inserta documento directamente en la BD'],
    ]
    E.append(tabla_datos(filas_conftest[0], filas_conftest[1:],
                         anchos=[5*cm, 2.5*cm, 9*cm]))
    E.append(sp(8))

    # test_logica
    E.append(h2('5.2  test_logica.py — Funciones lógicas puras (56 tests)'))
    E.append(p(
        'Prueba funciones de lógica interna que no requieren base de datos ni red. '
        'Son los tests más rápidos y los primeros en ejecutarse.'
    ))
    E.append(sp(4))
    filas_logica = [
        ['Clase', 'Tests', 'Función probada', 'Casos cubiertos'],
        ['TestFechasProximas', '22', '_fechas_proximas()', 'Diferencias dentro/fuera de 30 días, formatos dd/mm/yyyy, yyyy-mm-dd, dd-mm-yyyy, dd.mm.yyyy, valores None y vacíos, límite personalizado'],
        ['TestExtensionPermitida', '18', 'extension_permitida()', 'Extensiones válidas (pdf, png, jpg, jpeg, tiff, bmp), inválidas (exe, docx, txt, gif), casos sin extensión'],
        ['TestOcrEsSuficiente', '16', '_ocr_es_suficiente()', 'Textos con palabras clave (factura, total, IVA, invoice...), textos cortos, None, sin palabras clave'],
    ]
    E.append(tabla_datos(filas_logica[0], filas_logica[1:],
                         anchos=[4*cm, 1.5*cm, 4*cm, 7*cm]))
    E.append(sp(8))

    # test_backend
    E.append(h2('5.3  test_backend.py — API REST Flask (134 tests)'))
    E.append(p(
        'Prueba todos los endpoints del microservicio Flask usando un TestClient '
        'con base de datos SQLite en fichero temporal. El OCR se simula con '
        '<font name="Courier">unittest.mock.patch</font> para no requerir '
        'Tesseract instalado.'
    ))
    E.append(sp(4))
    filas_backend = [
        ['Clase', 'Tests', 'Endpoints cubiertos'],
        ['TestAutenticacion', '8', 'Todos — verifica que 401 sin token, con token expirado/malformado'],
        ['TestHealth', '3', 'GET /api/health'],
        ['TestEstadisticas', '6', 'GET /api/estadisticas'],
        ['TestDocumentosListar', '10', 'GET /api/documentos (filtros, paginación)'],
        ['TestDocumentoCRUD', '11', 'GET/PUT/DELETE /api/documentos/:id'],
        ['TestEscanear', '10', 'POST /api/escanear (PDF, PNG, formatos inválidos, error OCR)'],
        ['TestArchivoOriginal', '4', 'GET /api/documentos/:id/archivo'],
        ['TestNeteo', '13', 'GET /api/neteo/sin-asociar, POST /api/neteo/asociar, POST /api/neteo/desasociar/:id'],
        ['TestProveedoresListar', '8', 'GET /api/proveedores (búsqueda, filtro activo)'],
        ['TestProveedoresCRUD', '16', 'POST/GET/PUT/DELETE /api/proveedores/:id'],
        ['TestProveedorDesdeDocumento', '4', 'POST /api/proveedores/desde-documento/:id'],
        ['TestAlertas', '5', 'GET /api/alertas/sin-netear'],
        ['TestLogs', '8', 'GET /api/logs, DELETE /api/logs'],
        ['TestReportes', '9', 'POST /api/reportes/generar, /contable, /analitico'],
    ]
    E.append(tabla_datos(filas_backend[0], filas_backend[1:],
                         anchos=[5.5*cm, 1.5*cm, 9.5*cm]))
    E.append(sp(8))

    # test_usuarios
    E.append(h2('5.4  test_usuarios.py — API FastAPI usuarios (69 tests)'))
    E.append(p(
        'Prueba el microservicio de autenticación y gestión de usuarios. '
        'Usa una base de datos SQLite <i>in-memory</i> con '
        '<font name="Courier">StaticPool</font> para garantizar '
        'que todas las sesiones comparten la misma conexión.'
    ))
    E.append(sp(4))
    filas_usuarios = [
        ['Clase', 'Tests', 'Endpoints cubiertos'],
        ['TestHealth', '3', 'GET /health, GET /health/full'],
        ['TestLogin', '7', 'POST /token'],
        ['TestMe', '4', 'GET /me, GET /me/permissions'],
        ['TestListarUsuarios', '4', 'GET /api/users'],
        ['TestObtenerUsuario', '4', 'GET /api/users/:id'],
        ['TestCrearUsuario', '8', 'POST /admin/users'],
        ['TestEditarUsuario', '8', 'PUT /users/:id'],
        ['TestEliminarUsuario', '5', 'DELETE /api/users/:id'],
        ['TestPermisos', '8', 'GET/PUT /api/users/:id/permissions'],
        ['TestUsuarioInactivo', '6', 'Login y operaciones con usuario desactivado'],
        ['TestPaginasHTML', '5', 'GET /login, /users, /create-user, /edit-user, /profile'],
    ]
    E.append(tabla_datos(filas_usuarios[0], filas_usuarios[1:],
                         anchos=[5.5*cm, 1.5*cm, 9.5*cm]))
    E.append(sp(8))

    # ══════════════════════════════════════════════════════════════════
    # 6. EJECUCIÓN DE LOS TESTS
    # ══════════════════════════════════════════════════════════════════
    E.append(h1('6. Ejecución de los tests'))
    E.append(hr())
    E.append(bloque_nota(
        'Todos los comandos se ejecutan desde la <b>raíz del repositorio</b> '
        '(<font name="Courier">facturapp-dev/</font>). '
        'Usar siempre <font name="Courier">python -m pytest</font> para '
        'garantizar que se usa el intérprete correcto.',
        'info'
    ))
    E.append(sp(8))

    E.append(h2('6.1  Ejecutar todos los tests unitarios'))
    E.append(bloque_codigo([
        'python -m pytest sistema_facturas/tests/test_backend.py \\',
        '                 sistema_facturas/tests/test_logica.py \\',
        '                 sistema_facturas/tests/test_usuarios.py -v',
    ]))
    E.append(sp(4))
    E.append(p('<b>Resultado esperado:</b>'))
    E.append(bloque_codigo([
        '============================== test session starts ==============================',
        'collected 259 items',
        '',
        'sistema_facturas/tests/test_backend.py::TestAutenticacion::... PASSED',
        '...',
        '====================== 259 passed in ~13s =======================================',
    ]))
    E.append(sp(8))

    E.append(h2('6.2  Ejecutar un archivo de tests específico'))
    E.append(bloque_codigo([
        '# Solo tests de lógica pura (más rápidos)',
        'python -m pytest sistema_facturas/tests/test_logica.py -v',
        '',
        '# Solo tests del backend Flask',
        'python -m pytest sistema_facturas/tests/test_backend.py -v',
        '',
        '# Solo tests del sistema de usuarios',
        'python -m pytest sistema_facturas/tests/test_usuarios.py -v',
    ]))
    E.append(sp(8))

    E.append(h2('6.3  Ejecutar una clase o test concreto'))
    E.append(bloque_codigo([
        '# Ejecutar solo la clase TestAutenticacion',
        'python -m pytest sistema_facturas/tests/test_backend.py::TestAutenticacion -v',
        '',
        '# Ejecutar un test específico por nombre',
        'python -m pytest sistema_facturas/tests/test_backend.py::TestAutenticacion::test_token_expirado_retorna_401 -v',
        '',
        '# Ejecutar tests que contengan "proveedor" en el nombre',
        'python -m pytest sistema_facturas/tests/ -k "proveedor" -v',
    ]))
    E.append(sp(8))

    E.append(h2('6.4  Opciones útiles de pytest'))
    filas_opts = [
        ['Opción', 'Descripción'],
        ['-v', 'Verbose: muestra el nombre de cada test y su resultado'],
        ['-s', 'No captura stdout (útil para ver print() durante depuración)'],
        ['--tb=short', 'Tracebacks cortos en caso de fallo (por defecto)'],
        ['--tb=long', 'Tracebacks completos para diagnóstico detallado'],
        ['--tb=no', 'No muestra tracebacks (solo el resumen final)'],
        ['-x', 'Detiene la ejecución al primer fallo (fail fast)'],
        ['--lf', 'Ejecuta solo los tests que fallaron en la última ejecución'],
        ['-q', 'Salida compacta (sin nombres individuales)'],
        ['--co -q', 'Listar todos los tests sin ejecutarlos (collect-only)'],
    ]
    E.append(tabla_datos(filas_opts[0], filas_opts[1:], anchos=[3.5*cm, 13*cm]))
    E.append(sp(8))

    E.append(h2('6.5  Ejemplo de salida exitosa'))
    E.append(p(
        'Al ejecutar el comando completo se verá una salida similar a esta '
        '(las advertencias de SQLAlchemy sobre <i>Query.get()</i> legacy son '
        'informativas y no indican ningún error):'
    ))
    E.append(sp(4))
    E.append(bloque_codigo([
        '$ python -m pytest sistema_facturas/tests/test_backend.py \\',
        '                   sistema_facturas/tests/test_logica.py \\',
        '                   sistema_facturas/tests/test_usuarios.py -v',
        '',
        '============================= test session starts ==============================',
        'platform linux -- Python 3.11, pytest-9.0.3',
        'collected 259 items',
        '',
        'test_backend.py::TestAutenticacion::test_sin_cabecera_auth_retorna_401 PASSED',
        'test_backend.py::TestAutenticacion::test_token_expirado_retorna_401   PASSED',
        '...',
        'test_logica.py::TestFechasProximas::test_misma_fecha                  PASSED',
        '...',
        'test_usuarios.py::TestLogin::test_login_correcto_devuelve_token       PASSED',
        '...',
        '',
        '-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html',
        '====================== 259 passed, 47 warnings in 13.02s ====================',
    ]))
    E.append(sp(8))

    # ══════════════════════════════════════════════════════════════════
    # 7. RESOLUCIÓN DE PROBLEMAS
    # ══════════════════════════════════════════════════════════════════
    E.append(PageBreak())
    E.append(h1('7. Resolución de problemas frecuentes'))
    E.append(hr())

    problemas = [
        {
            'titulo': 'Error: No module named pytest',
            'causa':  'pytest no está instalado en el intérprete de Python que se está usando.',
            'solucion': [
                'pip install pytest',
                '# Si hay varios intérpretes instalados, usar:',
                'python3 -m pip install pytest',
            ],
            'tipo': 'error',
        },
        {
            'titulo': 'Error: No module named jwt',
            'causa':  'PyJWT no está instalado.',
            'solucion': ['pip install PyJWT'],
            'tipo': 'error',
        },
        {
            'titulo': 'Error: No module named httpx',
            'causa':  'httpx es necesario para el TestClient de FastAPI/Starlette.',
            'solucion': ['pip install httpx'],
            'tipo': 'error',
        },
        {
            'titulo': "AttributeError: module 'bcrypt' has no attribute '__about__'",
            'causa':  'bcrypt 5.x instalado. Passlib requiere bcrypt 4.x.',
            'solucion': ['pip install "bcrypt==4.0.1" --force-reinstall'],
            'tipo': 'warn',
        },
        {
            'titulo': 'ImportError: cannot import name db from models',
            'causa':  'Conflicto entre backend/models.py y sistema_usuarios/models.py. '
                      'Ambos se llaman "models" y Python carga el incorrecto.',
            'solucion': [
                '# Asegurarse de ejecutar desde la raíz del repo:',
                'python -m pytest sistema_facturas/tests/test_backend.py ...',
                '# NO desde dentro de backend/ ni sistema_usuarios/',
            ],
            'tipo': 'error',
        },
        {
            'titulo': 'sqlite3.OperationalError: no such table',
            'causa':  'La base de datos en memoria no tiene las tablas creadas.',
            'solucion': [
                '# Verificar que conftest.py está en sistema_facturas/tests/',
                '# y que test_usuarios.py usa StaticPool en TEST_ENGINE',
            ],
            'tipo': 'error',
        },
        {
            'titulo': 'Los tests de test_integracion.py fallan',
            'causa':  'test_integracion.py requiere los servidores en ejecución '
                      '(puertos 5000 y 8000). Esos tests NO forman parte de la '
                      'suite unitaria.',
            'solucion': [
                '# Para la suite unitaria, excluir test_integracion.py:',
                'python -m pytest sistema_facturas/tests/test_backend.py \\',
                '                 sistema_facturas/tests/test_logica.py \\',
                '                 sistema_facturas/tests/test_usuarios.py -v',
            ],
            'tipo': 'info',
        },
        {
            'titulo': "PermissionError o WinError al crear BD temporal",
            'causa':  'En Windows, la BD temporal puede quedar bloqueada si un test '
                      'anterior terminó de forma abrupta.',
            'solucion': [
                '# Eliminar archivos .db temporales del directorio del sistema:',
                'del %TEMP%\\test_facturas_*.db    # Windows',
                'rm /tmp/test_facturas_*.db        # Linux / macOS',
            ],
            'tipo': 'warn',
        },
    ]

    for prob in problemas:
        E.append(KeepTogether([
            h3(f'• {prob["titulo"]}'),
            p(f'<b>Causa:</b> {prob["causa"]}'),
            p('<b>Solución:</b>'),
            bloque_codigo(prob['solucion']),
            sp(6),
        ]))

    # ══════════════════════════════════════════════════════════════════
    # 8. REFERENCIA RÁPIDA
    # ══════════════════════════════════════════════════════════════════
    E.append(h1('8. Referencia rápida — Comandos esenciales'))
    E.append(hr())
    E.append(bloque_codigo([
        '# ── Instalación (una sola vez) ────────────────────────────────────',
        'cd backend && pip install -r requirements.txt && cd ..',
        'cd sistema_usuarios && pip install -r requirements.txt && cd ..',
        'pip install pytest httpx "bcrypt==4.0.1" --force-reinstall',
        '',
        '# ── Ejecución completa ────────────────────────────────────────────',
        'python -m pytest sistema_facturas/tests/test_backend.py \\',
        '                 sistema_facturas/tests/test_logica.py \\',
        '                 sistema_facturas/tests/test_usuarios.py -v',
        '',
        '# ── Por módulo ────────────────────────────────────────────────────',
        'python -m pytest sistema_facturas/tests/test_logica.py   -v  # 56 tests',
        'python -m pytest sistema_facturas/tests/test_backend.py  -v  # 134 tests',
        'python -m pytest sistema_facturas/tests/test_usuarios.py -v  # 69 tests',
        '',
        '# ── Diagnóstico ───────────────────────────────────────────────────',
        'python -m pytest sistema_facturas/tests/ --co -q   # listar tests',
        'python -m pytest sistema_facturas/tests/ -x        # parar al primer fallo',
        'python -m pytest sistema_facturas/tests/ --lf      # repetir solo fallidos',
    ]))
    E.append(sp(12))

    E.append(bloque_nota(
        '<b>Resultado esperado siempre:</b> '
        '<font name="Courier">259 passed</font> en aproximadamente 13 segundos. '
        'Cualquier número menor indica un fallo que debe investigarse.',
        'ok'
    ))

    return E

# ── Construir el PDF ──────────────────────────────────────────────────────────

def main():
    doc = SimpleDocTemplate(
        OUT,
        pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2*cm,    bottomMargin=1.5*cm,
        title='FacturApp — Guía Técnica de Pruebas Unitarias',
        author='FacturApp Dev Team',
        subject='Guía de ejecución de tests unitarios v1.2',
    )

    story = portada() + contenido()
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f'PDF generado: {OUT}')

if __name__ == '__main__':
    main()
