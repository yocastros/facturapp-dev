# Modelos de Base de Datos

El sistema usa **dos bases de datos SQLite independientes**, una por servicio.
Ambas se crean automáticamente en el primer arranque.

---

## sistema_facturas.db

Gestionada por `backend/models.py` con Flask-SQLAlchemy.  
Ubicación: `sistema_facturas.db` en la raíz del proyecto.

### Diagrama de relaciones

```
┌─────────────┐         ┌──────────────────┐         ┌────────────────────┐
│  proveedores│         │    documentos    │         │  lineas_documento  │
│─────────────│         │──────────────────│         │────────────────────│
│ id (PK)     │◄────────│ proveedor_id(FK) │◄────────│ documento_id (FK)  │
│ nombre      │  0..N   │ id (PK)          │  0..N   │ id (PK)            │
│ cif (UQ)    │         │ tipo             │         │ descripcion        │
│ email       │         │ numero           │         │ cantidad           │
│ telefono    │         │ fecha            │         │ unidad             │
│ direccion   │         │ proveedor        │         │ precio_unitario    │
│ notas       │         │ cif              │         │ importe_linea      │
│ fecha_alta  │         │ base_imponible   │         │ orden              │
│ activo      │         │ iva              │         └────────────────────┘
└─────────────┘         │ total            │
                        │ porcentaje_iva   │    ┌──────────────────┐
                        │ estado           │    │  log_actividad   │
                        │ archivo_original │    │──────────────────│
                        │ texto_ocr        │    │ id (PK)          │
                        │ fecha_subida     │    │ timestamp        │
                        │ notas            │    │ usuario          │
                        │ factura_id (FK)◄─┐    │ accion           │
                        │ proveedor_norm.  │ │  │ entidad          │
                        └──────────────────┘ │  │ entidad_id       │
                               │self          │  │ detalle          │
                               └──────────────┘  │ ip               │
                          (albaran → su factura)  │ resultado        │
                                                 └──────────────────┘
```

---

### Tabla: `proveedores`

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | INTEGER | PK, autoincrement | Identificador único |
| `nombre` | VARCHAR(200) | NOT NULL | Nombre o razón social |
| `cif` | VARCHAR(20) | UNIQUE, nullable, index | CIF/NIF del proveedor |
| `email` | VARCHAR(100) | nullable | Correo de contacto |
| `telefono` | VARCHAR(30) | nullable | Teléfono de contacto |
| `direccion` | VARCHAR(300) | nullable | Dirección postal |
| `notas` | TEXT | nullable | Observaciones libres |
| `fecha_alta` | DATETIME | default: now | Fecha de creación del registro |
| `activo` | BOOLEAN | default: True | Si el proveedor está activo |

**Relaciones:**
- `documentos` → 1:N con `Documento` (via `Documento.proveedor_id`)

---

### Tabla: `documentos`

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | INTEGER | PK, autoincrement | Identificador único |
| `tipo` | VARCHAR(20) | NOT NULL | `'factura'` o `'albaran'` |
| `numero` | VARCHAR(100) | nullable | Número de documento extraído por OCR |
| `fecha` | VARCHAR(50) | nullable | Fecha del documento (string, formato variable) |
| `proveedor` | VARCHAR(200) | nullable | Nombre del proveedor extraído por OCR |
| `cif` | VARCHAR(20) | nullable | CIF extraído por OCR |
| `base_imponible` | FLOAT | default: 0.0 | Base imponible en euros |
| `iva` | FLOAT | default: 0.0 | Importe de IVA en euros |
| `total` | FLOAT | default: 0.0 | Total del documento en euros |
| `porcentaje_iva` | FLOAT | default: 21.0 | Porcentaje de IVA aplicado |
| `estado` | VARCHAR(30) | default: `'PENDIENTE'` | Estado actual del documento |
| `archivo_original` | VARCHAR(500) | nullable | Nombre del fichero subido |
| `texto_ocr` | TEXT | nullable | Texto completo extraído por OCR (no se expone en API) |
| `fecha_subida` | DATETIME | default: now | Timestamp de subida al sistema |
| `notas` | TEXT | nullable | Notas manuales del usuario |
| `factura_id` | INTEGER | FK → `documentos.id`, nullable | Si es albarán: ID de la factura asociada |
| `proveedor_id` | INTEGER | FK → `proveedores.id`, nullable | Proveedor normalizado asignado |
| `proveedor_normalizado` | BOOLEAN | default: False | Si el proveedor ha sido asociado al catálogo |

**Estados posibles:**

| Estado | Cuándo se asigna |
|--------|-----------------|
| `PENDIENTE` | Recién subido, antes de procesar OCR |
| `PROCESADO` | OCR completado con éxito |
| `ERROR` | Falló OCR o el documento no superó la validación |
| `FACTURA_ASOCIADA` | Es un albarán y ya tiene `factura_id` asignado |

**Relaciones:**
- `albaranes_asociados` → 1:N con sí mismo: facturas tienen albaranes hijos (`factura_id`)
- `lineas` → 1:N con `LineaDocumento` (cascade delete)
- `proveedor_obj` → N:1 con `Proveedor`

> **Nota sobre `fecha`:** Se almacena como string porque los formatos de fecha en facturas y albaranes son muy variables (DD/MM/YYYY, YYYY-MM-DD, "15 de marzo de 2024", etc.). El OCR extrae el texto tal cual y se normaliza en la UI.

---

### Tabla: `lineas_documento`

Almacena las líneas de detalle extraídas por OCR (descripción, cantidad, precio unitario, importe). Solo se rellenan cuando el OCR es capaz de identificar una tabla de líneas en el documento.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | INTEGER | PK, autoincrement | Identificador único |
| `documento_id` | INTEGER | FK → `documentos.id`, CASCADE DELETE | Documento al que pertenece |
| `descripcion` | VARCHAR(500) | nullable | Descripción del artículo o servicio |
| `cantidad` | FLOAT | default: 1.0 | Cantidad |
| `unidad` | VARCHAR(30) | nullable | Unidad de medida (ud, kg, l, caja…) |
| `precio_unitario` | FLOAT | default: 0.0 | Precio por unidad en euros |
| `importe_linea` | FLOAT | default: 0.0 | Importe total de la línea |
| `orden` | INTEGER | default: 0 | Posición de la línea en el documento |

**Relaciones:**
- `documento` → N:1 con `Documento` (backref)

---

### Tabla: `log_actividad`

Registro inmutable de todas las acciones realizadas en el sistema. Se escribe en cada operación de escritura mediante `registrar_log()`.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | INTEGER | PK, autoincrement | Identificador único |
| `timestamp` | DATETIME | default: now, index | Momento de la acción |
| `usuario` | VARCHAR(100) | NOT NULL, index | Username del usuario autenticado |
| `accion` | VARCHAR(50) | NOT NULL, index | Código de acción (ver tabla de acciones) |
| `entidad` | VARCHAR(50) | nullable | Tipo de objeto afectado (`documento`, `proveedor`) |
| `entidad_id` | INTEGER | nullable | ID del objeto afectado |
| `detalle` | VARCHAR(500) | nullable | Descripción legible de la acción |
| `ip` | VARCHAR(45) | nullable | IP del cliente (IPv4 o IPv6) |
| `resultado` | VARCHAR(10) | default: `'ok'` | `'ok'` o `'error'` |

**Acciones registradas:**

| Código | Cuándo se genera |
|--------|-----------------|
| `LOGIN` | Login de usuario en el sistema de usuarios |
| `ESCANEAR` | Subida y procesado de documento OCR |
| `EDITAR_DOC` | Modificación de campos de un documento |
| `BORRAR_DOC` | Eliminación de un documento |
| `NETEAR` | Asociación factura ↔ albarán |
| `DESNETEAR` | Desasociación de albarán |
| `CREAR_PROV` | Creación de proveedor |
| `EDITAR_PROV` | Modificación de proveedor |
| `BORRAR_PROV` | Eliminación de proveedor |
| `PROV_DOC` | Creación de proveedor desde documento |
| `REPORTE` | Generación de informe Excel |
| `VER_ALERTAS` | Consulta de alertas sin netear |

---

## sistema_usuarios.db

Gestionada por `sistema_usuarios/models.py` con SQLAlchemy puro (sin Flask).  
Ubicación: `sistema_usuarios/sistema_usuarios.db`.

### Diagrama de relaciones

```
┌──────────┐         ┌──────────────────┐         ┌──────────────────┐
│  roles   │         │      users       │         │ user_permissions │
│──────────│         │──────────────────│         │──────────────────│
│ id (PK)  │◄────────│ role_id (FK)     │◄────────│ user_id (FK)     │
│ name(UQ) │  N:1    │ id (PK)          │  1:N    │ id (PK)          │
│ descrip. │         │ username (UQ)    │         │ module           │
└──────────┘         │ email (UQ)       │         │ can_access       │
                     │ hashed_password  │         └──────────────────┘
                     │ full_name        │
                     │ is_active        │
                     │ created_at       │
                     │ last_login       │
                     └──────────────────┘
```

---

### Tabla: `roles`

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | INTEGER | PK, autoincrement | Identificador único |
| `name` | STRING | UNIQUE, index | Nombre del rol |
| `description` | STRING | nullable | Descripción del rol |

**Roles predefinidos:**

| ID | Nombre | Descripción |
|----|--------|-------------|
| 1 | `admin` | Acceso total, gestión de usuarios y logs |
| 2 | `supervisor` | Acceso a todos los módulos, sin gestión de usuarios |
| 3 | `basico` | Acceso limitado según permisos asignados |

---

### Tabla: `users`

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | INTEGER | PK, autoincrement | Identificador único |
| `username` | STRING | UNIQUE, index | Nombre de usuario para login |
| `email` | STRING | UNIQUE, index | Correo electrónico |
| `hashed_password` | STRING | NOT NULL | Contraseña cifrada con bcrypt |
| `full_name` | STRING | nullable | Nombre completo para mostrar |
| `role_id` | INTEGER | FK → `roles.id`, default: 3 | Rol asignado |
| `is_active` | BOOLEAN | default: True | Si el usuario puede iniciar sesión |
| `created_at` | DATETIME | default: now | Fecha de creación |
| `last_login` | DATETIME | nullable | Último acceso registrado |

**Relaciones:**
- `role` → N:1 con `Role`
- `permissions` → 1:N con `UserPermission` (cascade delete)

---

### Tabla: `user_permissions`

Permisos granulares por módulo para usuarios con rol `basico` o `supervisor`. Los administradores tienen acceso total sin consultar esta tabla.

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | INTEGER | PK, autoincrement | Identificador único |
| `user_id` | INTEGER | FK → `users.id`, CASCADE DELETE | Usuario al que aplica |
| `module` | STRING | NOT NULL | Módulo del sistema |
| `can_access` | BOOLEAN | default: True | Si tiene acceso al módulo |

**Módulos disponibles:**

| Módulo | Sección de la interfaz |
|--------|----------------------|
| `dashboard` | Panel de KPIs y alertas |
| `escanear` | Subida y procesado de documentos |
| `documentos` | Listado y edición de documentos |
| `neteo` | Asociación factura ↔ albarán |
| `reportes` | Generación de informes Excel |

---

## Migraciones

El sistema no usa Alembic. Las migraciones se hacen con `ALTER TABLE` manual al arrancar, en `backend/app.py`:

```python
with app.app_context():
    db.create_all()  # Crea tablas si no existen
    # Añade columnas nuevas si la BD es antigua
    if 'proveedor_id' not in _cols_doc:
        _conn.execute(text('ALTER TABLE documentos ADD COLUMN proveedor_id INTEGER'))
    if 'proveedor_normalizado' not in _cols_doc:
        _conn.execute(text('ALTER TABLE documentos ADD COLUMN proveedor_normalizado BOOLEAN DEFAULT 0'))
```

> Si se añaden columnas nuevas a los modelos, hay que añadir el `ALTER TABLE` correspondiente en este bloque para que las instalaciones existentes se actualicen sin perder datos.

---

## Ubicación de los ficheros SQLite

| Base de datos | Ruta | Servicio |
|---------------|------|---------|
| `sistema_facturas.db` | Raíz del proyecto | `backend/app.py` |
| `sistema_usuarios.db` | `sistema_usuarios/` | `sistema_usuarios/main.py` |

Ambos ficheros están en `.gitignore` y no se versionan.
