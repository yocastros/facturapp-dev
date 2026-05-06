"""
Genera docs/plan_pruebas_usuario.pdf
Guía de pruebas funcionales para usuario, desde la instalación en Windows.
Formato: caso de prueba con Opción / Pasos / Resultado esperado / Estado.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import os

# ── Rutas ──────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(ROOT, 'docs', 'plan_pruebas_usuario.pdf')
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# ── Paleta ─────────────────────────────────────────────────────────────────
AZUL        = colors.HexColor('#1B3A5C')
AZUL_MED    = colors.HexColor('#2A5280')
AZUL_CLARO  = colors.HexColor('#E8EEF4')
DORADO      = colors.HexColor('#C9A84C')
DORADO_CL   = colors.HexColor('#F5EDD6')
VERDE       = colors.HexColor('#166534')
VERDE_CL    = colors.HexColor('#dcfce7')
GRIS        = colors.HexColor('#374151')
GRIS_CL     = colors.HexColor('#F3F4F6')
GRIS_BD     = colors.HexColor('#D1D5DB')
ROJO        = colors.HexColor('#991B1B')
ROJO_CL     = colors.HexColor('#FEE2E2')
NARANJA     = colors.HexColor('#92400E')
NARANJA_CL  = colors.HexColor('#FEF3C7')
BLANCO      = colors.white

# ── Estilos ─────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def S(nombre, padre='Normal', **kw):
    return ParagraphStyle(nombre, parent=base[padre], **kw)

EST = {
    'h1':      S('h1',  fontSize=14, textColor=AZUL,    fontName='Helvetica-Bold',
                        spaceBefore=14, spaceAfter=4, leading=18),
    'h2':      S('h2',  fontSize=11, textColor=AZUL_MED, fontName='Helvetica-Bold',
                        spaceBefore=10, spaceAfter=3, leading=15),
    'body':    S('body', fontSize=9,  textColor=GRIS, leading=13, spaceAfter=3,
                         alignment=TA_JUSTIFY),
    'paso':    S('paso', fontSize=8.5, textColor=GRIS, leading=12, leftIndent=4),
    'result':  S('result', fontSize=8.5, textColor=VERDE, leading=12,
                           fontName='Helvetica-Bold'),
    'id_txt':  S('id_txt', fontSize=9, textColor=BLANCO, fontName='Helvetica-Bold',
                           alignment=TA_CENTER),
    'opt_txt': S('opt_txt', fontSize=9.5, textColor=BLANCO, fontName='Helvetica-Bold',
                            leading=13),
    'sec_num': S('sec_num', fontSize=20, textColor=DORADO, fontName='Helvetica-Bold',
                            alignment=TA_CENTER),
    'sec_nom': S('sec_nom', fontSize=13, textColor=BLANCO, fontName='Helvetica-Bold',
                            alignment=TA_CENTER, leading=17),
    'pie':     S('pie',  fontSize=7.5, textColor=colors.HexColor('#9CA3AF'),
                         alignment=TA_CENTER),
    'porta_t': S('porta_t', fontSize=30, textColor=BLANCO, fontName='Helvetica-Bold',
                             alignment=TA_CENTER, leading=36),
    'porta_s': S('porta_s', fontSize=14, textColor=colors.HexColor('#93C5FD'),
                             alignment=TA_CENTER),
    'porta_m': S('porta_m', fontSize=10, textColor=colors.HexColor('#BFDBFE'),
                             alignment=TA_CENTER),
    'estado':  S('estado', fontSize=8.5, textColor=GRIS, fontName='Helvetica-Bold',
                           leading=12),
    'nota_t':  S('nota_t', fontSize=8.5, textColor=NARANJA, leading=12),
}

def sp(h=6):   return Spacer(1, h)
def hr():      return HRFlowable(width='100%', thickness=0.5, color=GRIS_BD,
                                 spaceAfter=6, spaceBefore=4)
def p(t, e='body'): return Paragraph(t, EST[e])

# ── Encabezado / pie de página ───────────────────────────────────────────────
_seccion_actual = ['']

def header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(AZUL)
    canvas.rect(0, h - 1.4*cm, w, 1.4*cm, fill=True, stroke=False)
    canvas.setFillColor(BLANCO)
    canvas.setFont('Helvetica-Bold', 8.5)
    canvas.drawString(1.5*cm, h - 0.95*cm, 'FacturApp · Plan de Pruebas Funcionales')
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#93C5FD'))
    canvas.drawRightString(w - 1.5*cm, h - 0.95*cm, _seccion_actual[0])
    # pie
    canvas.setFillColor(GRIS_BD)
    canvas.rect(0, 0, w, 0.9*cm, fill=True, stroke=False)
    canvas.setFillColor(colors.HexColor('#6B7280'))
    canvas.setFont('Helvetica', 7.5)
    canvas.drawString(1.5*cm, 0.3*cm, 'FacturApp v1.2  ·  Gestión de Facturas y Albaranes')
    canvas.drawCentredString(w/2, 0.3*cm, f'Página {doc.page}')
    canvas.drawRightString(w - 1.5*cm, 0.3*cm, 'Uso interno')
    canvas.restoreState()

# ── Portada ───────────────────────────────────────────────────────────────────
def portada():
    fl = []
    cuerpo = Table([
        [p('FacturApp', 'porta_t')],
        [sp(4)],
        [p('Plan de Pruebas Funcionales', 'porta_s')],
        [sp(2)],
        [p('Guía para el tester · Windows · Versión 1.2', 'porta_m')],
        [sp(2)],
        [p('Mayo 2026', 'porta_m')],
    ], colWidths=[16.5*cm])
    cuerpo.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), AZUL),
        ('TOPPADDING',    (0,0),(-1,-1), 10),
        ('BOTTOMPADDING', (0,0),(-1,-1), 10),
        ('LEFTPADDING',   (0,0),(-1,-1), 20),
        ('RIGHTPADDING',  (0,0),(-1,-1), 20),
    ]))
    fl.append(sp(45))
    fl.append(cuerpo)
    fl.append(sp(16))

    # tabla de secciones
    secciones = [
        ['#', 'Sección', 'Casos'],
        ['0', 'Instalación en Windows',     '5'],
        ['1', 'Arranque del sistema',        '4'],
        ['2', 'Autenticación',               '5'],
        ['3', 'Dashboard',                   '2'],
        ['4', 'Escaneo de documentos',       '5'],
        ['5', 'Gestión de documentos',       '8'],
        ['6', 'Neteo factura ↔ albarán',     '5'],
        ['7', 'Gestión de proveedores',      '6'],
        ['8', 'Reportes Excel',              '4'],
        ['9', 'Panel de alertas',            '4'],
        ['10','Gestión de usuarios',         '6'],
        ['11','Permisos por módulo',         '3'],
        ['', 'TOTAL', '57'],
    ]
    datos = []
    for i, fila in enumerate(secciones):
        if i == 0:
            datos.append([Paragraph(c, S('h', fontSize=8.5, textColor=BLANCO,
                          fontName='Helvetica-Bold', alignment=TA_CENTER))
                          for c in fila])
        elif i == len(secciones)-1:
            datos.append([Paragraph(c, S('tot', fontSize=9, textColor=BLANCO,
                          fontName='Helvetica-Bold', alignment=TA_CENTER))
                          for c in fila])
        else:
            datos.append([
                Paragraph(fila[0], S(f'n{i}', fontSize=8.5, textColor=GRIS,
                          alignment=TA_CENTER)),
                Paragraph(fila[1], S(f'm{i}', fontSize=8.5, textColor=GRIS)),
                Paragraph(fila[2], S(f'c{i}', fontSize=8.5, textColor=GRIS,
                          alignment=TA_CENTER)),
            ])
    t = Table(datos, colWidths=[1.5*cm, 12.5*cm, 2.5*cm], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),  (-1,0),  AZUL),
        ('BACKGROUND',    (0,-1), (-1,-1), AZUL_MED),
        ('ROWBACKGROUNDS',(0,1),  (-1,-2), [BLANCO, GRIS_CL]),
        ('GRID',          (0,0),  (-1,-1), 0.5, GRIS_BD),
        ('TOPPADDING',    (0,0),  (-1,-1), 5),
        ('BOTTOMPADDING', (0,0),  (-1,-1), 5),
        ('LEFTPADDING',   (0,0),  (-1,-1), 6),
        ('ALIGN',         (0,0),  (0,-1),  'CENTER'),
        ('ALIGN',         (2,0),  (2,-1),  'CENTER'),
    ]))
    fl.append(t)
    fl.append(PageBreak())
    return fl

# ── Helpers de construcción de casos ────────────────────────────────────────

def separador_seccion(numero, nombre):
    """Página de separación entre secciones con fondo azul."""
    _seccion_actual[0] = f'Sección {numero} — {nombre}'
    bloque = Table([
        [p(str(numero), 'sec_num')],
        [sp(4)],
        [p(nombre, 'sec_nom')],
    ], colWidths=[16.5*cm])
    bloque.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), AZUL),
        ('TOPPADDING',    (0,0),(-1,-1), 30),
        ('BOTTOMPADDING', (0,0),(-1,-1), 30),
        ('LEFTPADDING',   (0,0),(-1,-1), 20),
        ('RIGHTPADDING',  (0,0),(-1,-1), 20),
    ]))
    return [PageBreak(), sp(80), bloque, PageBreak()]


def caso(id_, opcion, pasos, resultado, nota=None):
    """
    Genera el bloque visual de un caso de prueba.
    pasos: lista de strings
    resultado: string con el resultado esperado
    nota: string opcional de advertencia
    """
    # ── Cabecera: ID + Opción ───
    cab = Table([[
        Paragraph(id_, EST['id_txt']),
        Paragraph(opcion, EST['opt_txt']),
    ]], colWidths=[2*cm, 14.5*cm])
    cab.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), AZUL_MED),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('RIGHTPADDING',  (0,0),(-1,-1), 8),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('LINEAFTER',     (0,0),(0,-1), 0.5, DORADO),
    ]))

    # ── Pasos ───
    pasos_parrs = [Paragraph(f'<b>{i+1}.</b>  {paso}', EST['paso'])
                   for i, paso in enumerate(pasos)]

    # ── Resultado esperado ───
    res_parr = Paragraph(f'<b>Resultado esperado:</b><br/>{resultado}', EST['result'])

    # ── Estado ───
    estado_parr = Paragraph(
        '<b>Estado:</b>    [ ] Pasa      [ ] Falla      [ ] N/A      '
        '&nbsp;&nbsp;&nbsp; <b>Observaciones:</b> ________________________________',
        EST['estado']
    )

    # ── Tabla interior pasos | resultado ───
    interior_rows = [(Paragraph('<b>PASOS</b>', S('lbl', fontSize=8,
                       textColor=AZUL_MED, fontName='Helvetica-Bold')),
                      Paragraph('<b>RESULTADO ESPERADO</b>', S('lbl2', fontSize=8,
                       textColor=VERDE, fontName='Helvetica-Bold')))]
    interior_rows += [(p, res_parr) for p in pasos_parrs[:1]]
    for p_ in pasos_parrs[1:]:
        interior_rows.append((p_, Paragraph('', EST['paso'])))

    t_int = Table(interior_rows, colWidths=[9*cm, 7.5*cm])
    t_int.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  GRIS_CL),
        ('GRID',          (0,0),(-1,-1), 0.3, GRIS_BD),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ('SPAN',          (1,1),(1,-1)),  # resultado ocupa todas las filas del lado derecho
    ]))

    # ── Pie con estado ───
    t_est = Table([[estado_parr]], colWidths=[16.5*cm])
    t_est.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), DORADO_CL),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('LINEABOVE',     (0,0),(-1,0), 1, DORADO),
    ]))

    inner = [cab, t_int, t_est]

    if nota:
        t_nota = Table([[Paragraph(f'<b>NOTA: </b>{nota}', EST['nota_t'])]],
                       colWidths=[16.5*cm])
        t_nota.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), NARANJA_CL),
            ('TOPPADDING',    (0,0),(-1,-1), 4),
            ('BOTTOMPADDING', (0,0),(-1,-1), 4),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ('LINEABOVE',     (0,0),(-1,0), 1.5, NARANJA),
        ]))
        inner.append(t_nota)

    bloque_final = Table([[inner_item] for inner_item in inner],
                         colWidths=[16.5*cm])
    bloque_final.setStyle(TableStyle([
        ('BOX',           (0,0),(-1,-1), 1, AZUL_MED),
        ('TOPPADDING',    (0,0),(-1,-1), 0),
        ('BOTTOMPADDING', (0,0),(-1,-1), 0),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 0),
    ]))
    return KeepTogether([bloque_final, sp(8)])


# ══════════════════════════════════════════════════════════════════════════════
# CASOS DE PRUEBA
# ══════════════════════════════════════════════════════════════════════════════

def sec0_instalacion():
    fl = separador_seccion('0', 'Instalación en Windows')
    fl += [
        caso('INST-01', 'Descarga del instalador',
             pasos=[
                 'Abrir el explorador de archivos o el correo donde se recibió el instalador.',
                 'Localizar el archivo instalar_windows.bat.',
                 'Verificar que el archivo está completo (no truncado).',
             ],
             resultado='El archivo instalar_windows.bat existe en el equipo y su tamaño es mayor de 1 KB.',
        ),
        caso('INST-02', 'Ejecutar el instalador como Administrador',
             pasos=[
                 'Hacer clic derecho sobre instalar_windows.bat.',
                 'Seleccionar "Ejecutar como administrador".',
                 'Aceptar el aviso de Control de Cuentas de Usuario (UAC) si aparece.',
                 'Observar la ventana de consola negra que se abre.',
             ],
             resultado='La consola muestra el progreso con etiquetas [1/6] a [6/6] y el mensaje final '
                       '"Instalación completada correctamente!".',
             nota='Si aparece el mensaje "[!] Ejecuta como Administrador", cerrar y repetir el paso 1.',
        ),
        caso('INST-03', 'Verificar instalación de Python',
             pasos=[
                 'Abrir el menú Inicio y buscar "Símbolo del sistema" (CMD).',
                 'Escribir el comando:  python --version  y pulsar Enter.',
             ],
             resultado='La consola muestra "Python 3.11.x" o superior. No aparece ningún error.',
        ),
        caso('INST-04', 'Verificar instalación de Tesseract OCR',
             pasos=[
                 'En el explorador de archivos navegar a:  C:\\Program Files\\Tesseract-OCR\\',
                 'Comprobar que existe el archivo tesseract.exe.',
                 'Dentro de la carpeta tessdata\\ comprobar que existe spa.traineddata.',
             ],
             resultado='Ambos archivos existen. El sistema podrá realizar OCR en español.',
        ),
        caso('INST-05', 'Verificar acceso directo en el escritorio',
             pasos=[
                 'Ir al escritorio de Windows.',
                 'Localizar el icono "Facturas y Albaranes".',
             ],
             resultado='El icono está presente en el escritorio con el nombre del sistema.',
             nota='Si el acceso directo no aparece, ejecutar manualmente desde la carpeta del proyecto: '
                  'python crear_acceso_directo.py',
        ),
    ]
    return fl


def sec1_arranque():
    fl = separador_seccion('1', 'Arranque del sistema')
    fl += [
        caso('ARR-01', 'Arrancar el sistema desde el acceso directo',
             pasos=[
                 'Hacer doble clic en el icono "Facturas y Albaranes" del escritorio.',
                 'Esperar entre 10 y 30 segundos a que los servicios arranquen.',
                 'Observar el icono de bandeja del sistema (esquina inferior derecha).',
             ],
             resultado='Aparece el icono del sistema en la bandeja. '
                       'El navegador predeterminado se abre automáticamente con la pantalla de login.',
        ),
        caso('ARR-02', 'Verificar que ambos servicios están activos',
             pasos=[
                 'Con el sistema arrancado, abrir el navegador.',
                 'Navegar a:  http://localhost:5000/api/health',
                 'En otra pestaña navegar a:  http://localhost:8000/health',
             ],
             resultado='Ambas URLs devuelven una respuesta JSON con  "status": "ok"  '
                       'y el timestamp del servidor.',
        ),
        caso('ARR-03', 'Apertura automática del navegador',
             pasos=[
                 'Arrancar el sistema desde el acceso directo.',
                 'No abrir el navegador manualmente.',
             ],
             resultado='El sistema abre automáticamente la URL http://localhost:5000 '
                       'mostrando la pantalla de login sin intervención del usuario.',
        ),
        caso('ARR-04', 'Intentar arrancar una segunda instancia',
             pasos=[
                 'Con el sistema ya corriendo, hacer doble clic de nuevo en el acceso directo.',
             ],
             resultado='No se abre una segunda instancia. En su lugar, se abre el navegador '
                       'con la aplicación ya activa en http://localhost:5000.',
        ),
    ]
    return fl


def sec2_autenticacion():
    fl = separador_seccion('2', 'Autenticación')
    fl += [
        caso('AUTH-01', 'Login con credenciales correctas (administrador)',
             pasos=[
                 'Con el navegador en http://localhost:5000, observar la pantalla de login.',
                 'En el campo "Usuario" escribir:  admin',
                 'En el campo "Contraseña" escribir la contraseña del administrador.',
                 'Hacer clic en el botón "Iniciar sesión".',
             ],
             resultado='El sistema redirige al Dashboard principal. '
                       'En la esquina superior aparece el nombre del usuario y su rol "Administrador".',
        ),
        caso('AUTH-02', 'Login con contraseña incorrecta',
             pasos=[
                 'En la pantalla de login escribir un usuario válido.',
                 'En el campo contraseña escribir una contraseña incorrecta.',
                 'Hacer clic en "Iniciar sesión".',
             ],
             resultado='Aparece un mensaje de error: "Credenciales incorrectas" o similar. '
                       'La pantalla de login permanece visible. No se accede al sistema.',
        ),
        caso('AUTH-03', 'Login con usuario inexistente',
             pasos=[
                 'En la pantalla de login escribir un usuario que no existe (ej: usuario_falso).',
                 'Escribir cualquier contraseña.',
                 'Hacer clic en "Iniciar sesión".',
             ],
             resultado='Aparece un mensaje de error. '
                       'El sistema no revela si el usuario existe o no. No se accede.',
        ),
        caso('AUTH-04', 'Cierre de sesión',
             pasos=[
                 'Con sesión iniciada, localizar el menú de usuario (esquina superior).',
                 'Hacer clic en "Cerrar sesión" o "Logout".',
             ],
             resultado='La sesión se cierra y se muestra de nuevo la pantalla de login. '
                       'Al pulsar "Atrás" en el navegador no se puede volver a la aplicación sin login.',
        ),
        caso('AUTH-05', 'Acceso con sesión expirada',
             pasos=[
                 'Iniciar sesión correctamente.',
                 'Dejar la aplicación sin usar durante el tiempo de expiración del token (normalmente 8 horas) '
                   'O modificar manualmente el token en el almacenamiento del navegador para que sea inválido.',
                 'Intentar realizar cualquier acción (ej: cargar documentos).',
             ],
             resultado='El sistema detecta la sesión inválida, muestra un aviso '
                       'y redirige automáticamente a la pantalla de login.',
             nota='Para pruebas rápidas: abrir Herramientas de desarrollador (F12) → Aplicación → '
                  'Local Storage → borrar el token y recargar la página.',
        ),
    ]
    return fl


def sec3_dashboard():
    fl = separador_seccion('3', 'Dashboard')
    fl += [
        caso('DASH-01', 'Visualizar KPIs del dashboard',
             pasos=[
                 'Iniciar sesión como administrador.',
                 'Observar la pantalla principal (Dashboard).',
                 'Identificar los indicadores de resumen (KPIs).',
             ],
             resultado='Se muestran al menos los siguientes indicadores: '
                       'Total de documentos, Total de facturas, Total de albaranes, '
                       'Documentos pendientes de neteo, Importe total. '
                       'Todos muestran valores numéricos (pueden ser 0 si la BD está vacía).',
        ),
        caso('DASH-02', 'KPIs reflejan datos reales',
             pasos=[
                 'Anotar el valor de "Total de documentos" que muestra el Dashboard.',
                 'Ir al módulo "Documentos" y contar el número de documentos listados.',
                 'Volver al Dashboard.',
             ],
             resultado='El número de documentos en el Dashboard coincide con '
                       'el número de documentos listados en el módulo Documentos.',
        ),
    ]
    return fl


def sec4_escaneo():
    fl = separador_seccion('4', 'Escaneo de documentos (OCR)')
    fl += [
        caso('ESC-01', 'Subir una factura en formato PDF',
             pasos=[
                 'Ir al módulo "Escanear" en el menú lateral.',
                 'Hacer clic en el área de carga o en "Seleccionar archivo".',
                 'Seleccionar un archivo PDF que contenga una factura real.',
                 'Hacer clic en "Escanear" o "Procesar".',
                 'Esperar a que el sistema termine el procesamiento.',
             ],
             resultado='El sistema muestra los datos extraídos: número de factura, '
                       'fecha, proveedor, CIF, base imponible, IVA y total. '
                       'El documento queda guardado con estado "PROCESADO".',
        ),
        caso('ESC-02', 'Subir un albarán en formato imagen (JPG o PNG)',
             pasos=[
                 'Ir al módulo "Escanear".',
                 'Seleccionar un archivo JPG o PNG con imagen de un albarán.',
                 'Hacer clic en "Escanear".',
             ],
             resultado='El sistema procesa la imagen y extrae los campos disponibles. '
                       'El documento se guarda con tipo "albaran" y estado "PROCESADO".',
             nota='Si la imagen tiene baja resolución, algunos campos pueden quedar vacíos. '
                  'Esto es comportamiento esperado; el usuario deberá corregirlos manualmente.',
        ),
        caso('ESC-03', 'Intentar subir un formato no soportado',
             pasos=[
                 'Ir al módulo "Escanear".',
                 'Intentar seleccionar un archivo .docx, .xlsx o .txt.',
             ],
             resultado='El sistema rechaza el archivo antes de enviarlo al servidor '
                       'con un mensaje indicando los formatos aceptados '
                       '(PDF, PNG, JPG, JPEG, TIFF, BMP).',
        ),
        caso('ESC-04', 'Verificar datos extraídos por OCR',
             pasos=[
                 'Subir un documento con datos legibles (buena calidad).',
                 'Revisar cada campo extraído: número, fecha, proveedor, CIF, total.',
                 'Comparar visualmente con el documento original.',
             ],
             resultado='Los campos coinciden con el documento original. '
                       'El total extraído coincide con el impreso en el documento.',
        ),
        caso('ESC-05', 'Corregir datos mal extraídos por OCR',
             pasos=[
                 'Localizar un documento recién escaneado con algún campo incorrecto.',
                 'Hacer clic en "Editar" sobre ese documento.',
                 'Corregir el campo erróneo (ej: número de factura).',
                 'Hacer clic en "Guardar".',
             ],
             resultado='El campo corregido se actualiza correctamente. '
                       'Al volver al detalle del documento el valor guardado es el nuevo.',
        ),
    ]
    return fl


def sec5_documentos():
    fl = separador_seccion('5', 'Gestión de documentos')
    fl += [
        caso('DOC-01', 'Listar todos los documentos',
             pasos=[
                 'Ir al módulo "Documentos" en el menú lateral.',
             ],
             resultado='Se muestra la lista de documentos con columnas: '
                       'tipo, número, fecha, proveedor, total y estado.',
        ),
        caso('DOC-02', 'Filtrar documentos por tipo',
             pasos=[
                 'En la lista de documentos, localizar el filtro "Tipo".',
                 'Seleccionar "Factura".',
                 'Observar los resultados.',
                 'Cambiar el filtro a "Albarán".',
             ],
             resultado='Con "Factura" solo se muestran facturas. '
                       'Con "Albarán" solo se muestran albaranes. '
                       'El contador de resultados cambia acorde.',
        ),
        caso('DOC-03', 'Filtrar documentos por estado',
             pasos=[
                 'En la lista de documentos, localizar el filtro "Estado".',
                 'Seleccionar "PENDIENTE".',
                 'Luego seleccionar "PROCESADO".',
             ],
             resultado='Cada filtro muestra solo los documentos con ese estado. '
                       'Los documentos no coincidentes quedan ocultos.',
        ),
        caso('DOC-04', 'Buscar documentos por número o proveedor',
             pasos=[
                 'En la lista de documentos, localizar el campo de búsqueda.',
                 'Escribir el número de una factura conocida (ej: FAC-2025-001).',
                 'Observar los resultados.',
                 'Borrar y escribir el nombre de un proveedor.',
             ],
             resultado='La búsqueda filtra los resultados en tiempo real o al confirmar. '
                       'Solo se muestran documentos que coincidan con el término buscado.',
        ),
        caso('DOC-05', 'Ver detalle de un documento',
             pasos=[
                 'En la lista de documentos, hacer clic sobre cualquier documento.',
             ],
             resultado='Se abre la vista de detalle con todos los campos del documento: '
                       'tipo, número, fecha, proveedor, CIF, base imponible, IVA, total, '
                       'estado y, si está neteado, la factura o albaranes asociados.',
        ),
        caso('DOC-06', 'Editar un documento existente',
             pasos=[
                 'Abrir el detalle de un documento.',
                 'Hacer clic en "Editar".',
                 'Modificar el campo "Total" con un valor diferente.',
                 'Hacer clic en "Guardar".',
             ],
             resultado='El sistema confirma el guardado. Al volver al detalle, '
                       'el campo Total muestra el nuevo valor.',
        ),
        caso('DOC-07', 'Eliminar un documento',
             pasos=[
                 'Abrir el detalle de un documento que no tenga albaranes asociados.',
                 'Hacer clic en "Eliminar".',
                 'Confirmar la acción en el diálogo de confirmación.',
             ],
             resultado='El documento desaparece de la lista. '
                       'Si se busca por su número, no aparece en los resultados.',
             nota='Los documentos con albaranes asociados deben desasociarse antes de poder eliminarse.',
        ),
        caso('DOC-08', 'Ver el archivo original del documento',
             pasos=[
                 'Abrir el detalle de un documento que fue subido como archivo.',
                 'Hacer clic en "Ver archivo original" o en el nombre del archivo.',
             ],
             resultado='El navegador abre o descarga el archivo original (PDF o imagen) '
                       'tal como fue subido al sistema.',
        ),
    ]
    return fl


def sec6_neteo():
    fl = separador_seccion('6', 'Neteo factura ↔ albarán')
    fl += [
        caso('NET-01', 'Ver documentos sin netear',
             pasos=[
                 'Ir al módulo "Neteo" en el menú lateral.',
                 'Observar los dos paneles: "Facturas sin asociar" y "Albaranes sin asociar".',
             ],
             resultado='Se muestran todas las facturas en estado PROCESADO sin albarán '
                       'y todos los albaranes sin factura asociada.',
        ),
        caso('NET-02', 'Asociar manualmente un albarán a una factura',
             pasos=[
                 'En el módulo Neteo, seleccionar una factura del panel izquierdo.',
                 'En el panel derecho, seleccionar uno o varios albaranes del mismo proveedor.',
                 'Hacer clic en "Asociar".',
             ],
             resultado='La factura y el/los albarán/es desaparecen de los paneles de pendientes. '
                       'El estado del albarán cambia a "FACTURA_ASOCIADA". '
                       'La factura muestra los albaranes vinculados en su detalle.',
        ),
        caso('NET-03', 'Neteo automático por número de albarán',
             pasos=[
                 'Subir una factura cuyo texto OCR contenga el número de un albarán ya existente '
                   '(ej: en el cuerpo de la factura aparece "Alb. 2025-100").',
                 'Observar el estado de la factura recién escaneada.',
             ],
             resultado='El sistema detecta automáticamente el número de albarán y asocia '
                       'la factura con ese albarán sin intervención manual. '
                       'Ambos documentos muestran el estado "FACTURA_ASOCIADA".',
             nota='El neteo automático ocurre durante el escaneo si el número de albarán '
                  'aparece en el texto extraído por OCR.',
        ),
        caso('NET-04', 'Desasociar un albarán de su factura',
             pasos=[
                 'Abrir el detalle de una factura neteada (con albaranes asociados).',
                 'Localizar el albarán a desasociar en la sección de albaranes vinculados.',
                 'Hacer clic en "Desasociar" junto al albarán.',
                 'Confirmar la acción.',
             ],
             resultado='El albarán queda libre y vuelve a aparecer en el panel de albaranes '
                       'sin asociar del módulo Neteo.',
        ),
        caso('NET-05', 'Verificar estados tras desasociar el último albarán',
             pasos=[
                 'Localizar una factura que tenga solo un albarán asociado.',
                 'Desasociar ese único albarán (ver NET-04).',
                 'Verificar el estado de la factura en la lista de documentos.',
             ],
             resultado='Al quedar sin ningún albarán, la factura vuelve al estado '
                       '"PROCESADO" (ya no está marcada como neteada).',
        ),
    ]
    return fl


def sec7_proveedores():
    fl = separador_seccion('7', 'Gestión de proveedores')
    fl += [
        caso('PROV-01', 'Crear un proveedor manualmente',
             pasos=[
                 'Ir al módulo "Proveedores" en el menú lateral.',
                 'Hacer clic en "Nuevo proveedor".',
                 'Rellenar los campos: Nombre (obligatorio), CIF, Email, Teléfono, Dirección.',
                 'Hacer clic en "Guardar".',
             ],
             resultado='El proveedor aparece en la lista de proveedores. '
                       'El sistema confirma la creación con un mensaje de éxito.',
        ),
        caso('PROV-02', 'Crear proveedor desde un documento escaneado',
             pasos=[
                 'Abrir el detalle de un documento escaneado que tenga proveedor y CIF extraídos.',
                 'Hacer clic en "Crear proveedor desde este documento".',
             ],
             resultado='Se crea un nuevo proveedor con los datos del documento pre-rellenados. '
                       'El documento queda vinculado al nuevo proveedor.',
             nota='Si ya existe un proveedor con el mismo CIF, el sistema debe '
                  'mostrar un aviso y no crear un duplicado.',
        ),
        caso('PROV-03', 'Buscar proveedor por nombre o CIF',
             pasos=[
                 'En la lista de proveedores, escribir parte del nombre o el CIF en el buscador.',
             ],
             resultado='La lista se filtra mostrando solo los proveedores que coinciden '
                       'con el término de búsqueda. La búsqueda no distingue mayúsculas.',
        ),
        caso('PROV-04', 'Ver detalle de proveedor con historial de documentos',
             pasos=[
                 'En la lista de proveedores, hacer clic sobre un proveedor.',
             ],
             resultado='Se abre el detalle con todos los datos del proveedor '
                       'y un listado de los últimos documentos asociados a él.',
        ),
        caso('PROV-05', 'Editar datos de un proveedor',
             pasos=[
                 'Abrir el detalle de un proveedor.',
                 'Hacer clic en "Editar".',
                 'Cambiar el campo "Email" por una dirección diferente.',
                 'Hacer clic en "Guardar".',
             ],
             resultado='El email actualizado aparece en el detalle del proveedor.',
        ),
        caso('PROV-06', 'Desactivar un proveedor',
             pasos=[
                 'Abrir el detalle de un proveedor.',
                 'Hacer clic en "Desactivar" o cambiar el estado a "Inactivo".',
                 'Confirmar la acción.',
                 'Volver a la lista de proveedores y aplicar el filtro "Activos".',
             ],
             resultado='El proveedor desactivado ya no aparece en el filtro "Activos". '
                       'Sus documentos históricos permanecen en el sistema.',
        ),
    ]
    return fl


def sec8_reportes():
    fl = separador_seccion('8', 'Reportes Excel')
    fl += [
        caso('REP-01', 'Generar reporte estándar de documentos',
             pasos=[
                 'Ir al módulo "Reportes" en el menú lateral.',
                 'Seleccionar "Reporte estándar".',
                 'Dejar las fechas en blanco (todos los documentos).',
                 'Hacer clic en "Generar".',
             ],
             resultado='El navegador descarga un archivo Excel (.xlsx) con '
                       'todos los documentos del sistema, incluyendo: tipo, número, '
                       'fecha, proveedor, base imponible, IVA, total y estado.',
        ),
        caso('REP-02', 'Generar reporte con filtro de fechas',
             pasos=[
                 'Ir al módulo "Reportes".',
                 'En "Fecha desde" escribir el primer día del mes actual.',
                 'En "Fecha hasta" escribir el día de hoy.',
                 'Hacer clic en "Generar".',
             ],
             resultado='El Excel descargado contiene solo los documentos '
                       'cuya fecha está dentro del rango indicado.',
        ),
        caso('REP-03', 'Generar informe contable',
             pasos=[
                 'Ir al módulo "Reportes".',
                 'Seleccionar "Informe contable".',
                 'Opcionalmente seleccionar un proveedor concreto.',
                 'Hacer clic en "Generar".',
             ],
             resultado='El Excel incluye el desglose por proveedor: '
                       'total de facturas, base imponible acumulada, IVA acumulado '
                       'y total acumulado por proveedor.',
        ),
        caso('REP-04', 'Generar análisis CPP (análisis de compras)',
             pasos=[
                 'Ir al módulo "Reportes".',
                 'Seleccionar "Análisis CPP".',
                 'Hacer clic en "Generar".',
             ],
             resultado='El Excel incluye el análisis de coste por proveedor '
                       'con totales agrupados por categoría.',
        ),
    ]
    return fl


def sec9_alertas():
    fl = separador_seccion('9', 'Panel de alertas')
    fl += [
        caso('ALRT-01', 'Ver el panel de alertas',
             pasos=[
                 'Localizar el icono de campana o el badge de alertas en el menú.',
                 'Hacer clic en él para abrir el panel de alertas.',
             ],
             resultado='Se muestra la lista de facturas sin netear agrupadas por urgencia: '
                       'Normal, Aviso y Crítico.',
        ),
        caso('ALRT-02', 'Verificar alerta de nivel Normal (menos de 15 días)',
             pasos=[
                 'Crear o localizar una factura escaneada hace menos de 15 días sin albarán asociado.',
                 'Abrir el panel de alertas.',
             ],
             resultado='La factura aparece en el nivel "Normal" (color neutro o verde). '
                       'Indica que tiene margen de tiempo.',
        ),
        caso('ALRT-03', 'Verificar alerta de nivel Aviso (15–30 días)',
             pasos=[
                 'Localizar una factura con más de 15 días sin netear.',
                 'Abrir el panel de alertas.',
             ],
             resultado='La factura aparece en el nivel "Aviso" (color naranja o amarillo). '
                       'El sistema recomienda atenderla pronto.',
        ),
        caso('ALRT-04', 'Verificar alerta crítica (más de 30 días)',
             pasos=[
                 'Localizar una factura con más de 30 días sin netear.',
                 'Abrir el panel de alertas.',
             ],
             resultado='La factura aparece en el nivel "Crítico" (color rojo). '
                       'El badge del menú muestra el número de alertas críticas.',
        ),
    ]
    return fl


def sec10_usuarios():
    fl = separador_seccion('10', 'Gestión de usuarios')
    fl += [
        caso('USR-01', 'Acceder a la gestión de usuarios (solo admin)',
             pasos=[
                 'Con sesión de administrador, navegar a http://localhost:8000/users '
                   'o hacer clic en el enlace de gestión de usuarios si existe en la interfaz.',
             ],
             resultado='Se muestra la lista de usuarios del sistema con nombre, email, rol y estado.',
             nota='Los usuarios con rol "básico" o "supervisor" no deben ver este módulo. '
                  'Si un usuario básico intenta acceder, debe recibir un error 403.',
        ),
        caso('USR-02', 'Crear un nuevo usuario',
             pasos=[
                 'En la gestión de usuarios, hacer clic en "Nuevo usuario".',
                 'Rellenar: Nombre de usuario, Email, Contraseña (mínimo 6 caracteres), '
                   'Nombre completo y Rol (admin/supervisor/básico).',
                 'Hacer clic en "Crear".',
             ],
             resultado='El nuevo usuario aparece en la lista. '
                       'Se puede iniciar sesión con ese usuario desde la pantalla de login.',
        ),
        caso('USR-03', 'Editar datos de un usuario',
             pasos=[
                 'En la lista de usuarios, hacer clic en "Editar" sobre un usuario.',
                 'Cambiar el campo "Nombre completo".',
                 'Hacer clic en "Guardar".',
             ],
             resultado='Los datos actualizados aparecen en la lista de usuarios.',
        ),
        caso('USR-04', 'Desactivar un usuario',
             pasos=[
                 'En la lista de usuarios, hacer clic en "Desactivar" sobre un usuario activo.',
                 'Confirmar la acción.',
                 'Intentar hacer login con ese usuario.',
             ],
             resultado='El usuario queda marcado como inactivo en la lista. '
                       'El intento de login con ese usuario es rechazado '
                       'con un mensaje de "Usuario inactivo" o credenciales inválidas.',
        ),
        caso('USR-05', 'Reactivar un usuario desactivado',
             pasos=[
                 'Localizar un usuario con estado "Inactivo".',
                 'Hacer clic en "Activar".',
                 'Intentar hacer login con ese usuario.',
             ],
             resultado='El usuario vuelve a estar activo. El login funciona correctamente.',
        ),
        caso('USR-06', 'Cambiar la contraseña de un usuario',
             pasos=[
                 'Como administrador, editar un usuario.',
                 'Escribir una nueva contraseña en el campo "Nueva contraseña".',
                 'Guardar los cambios.',
                 'Cerrar sesión e intentar acceder con la nueva contraseña.',
             ],
             resultado='La nueva contraseña funciona. La contraseña anterior queda invalidada.',
        ),
    ]
    return fl


def sec11_permisos():
    fl = separador_seccion('11', 'Permisos por módulo')
    fl += [
        caso('PERM-01', 'Configurar permisos de un usuario',
             pasos=[
                 'En la gestión de usuarios, hacer clic en "Permisos" de un usuario básico.',
                 'Desactivar el permiso del módulo "Reportes".',
                 'Activar el permiso del módulo "Documentos".',
                 'Guardar.',
             ],
             resultado='Los permisos quedan guardados. Al consultar los permisos del usuario '
                       'se reflejan los cambios realizados.',
        ),
        caso('PERM-02', 'Verificar acceso restringido a un módulo',
             pasos=[
                 'Iniciar sesión con el usuario al que se le quitó el permiso de "Reportes" (ver PERM-01).',
                 'Intentar acceder al módulo "Reportes" desde el menú.',
             ],
             resultado='El módulo "Reportes" no aparece en el menú lateral '
                       'o, si se accede directamente por URL, el sistema muestra '
                       'un mensaje de acceso denegado.',
        ),
        caso('PERM-03', 'Usuario básico sin acceso a gestión de usuarios',
             pasos=[
                 'Iniciar sesión con un usuario de rol "básico".',
                 'Intentar acceder a http://localhost:8000/users',
             ],
             resultado='El sistema devuelve un error de acceso denegado (403) '
                       'o redirige al login. El usuario básico no puede ver ni gestionar usuarios.',
        ),
    ]
    return fl


# ── Ensamblar documento ───────────────────────────────────────────────────────

def main():
    doc = SimpleDocTemplate(
        OUT,
        pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2*cm,    bottomMargin=1.5*cm,
        title='FacturApp — Plan de Pruebas Funcionales',
        author='FacturApp Dev Team',
        subject='Plan de pruebas funcionales para usuario final v1.2',
    )

    story = (
        portada()
        + sec0_instalacion()
        + sec1_arranque()
        + sec2_autenticacion()
        + sec3_dashboard()
        + sec4_escaneo()
        + sec5_documentos()
        + sec6_neteo()
        + sec7_proveedores()
        + sec8_reportes()
        + sec9_alertas()
        + sec10_usuarios()
        + sec11_permisos()
    )

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f'PDF generado: {OUT}')

if __name__ == '__main__':
    main()
