import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config_loader import get_secret_key
import uuid
import logging
from datetime import datetime
from pathlib import Path
from functools import wraps

# ── Variables de entorno para Windows (Tesseract + Poppler) ──────────────
_tesseract_data = r"C:\Program Files\Tesseract-OCR\tessdata"
if os.path.exists(_tesseract_data):
    os.environ.setdefault('TESSDATA_PREFIX', _tesseract_data)

_tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
try:
    import pytesseract
    if os.path.exists(_tesseract_cmd):
        pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd
except ImportError:
    pass
# ─────────────────────────────────────────────────────────────────────────

from flask import Flask, request, jsonify, send_file, send_from_directory, g
import requests as http_requests
from flask_cors import CORS
from models import db, Documento, Proveedor, LineaDocumento, LogActividad
from ocr_processor import procesar_documento
from report_generator import generar_reporte_excel, generar_reporte_contable, generar_reporte_analitico

try:
    import jwt as pyjwt
    JWT_DISPONIBLE = True
except ImportError:
    JWT_DISPONIBLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Debe coincidir con SECRET_KEY del sistema de usuarios
_JWT_SECRET = get_secret_key()
_JWT_ALGORITHM = "HS256"

# ── Constantes de acciones para el log ───────────────────────────────────────
LOG_LOGIN       = 'LOGIN'
LOG_ESCANEAR    = 'ESCANEAR'
LOG_EDITAR_DOC  = 'EDITAR_DOC'
LOG_BORRAR_DOC  = 'BORRAR_DOC'
LOG_NETEAR      = 'NETEAR'
LOG_DESNETEAR   = 'DESNETEAR'
LOG_CREAR_PROV  = 'CREAR_PROV'
LOG_EDITAR_PROV = 'EDITAR_PROV'
LOG_BORRAR_PROV = 'BORRAR_PROV'
LOG_PROV_DOC    = 'PROV_DOC'
LOG_REPORTE     = 'REPORTE'


def require_auth(f):
    """Valida el token JWT emitido por el sistema de usuarios."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not JWT_DISPONIBLE:
            return f(*args, **kwargs)  # Sin PyJWT instalado, modo sin auth
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'error': 'No autorizado. Inicia sesión en el sistema de usuarios.'}), 401
        token = auth.split(' ', 1)[1]
        try:
            payload = pyjwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
            request.usuario = payload
        except pyjwt.ExpiredSignatureError:
            return jsonify({'error': 'Sesión expirada. Vuelve a iniciar sesión.'}), 401
        except pyjwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido.'}), 401
        return f(*args, **kwargs)
    return decorated

def _get_usuario():
    """Devuelve el nombre de usuario del token JWT, o 'desconocido' si no hay."""
    payload = getattr(request, 'usuario', None)
    if payload:
        return payload.get('sub', 'desconocido')
    return 'sin-auth'


def _es_admin():
    payload = getattr(request, 'usuario', None)
    return bool(payload and payload.get('role') == 'admin')


def registrar_log(usuario, accion, entidad=None, entidad_id=None, detalle=None, resultado='ok'):
    try:
        log = LogActividad(
            usuario=usuario,
            accion=accion,
            entidad=entidad,
            entidad_id=entidad_id,
            detalle=detalle,
            ip=request.remote_addr,
            resultado=resultado,
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error registrando log: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass


# Configuración
BASE_DIR = Path(__file__).parent.parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
REPORTS_FOLDER = BASE_DIR / 'reports'
DB_PATH = BASE_DIR / 'sistema_facturas.db'

UPLOAD_FOLDER.mkdir(exist_ok=True)
REPORTS_FOLDER.mkdir(exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB

EXTENSIONES_PERMITIDAS = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp'}

db.init_app(app)

with app.app_context():
    db.create_all()
    # Migración: añadir columnas nuevas a tablas existentes
    from sqlalchemy import inspect, text
    _inspector = inspect(db.engine)
    _cols_doc = {c['name'] for c in _inspector.get_columns('documentos')}
    with db.engine.connect() as _conn:
        if 'proveedor_id' not in _cols_doc:
            _conn.execute(text(
                'ALTER TABLE documentos ADD COLUMN proveedor_id INTEGER REFERENCES proveedores(id)'))
        if 'proveedor_normalizado' not in _cols_doc:
            _conn.execute(text(
                'ALTER TABLE documentos ADD COLUMN proveedor_normalizado BOOLEAN DEFAULT 0'))
        _conn.commit()
    logger.info("Base de datos inicializada")


def extension_permitida(filename):
    return Path(filename).suffix.lower() in EXTENSIONES_PERMITIDAS


# ═══════════════════════════════════════════════════════════
# ENDPOINTS DE DOCUMENTOS
# ═══════════════════════════════════════════════════════════

@app.route('/api/escanear', methods=['POST'])
@require_auth
def escanear_documento():
    """Sube y procesa un documento con OCR."""
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se proporcionó archivo'}), 400

    archivo = request.files['archivo']
    if not archivo.filename:
        return jsonify({'error': 'Nombre de archivo vacío'}), 400

    if not extension_permitida(archivo.filename):
        return jsonify({'error': f'Formato no soportado. Use: PDF, PNG, JPG, TIFF'}), 400

    # Guardar archivo
    ext = Path(archivo.filename).suffix.lower()
    nombre_unico = f"{uuid.uuid4().hex}{ext}"
    ruta_archivo = UPLOAD_FOLDER / nombre_unico
    archivo.save(str(ruta_archivo))

    # Procesar con OCR
    try:
        resultado = procesar_documento(str(ruta_archivo))
    except Exception as e:
        logger.error(f"Error OCR: {e}")
        if ruta_archivo.exists():
            ruta_archivo.unlink()
        registrar_log(_get_usuario(), LOG_ESCANEAR,
                      detalle=f'OCR error: {str(e)[:200]}', resultado='error')
        return jsonify({'error': f'Error procesando documento: {str(e)}'}), 500

    if resultado.get('estado') == 'ERROR':
        if ruta_archivo.exists():
            ruta_archivo.unlink()
            logger.info(f"Archivo eliminado por validación fallida: {nombre_unico}")
        registrar_log(_get_usuario(), LOG_ESCANEAR,
                      detalle=resultado.get('error', 'Validación fallida')[:200], resultado='error')
        return jsonify({'error': resultado.get('error', 'Error desconocido')}), 422

    # Crear registro en BD
    doc = Documento(
        tipo=resultado['tipo'],
        numero=resultado.get('numero'),
        fecha=resultado.get('fecha'),
        proveedor=resultado.get('proveedor'),
        cif=resultado.get('cif'),
        base_imponible=resultado.get('base_imponible', 0),
        iva=resultado.get('iva', 0),
        total=resultado.get('total', 0),
        porcentaje_iva=resultado.get('porcentaje_iva', 21.0),
        estado='PROCESADO',
        archivo_original=nombre_unico,  # nombre uuid para recuperar el archivo
        texto_ocr=resultado.get('texto_ocr', ''),
    )
    db.session.add(doc)
    db.session.flush()  # Para obtener el ID

    # Neteo automático si es factura
    albaranes_referenciados = resultado.get('albaranes_referenciados', [])
    albaranes_neteados = []

    if doc.tipo == 'factura':
        albaranes_neteados = _netear_factura(doc, albaranes_referenciados)

    db.session.commit()

    # Guardar líneas de detalle
    lineas_data = resultado.get('lineas', [])
    for linea_data in lineas_data:
        linea = LineaDocumento(
            documento_id=doc.id,
            descripcion=linea_data.get('descripcion', ''),
            cantidad=float(linea_data.get('cantidad', 1.0)),
            unidad=linea_data.get('unidad'),
            precio_unitario=float(linea_data.get('precio_unitario', 0.0)),
            importe_linea=float(linea_data.get('importe_linea', 0.0)),
            orden=linea_data.get('orden', 0),
        )
        db.session.add(linea)

    # Normalizar proveedor
    cif_extraido = resultado.get('cif')
    nombre_extraido = resultado.get('proveedor') or ''
    proveedor_match = None

    if cif_extraido:
        proveedor_match = Proveedor.query.filter_by(cif=cif_extraido, activo=True).first()

    if not proveedor_match and nombre_extraido:
        import difflib
        todos = Proveedor.query.filter_by(activo=True).all()
        if todos:
            nombres_map = {p.nombre: p for p in todos}
            matches = difflib.get_close_matches(
                nombre_extraido, nombres_map.keys(), n=1, cutoff=0.75
            )
            if matches:
                proveedor_match = nombres_map[matches[0]]

    if proveedor_match:
        doc.proveedor_id = proveedor_match.id
        doc.proveedor_normalizado = True
        doc.proveedor = proveedor_match.nombre

    db.session.commit()

    response = doc.to_dict()
    response['albaranes_neteados_automaticamente'] = len(albaranes_neteados)
    response['lineas_extraidas'] = len(lineas_data)
    response['proveedor_normalizado'] = doc.proveedor_normalizado

    registrar_log(_get_usuario(), LOG_ESCANEAR, entidad='documento', entidad_id=doc.id,
                  detalle=f'{doc.tipo} {doc.numero or ""} — {doc.proveedor or ""}')
    return jsonify(response), 201


def _netear_factura(factura, numeros_albaran_ref):
    """Intenta asociar albaranes a una factura automáticamente."""
    asociados = []

    # Buscar por número de albarán mencionado en la factura
    for num_alb in numeros_albaran_ref:
        alb = Documento.query.filter(
            Documento.tipo == 'albaran',
            Documento.numero.ilike(f'%{num_alb}%'),
            Documento.factura_id.is_(None)
        ).first()
        if alb:
            alb.factura_id = factura.id
            alb.estado = 'FACTURA_ASOCIADA'
            asociados.append(alb)

    # Si no encontró por número, buscar por proveedor y fecha próxima
    if not asociados and factura.proveedor:
        albaranes_candidatos = Documento.query.filter(
            Documento.tipo == 'albaran',
            Documento.factura_id.is_(None),
            Documento.proveedor.ilike(f'%{factura.proveedor[:10]}%')
        ).all()

        for alb in albaranes_candidatos:
            if _fechas_proximas(factura.fecha, alb.fecha, dias=30):
                alb.factura_id = factura.id
                alb.estado = 'FACTURA_ASOCIADA'
                asociados.append(alb)

    if asociados:
        factura.estado = 'FACTURA_ASOCIADA'

    return asociados


def _fechas_proximas(fecha1_str, fecha2_str, dias=30):
    """Comprueba si dos fechas están dentro de N días de diferencia."""
    if not fecha1_str or not fecha2_str:
        return False
    formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d.%m.%Y']
    f1 = f2 = None
    for fmt in formatos:
        try:
            f1 = datetime.strptime(fecha1_str, fmt)
            break
        except ValueError:
            continue
    for fmt in formatos:
        try:
            f2 = datetime.strptime(fecha2_str, fmt)
            break
        except ValueError:
            continue
    if f1 and f2:
        return abs((f1 - f2).days) <= dias
    return False



@app.route('/api/documentos/<int:doc_id>/archivo', methods=['GET'])
@require_auth
def ver_archivo(doc_id):
    """Sirve el archivo original para visualizarlo en el navegador."""
    doc = Documento.query.get_or_404(doc_id)
    if not doc.archivo_original:
        return jsonify({'error': 'Sin archivo asociado'}), 404
    ruta = UPLOAD_FOLDER / doc.archivo_original
    if not ruta.exists():
        return jsonify({'error': 'Archivo no encontrado en disco'}), 404
    ext = ruta.suffix.lower()
    mimes = {
        '.pdf': 'application/pdf',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.tiff': 'image/tiff',
        '.tif': 'image/tiff',
        '.bmp': 'image/bmp',
    }
    mime = mimes.get(ext, 'application/octet-stream')
    return send_file(str(ruta), mimetype=mime)


@app.route('/api/documentos', methods=['GET'])
@require_auth
def listar_documentos():
    """Lista todos los documentos con filtros opcionales."""
    tipo = request.args.get('tipo')
    estado = request.args.get('estado')
    busqueda = request.args.get('q')
    pagina = int(request.args.get('pagina', 1))
    por_pagina = int(request.args.get('por_pagina', 50))

    query = Documento.query

    if tipo:
        query = query.filter(Documento.tipo == tipo)
    if estado:
        query = query.filter(Documento.estado == estado)
    if busqueda:
        busq = f'%{busqueda}%'
        query = query.filter(
            db.or_(
                Documento.numero.ilike(busq),
                Documento.proveedor.ilike(busq),
                Documento.cif.ilike(busq),
            )
        )

    total = query.count()
    docs = query.order_by(Documento.fecha_subida.desc()) \
                .offset((pagina - 1) * por_pagina) \
                .limit(por_pagina).all()

    return jsonify({
        'documentos': [d.to_dict() for d in docs],
        'total': total,
        'pagina': pagina,
        'por_pagina': por_pagina,
        'paginas': (total + por_pagina - 1) // por_pagina,
    })


@app.route('/api/documentos/<int:doc_id>', methods=['GET'])
@require_auth
def obtener_documento(doc_id):
    doc = Documento.query.get_or_404(doc_id)
    return jsonify(doc.to_dict())


@app.route('/api/documentos/<int:doc_id>', methods=['PUT'])
@require_auth
def actualizar_documento(doc_id):
    doc = Documento.query.get_or_404(doc_id)
    datos = request.get_json()

    campos = ['tipo', 'numero', 'fecha', 'proveedor', 'cif',
              'base_imponible', 'iva', 'total', 'notas']
    for campo in campos:
        if campo in datos:
            setattr(doc, campo, datos[campo])

    db.session.commit()
    registrar_log(_get_usuario(), LOG_EDITAR_DOC, entidad='documento', entidad_id=doc_id,
                  detalle=f'{doc.tipo} {doc.numero or ""}')
    return jsonify(doc.to_dict())


@app.route('/api/documentos/<int:doc_id>', methods=['DELETE'])
@require_auth
def eliminar_documento(doc_id):
    doc = Documento.query.get_or_404(doc_id)
    detalle_borrado = f'{doc.tipo} {doc.numero or ""} — {doc.proveedor or ""}'
    for alb in doc.albaranes_asociados.all():
        alb.factura_id = None
        alb.estado = 'PROCESADO'
    db.session.delete(doc)
    db.session.commit()
    registrar_log(_get_usuario(), LOG_BORRAR_DOC, entidad='documento', entidad_id=doc_id,
                  detalle=detalle_borrado)
    return jsonify({'mensaje': 'Documento eliminado correctamente'})


# ═══════════════════════════════════════════════════════════
# ENDPOINTS DE NETEO
# ═══════════════════════════════════════════════════════════

@app.route('/api/neteo/asociar', methods=['POST'])
@require_auth
def asociar_manualmente():
    """Asocia manualmente una factura con uno o varios albaranes."""
    datos = request.get_json()
    factura_id = datos.get('factura_id')
    albaran_ids = datos.get('albaran_ids', [])

    if not factura_id:
        return jsonify({'error': 'factura_id requerido'}), 400

    factura = Documento.query.filter_by(id=factura_id, tipo='factura').first()
    if not factura:
        return jsonify({'error': 'Factura no encontrada'}), 404

    asociados = []
    for alb_id in albaran_ids:
        alb = Documento.query.filter_by(id=alb_id, tipo='albaran').first()
        if alb:
            alb.factura_id = factura_id
            alb.estado = 'FACTURA_ASOCIADA'
            asociados.append(alb.to_dict_simple())

    if asociados:
        factura.estado = 'FACTURA_ASOCIADA'

    db.session.commit()
    registrar_log(_get_usuario(), LOG_NETEAR, entidad='factura', entidad_id=factura_id,
                  detalle=f'{len(asociados)} albarán(es) asociado(s)')
    return jsonify({
        'mensaje': f'{len(asociados)} albarán(es) asociado(s)',
        'factura': factura.to_dict(),
        'asociados': asociados,
    })


@app.route('/api/neteo/desasociar/<int:albaran_id>', methods=['POST'])
@require_auth
def desasociar_albaran(albaran_id):
    """Desasocia un albarán de su factura."""
    alb = Documento.query.filter_by(id=albaran_id, tipo='albaran').first()
    if not alb:
        return jsonify({'error': 'Albarán no encontrado'}), 404

    factura_id_anterior = alb.factura_id
    alb.factura_id = None
    alb.estado = 'PROCESADO'

    # Revisar si la factura padre sigue teniendo albaranes
    if factura_id_anterior:
        factura = Documento.query.get(factura_id_anterior)
        if factura and factura.albaranes_asociados.count() == 0:
            factura.estado = 'PROCESADO'

    db.session.commit()
    registrar_log(_get_usuario(), LOG_DESNETEAR, entidad='albaran', entidad_id=albaran_id,
                  detalle=f'Desasociado de factura {factura_id_anterior}')
    return jsonify({'mensaje': 'Albarán desasociado correctamente', 'albaran': alb.to_dict()})


@app.route('/api/neteo/sin-asociar', methods=['GET'])
@require_auth
def documentos_sin_asociar():
    """Lista facturas sin albaranes y albaranes sin factura."""
    facturas_sin = Documento.query.filter_by(tipo='factura', estado='PROCESADO').all()
    albaranes_sin = Documento.query.filter_by(tipo='albaran', factura_id=None).all()

    return jsonify({
        'facturas_sin_albaran': [f.to_dict_simple() for f in facturas_sin],
        'albaranes_sin_factura': [a.to_dict_simple() for a in albaranes_sin],
    })


# ═══════════════════════════════════════════════════════════
# ENDPOINTS DE PROVEEDORES
# ═══════════════════════════════════════════════════════════

@app.route('/api/proveedores', methods=['GET'])
@require_auth
def listar_proveedores():
    q        = request.args.get('q', '').strip()
    activo   = request.args.get('activo')
    pagina   = int(request.args.get('pagina', 1))
    por_pagina = int(request.args.get('por_pagina', 50))

    query = Proveedor.query
    if q:
        busq = f'%{q}%'
        query = query.filter(
            db.or_(Proveedor.nombre.ilike(busq), Proveedor.cif.ilike(busq))
        )
    if activo is not None:
        query = query.filter(Proveedor.activo == (activo.lower() == 'true'))

    total = query.count()
    proveedores = query.order_by(Proveedor.nombre) \
                       .offset((pagina - 1) * por_pagina) \
                       .limit(por_pagina).all()

    return jsonify({
        'proveedores': [p.to_dict() for p in proveedores],
        'total': total,
        'pagina': pagina,
        'paginas': (total + por_pagina - 1) // por_pagina,
    })


@app.route('/api/proveedores', methods=['POST'])
@require_auth
def crear_proveedor():
    datos = request.get_json() or {}
    nombre = datos.get('nombre', '').strip()
    if not nombre:
        return jsonify({'error': 'El campo nombre es obligatorio'}), 400

    cif = datos.get('cif', '').strip() or None
    if cif and Proveedor.query.filter_by(cif=cif).first():
        return jsonify({'error': 'Ya existe un proveedor con ese CIF'}), 409

    prov = Proveedor(
        nombre=nombre,
        cif=cif,
        email=datos.get('email', '').strip() or None,
        telefono=datos.get('telefono', '').strip() or None,
        direccion=datos.get('direccion', '').strip() or None,
        notas=datos.get('notas', '').strip() or None,
    )
    db.session.add(prov)
    db.session.commit()
    registrar_log(_get_usuario(), LOG_CREAR_PROV, entidad='proveedor', entidad_id=prov.id,
                  detalle=prov.nombre)
    return jsonify(prov.to_dict()), 201


@app.route('/api/proveedores/<int:prov_id>', methods=['GET'])
@require_auth
def obtener_proveedor(prov_id):
    prov = Proveedor.query.get_or_404(prov_id)
    data = prov.to_dict()
    ultimos = prov.documentos.order_by(Documento.fecha_subida.desc()).limit(20).all()
    data['ultimos_documentos'] = [d.to_dict_simple() for d in ultimos]
    return jsonify(data)


@app.route('/api/proveedores/<int:prov_id>', methods=['PUT'])
@require_auth
def actualizar_proveedor(prov_id):
    prov = Proveedor.query.get_or_404(prov_id)
    datos = request.get_json() or {}

    if 'cif' in datos:
        cif_nuevo = datos['cif'].strip() or None
        if cif_nuevo and cif_nuevo != prov.cif:
            if Proveedor.query.filter(Proveedor.cif == cif_nuevo, Proveedor.id != prov_id).first():
                return jsonify({'error': 'Ya existe un proveedor con ese CIF'}), 409
        prov.cif = cif_nuevo

    for campo in ['nombre', 'email', 'telefono', 'direccion', 'notas', 'activo']:
        if campo in datos:
            setattr(prov, campo, datos[campo])

    db.session.commit()
    registrar_log(_get_usuario(), LOG_EDITAR_PROV, entidad='proveedor', entidad_id=prov_id,
                  detalle=prov.nombre)
    return jsonify(prov.to_dict())


@app.route('/api/proveedores/<int:prov_id>', methods=['DELETE'])
@require_auth
def eliminar_proveedor(prov_id):
    prov = Proveedor.query.get_or_404(prov_id)
    n = prov.documentos.count()
    if n > 0:
        return jsonify({
            'error': f'No se puede eliminar: tiene {n} documento(s) asociado(s). Desvincula los documentos primero.'
        }), 409
    nombre_borrado = prov.nombre
    db.session.delete(prov)
    db.session.commit()
    registrar_log(_get_usuario(), LOG_BORRAR_PROV, entidad='proveedor', entidad_id=prov_id,
                  detalle=nombre_borrado)
    return jsonify({'mensaje': 'Proveedor eliminado'})


@app.route('/api/proveedores/desde-documento/<int:doc_id>', methods=['POST'])
@require_auth
def proveedor_desde_documento(doc_id):
    import difflib
    doc = Documento.query.get_or_404(doc_id)

    if doc.proveedor_id:
        return jsonify({'error': 'El documento ya tiene proveedor asignado'}), 409

    cif = (doc.cif or '').strip() or None

    # Reusar proveedor existente con mismo CIF, o crear uno nuevo
    prov = None
    if cif:
        prov = Proveedor.query.filter_by(cif=cif).first()
    if not prov:
        prov = Proveedor(nombre=doc.proveedor or 'Sin nombre', cif=cif)
        db.session.add(prov)
        db.session.flush()

    # Asociar todos los documentos coincidentes
    todos = Documento.query.filter(Documento.proveedor_id.is_(None)).all()
    asociados = 0
    for d in todos:
        coincide = False
        if cif and d.cif and d.cif.strip() == cif:
            coincide = True
        elif doc.proveedor and d.proveedor:
            ratio = difflib.SequenceMatcher(None, doc.proveedor.lower(), d.proveedor.lower()).ratio()
            if ratio >= 0.80:
                coincide = True
        if coincide:
            d.proveedor_id = prov.id
            d.proveedor_normalizado = True
            asociados += 1

    db.session.commit()
    registrar_log(_get_usuario(), LOG_PROV_DOC, entidad='proveedor', entidad_id=prov.id,
                  detalle=f'{prov.nombre} — {asociados} doc(s) asociados')
    return jsonify({'proveedor': prov.to_dict(), 'documentos_asociados': asociados})


# ═══════════════════════════════════════════════════════════
# ESTADÍSTICAS Y REPORTES
# ═══════════════════════════════════════════════════════════

@app.route('/api/estadisticas', methods=['GET'])
@require_auth
def obtener_estadisticas():
    """Estadísticas generales del sistema."""
    total = Documento.query.count()
    facturas = Documento.query.filter_by(tipo='factura').count()
    albaranes = Documento.query.filter_by(tipo='albaran').count()
    procesados = Documento.query.filter_by(estado='PROCESADO').count()
    pendientes = Documento.query.filter_by(estado='PENDIENTE').count()
    errores = Documento.query.filter_by(estado='ERROR').count()
    neteados = Documento.query.filter_by(estado='FACTURA_ASOCIADA').count()

    # Importes
    from sqlalchemy import func
    total_facturas_importe = db.session.query(
        func.sum(Documento.total)
    ).filter_by(tipo='factura').scalar() or 0

    total_albaranes_importe = db.session.query(
        func.sum(Documento.total)
    ).filter_by(tipo='albaran').scalar() or 0

    return jsonify({
        'total_documentos': total,
        'facturas': facturas,
        'albaranes': albaranes,
        'procesados': procesados,
        'pendientes': pendientes,
        'errores': errores,
        'neteados': neteados,
        'importe_facturas': round(total_facturas_importe, 2),
        'importe_albaranes': round(total_albaranes_importe, 2),
        'importe_total': round(total_facturas_importe + total_albaranes_importe, 2),
    })


@app.route('/api/reportes/generar', methods=['POST'])
@require_auth
def generar_reporte():
    """Genera y devuelve un reporte Excel."""
    datos = request.get_json() or {}
    fecha_desde = datos.get('fecha_desde')
    fecha_hasta = datos.get('fecha_hasta')

    # Obtener documentos
    docs = Documento.query.order_by(Documento.fecha_subida.desc()).all()
    docs_dict = [d.to_dict() for d in docs]

    # Generar reporte
    nombre = f"reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    ruta_salida = str(REPORTS_FOLDER / nombre)

    ruta, error = generar_reporte_excel(docs_dict, ruta_salida, fecha_desde, fecha_hasta)

    if error:
        return jsonify({'error': error}), 500

    registrar_log(_get_usuario(), LOG_REPORTE, detalle='Reporte general Excel')
    return send_file(
        ruta,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=nombre
    )


@app.route('/api/reportes/contable', methods=['POST'])
@require_auth
def generar_reporte_contable_endpoint():
    datos        = request.get_json() or {}
    fecha_desde  = datos.get('fecha_desde')
    fecha_hasta  = datos.get('fecha_hasta')
    proveedor_id = datos.get('proveedor_id')

    query = Documento.query.filter_by(tipo='factura')
    if fecha_desde:
        query = query.filter(Documento.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Documento.fecha <= fecha_hasta)
    if proveedor_id:
        query = query.filter(Documento.proveedor_id == proveedor_id)

    docs = query.order_by(Documento.fecha).all()
    if not docs:
        return jsonify({'error': 'No hay facturas para los filtros seleccionados'}), 404

    nombre_proveedor = 'Todos los proveedores'
    if proveedor_id:
        p = Proveedor.query.get(proveedor_id)
        if p:
            nombre_proveedor = p.nombre

    docs_dict = [d.to_dict() for d in docs]
    nombre = f"contable_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    ruta = str(REPORTS_FOLDER / nombre)

    ruta, error = generar_reporte_contable(docs_dict, ruta, nombre_proveedor)
    if error:
        return jsonify({'error': error}), 500

    registrar_log(_get_usuario(), LOG_REPORTE, detalle=f'Reporte contable — {nombre_proveedor}')
    return send_file(
        ruta,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=nombre
    )


@app.route('/api/reportes/analitico', methods=['POST'])
@require_auth
def generar_reporte_analitico_endpoint():
    datos        = request.get_json() or {}
    fecha_desde  = datos.get('fecha_desde')
    fecha_hasta  = datos.get('fecha_hasta')
    proveedor_id = datos.get('proveedor_id')

    query = Documento.query.filter(Documento.lineas.any())
    if fecha_desde:
        query = query.filter(Documento.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Documento.fecha <= fecha_hasta)
    if proveedor_id:
        query = query.filter(Documento.proveedor_id == proveedor_id)

    docs = query.order_by(Documento.fecha).all()
    if not docs:
        return jsonify({'error': 'No hay documentos con líneas de detalle para los filtros seleccionados'}), 404

    nombre_proveedor = 'Todos los proveedores'
    if proveedor_id:
        p = Proveedor.query.get(proveedor_id)
        if p:
            nombre_proveedor = p.nombre

    docs_dict = [d.to_dict() for d in docs]
    nombre = f"analitico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    ruta = str(REPORTS_FOLDER / nombre)

    ruta, error = generar_reporte_analitico(docs_dict, ruta, nombre_proveedor)
    if error:
        return jsonify({'error': error}), 500

    registrar_log(_get_usuario(), LOG_REPORTE, detalle=f'Reporte analítico — {nombre_proveedor}')
    return send_file(
        ruta,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=nombre
    )


# ═══════════════════════════════════════════════════════════
# LOGS DE ACTIVIDAD
# ═══════════════════════════════════════════════════════════

@app.route('/api/logs', methods=['GET'])
@require_auth
def listar_logs():
    if not _es_admin():
        return jsonify({'error': 'Solo administradores'}), 403

    usuario    = request.args.get('usuario', '').strip()
    accion     = request.args.get('accion', '').strip()
    fecha_desde = request.args.get('fecha_desde', '').strip()
    fecha_hasta = request.args.get('fecha_hasta', '').strip()
    resultado  = request.args.get('resultado', '').strip()
    pagina     = max(1, int(request.args.get('pagina', 1)))
    por_pagina = min(200, max(1, int(request.args.get('por_pagina', 50))))

    query = LogActividad.query
    if usuario:
        query = query.filter(LogActividad.usuario.ilike(f'%{usuario}%'))
    if accion:
        query = query.filter(LogActividad.accion == accion)
    if fecha_desde:
        query = query.filter(LogActividad.timestamp >= fecha_desde)
    if fecha_hasta:
        query = query.filter(LogActividad.timestamp <= fecha_hasta + ' 23:59:59')
    if resultado:
        query = query.filter(LogActividad.resultado == resultado)

    total = query.count()
    logs  = query.order_by(LogActividad.timestamp.desc()) \
                 .offset((pagina - 1) * por_pagina) \
                 .limit(por_pagina).all()

    return jsonify({
        'logs': [l.to_dict() for l in logs],
        'total': total,
        'pagina': pagina,
        'por_pagina': por_pagina,
        'paginas': max(1, (total + por_pagina - 1) // por_pagina),
    })


@app.route('/api/logs', methods=['DELETE'])
@require_auth
def purgar_logs():
    if not _es_admin():
        return jsonify({'error': 'Solo administradores'}), 403

    dias = max(1, int(request.args.get('dias', 90)))
    from datetime import timedelta
    fecha_limite = datetime.utcnow() - timedelta(days=dias)
    eliminados = LogActividad.query.filter(LogActividad.timestamp < fecha_limite).delete()
    db.session.commit()
    return jsonify({'eliminados': eliminados, 'dias': dias})


@app.route('/api/logs/evento', methods=['POST'])
def registrar_evento_externo():
    """Acepta eventos de log desde servicios internos (solo localhost, sin JWT)."""
    if request.remote_addr not in ('127.0.0.1', '::1'):
        return jsonify({'error': 'No autorizado'}), 403

    datos = request.get_json() or {}
    log = LogActividad(
        usuario=datos.get('usuario', 'desconocido'),
        accion=datos.get('accion', 'EVENTO'),
        entidad=datos.get('entidad'),
        entidad_id=datos.get('entidad_id'),
        detalle=datos.get('detalle'),
        ip=datos.get('ip') or request.remote_addr,
        resultado=datos.get('resultado', 'ok'),
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({'ok': True}), 201


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()})


# ═══════════════════════════════════════════════════════════
# SERVIR FRONTEND
# ═══════════════════════════════════════════════════════════

FRONTEND_DIR = str(BASE_DIR / 'frontend')

@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)


if __name__ == '__main__':
    print("Sistema de Facturas y Albaranes iniciado")
    print("   Backend: http://localhost:5000")
    app.run(debug=False, host='0.0.0.0', port=5000)
