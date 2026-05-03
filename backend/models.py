from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Proveedor(db.Model):
    __tablename__ = 'proveedores'

    id         = db.Column(db.Integer, primary_key=True)
    nombre     = db.Column(db.String(200), nullable=False)
    cif        = db.Column(db.String(20), unique=True, nullable=True, index=True)
    email      = db.Column(db.String(100), nullable=True)
    telefono   = db.Column(db.String(30), nullable=True)
    direccion  = db.Column(db.String(300), nullable=True)
    notas      = db.Column(db.Text, nullable=True)
    fecha_alta = db.Column(db.DateTime, default=datetime.utcnow)
    activo     = db.Column(db.Boolean, default=True)
    documentos = db.relationship('Documento', backref='proveedor_obj',
                                 lazy='dynamic', foreign_keys='Documento.proveedor_id')

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'cif': self.cif,
            'email': self.email,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'notas': self.notas,
            'fecha_alta': self.fecha_alta.isoformat() if self.fecha_alta else None,
            'activo': self.activo,
            'num_documentos': self.documentos.count(),
        }


class Documento(db.Model):
    __tablename__ = 'documentos'

    id             = db.Column(db.Integer, primary_key=True)
    tipo           = db.Column(db.String(20), nullable=False)  # 'factura' o 'albaran'
    numero         = db.Column(db.String(100))
    fecha          = db.Column(db.String(50))
    proveedor      = db.Column(db.String(200))
    cif            = db.Column(db.String(20))
    base_imponible = db.Column(db.Float, default=0.0)
    iva            = db.Column(db.Float, default=0.0)
    total          = db.Column(db.Float, default=0.0)
    porcentaje_iva = db.Column(db.Float, default=21.0)
    estado         = db.Column(db.String(30), default='PENDIENTE')
    # Estados: PENDIENTE, PROCESADO, ERROR, FACTURA_ASOCIADA
    archivo_original = db.Column(db.String(500))
    texto_ocr        = db.Column(db.Text)
    fecha_subida     = db.Column(db.DateTime, default=datetime.utcnow)
    notas            = db.Column(db.Text)

    proveedor_id          = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=True)
    proveedor_normalizado = db.Column(db.Boolean, default=False)
    lineas                = db.relationship('LineaDocumento', backref='documento',
                                            lazy='dynamic', cascade='all, delete-orphan',
                                            order_by='LineaDocumento.orden')

    # Relaciones de neteo: una factura puede tener muchos albaranes asociados
    factura_id = db.Column(db.Integer, db.ForeignKey('documentos.id'), nullable=True)
    albaranes_asociados = db.relationship(
        'Documento',
        backref=db.backref('factura_padre', remote_side=[id]),
        lazy='dynamic'
    )

    def to_dict(self):
        albaranes = []
        if self.tipo == 'factura':
            albaranes = [a.to_dict_simple() for a in self.albaranes_asociados.all()]

        return {
            'id': self.id,
            'tipo': self.tipo,
            'numero': self.numero,
            'fecha': self.fecha,
            'proveedor': self.proveedor,
            'cif': self.cif,
            'base_imponible': self.base_imponible,
            'iva': self.iva,
            'total': self.total,
            'porcentaje_iva': self.porcentaje_iva,
            'estado': self.estado,
            'archivo_original': self.archivo_original,
            'fecha_subida': self.fecha_subida.isoformat() if self.fecha_subida else None,
            'notas': self.notas,
            'factura_id': self.factura_id,
            'albaranes_asociados': albaranes,
            'proveedor_id': self.proveedor_id,
            'proveedor_normalizado': self.proveedor_normalizado,
            'lineas': [l.to_dict() for l in self.lineas.all()],
        }

    def to_dict_simple(self):
        return {
            'id': self.id,
            'tipo': self.tipo,
            'numero': self.numero,
            'fecha': self.fecha,
            'proveedor': self.proveedor,
            'total': self.total,
            'estado': self.estado,
        }


class LineaDocumento(db.Model):
    __tablename__ = 'lineas_documento'

    id              = db.Column(db.Integer, primary_key=True)
    documento_id    = db.Column(db.Integer, db.ForeignKey('documentos.id',
                                 ondelete='CASCADE'), nullable=False)
    descripcion     = db.Column(db.String(500))
    cantidad        = db.Column(db.Float, default=1.0)
    unidad          = db.Column(db.String(30), nullable=True)
    precio_unitario = db.Column(db.Float, default=0.0)
    importe_linea   = db.Column(db.Float, default=0.0)
    orden           = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'documento_id': self.documento_id,
            'descripcion': self.descripcion,
            'cantidad': self.cantidad,
            'unidad': self.unidad,
            'precio_unitario': self.precio_unitario,
            'importe_linea': self.importe_linea,
            'orden': self.orden,
        }


class LogActividad(db.Model):
    __tablename__ = 'log_actividad'

    id         = db.Column(db.Integer, primary_key=True)
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    usuario    = db.Column(db.String(100), nullable=False, index=True)
    accion     = db.Column(db.String(50), nullable=False, index=True)
    entidad    = db.Column(db.String(50), nullable=True)
    entidad_id = db.Column(db.Integer, nullable=True)
    detalle    = db.Column(db.String(500), nullable=True)
    ip         = db.Column(db.String(45), nullable=True)
    resultado  = db.Column(db.String(10), default='ok')

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'usuario': self.usuario,
            'accion': self.accion,
            'entidad': self.entidad,
            'entidad_id': self.entidad_id,
            'detalle': self.detalle,
            'ip': self.ip,
            'resultado': self.resultado,
        }
