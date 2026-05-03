# Referencia de la API REST

**Base URL:** `http://localhost:5000`  
**Versión:** 1.2  
**Formato:** JSON en todas las respuestas y cuerpos de petición  

---

## Autenticación

Todos los endpoints requieren un token JWT en la cabecera, **excepto** `/api/health`.

```
Authorization: Bearer <token>
```

El token se obtiene haciendo login en el servicio de usuarios (puerto 8000):

```http
POST http://localhost:8000/token
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "role": "admin"
}
```

El token tiene una validez de **8 horas** (jornada laboral completa).

**Errores de autenticación:**

| Código | Descripción |
|--------|-------------|
| `401` | Token ausente, inválido o expirado |
| `403` | Token válido pero sin permisos para la operación |

---

## Códigos de estado comunes

| Código | Significado |
|--------|-------------|
| `200` | OK |
| `201` | Creado correctamente |
| `400` | Petición incorrecta (campo obligatorio faltante, formato inválido) |
| `401` | No autenticado |
| `403` | Sin permisos (solo admin) |
| `404` | Recurso no encontrado |
| `409` | Conflicto (ej. CIF duplicado) |
| `422` | Documento no válido (no es factura ni albarán) |
| `500` | Error interno del servidor |

---

## Documentos

### `POST /api/escanear`

Sube un fichero y lo procesa con OCR, extrayendo automáticamente todos los campos.

**Request:** `multipart/form-data`

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `archivo` | file | Sí | PDF, PNG, JPG, JPEG, TIFF, TIF o BMP. Máximo 32 MB. |

**Respuesta `200`:**
```json
{
  "id": 42,
  "tipo": "factura",
  "numero": "F-2024-0123",
  "fecha": "2024-03-15",
  "proveedor": "Distribuciones García S.L.",
  "cif": "B12345678",
  "base_imponible": 1000.00,
  "iva": 210.00,
  "total": 1210.00,
  "porcentaje_iva": 21.0,
  "estado": "PROCESADO",
  "archivo_original": "factura_garcia.pdf",
  "fecha_subida": "2024-03-20T10:30:00",
  "notas": null,
  "factura_id": null,
  "albaranes_asociados": [],
  "proveedor_id": null,
  "proveedor_normalizado": false,
  "lineas": []
}
```

**Errores:**
- `400` — No se proporcionó archivo o nombre vacío
- `400` — Formato de archivo no soportado
- `422` — El documento no es una factura ni un albarán (no contiene palabras clave, importes o número de documento)
- `500` — Error en el procesamiento OCR

> **Nota:** El sistema intenta neteo automático tras el escaneo. Si el documento menciona un número de albarán existente en la BD, se asocia automáticamente.

---

### `GET /api/documentos`

Lista todos los documentos con paginación y filtros opcionales.

**Query params:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `tipo` | string | `factura` o `albaran` |
| `estado` | string | `PENDIENTE`, `PROCESADO`, `ERROR`, `FACTURA_ASOCIADA` |
| `q` | string | Búsqueda en número, proveedor y CIF |
| `pagina` | int | Página actual (por defecto: `1`) |
| `por_pagina` | int | Resultados por página (por defecto: `50`) |

**Respuesta `200`:**
```json
{
  "documentos": [ /* array de objetos Documento completos */ ],
  "total": 120,
  "pagina": 1,
  "por_pagina": 50,
  "paginas": 3
}
```

---

### `GET /api/documentos/:id`

Obtiene el detalle completo de un documento, incluyendo sus líneas OCR y albaranes asociados.

**Respuesta `200`:** Objeto `Documento` completo (ver esquema en `/api/escanear`).

**Error `404`:** Documento no encontrado.

---

### `PUT /api/documentos/:id`

Actualiza los campos extraídos por OCR de un documento. Útil para corregir errores de reconocimiento.

**Body JSON:**

```json
{
  "tipo": "factura",
  "numero": "F-2024-0123",
  "fecha": "2024-03-15",
  "proveedor": "Distribuciones García S.L.",
  "cif": "B12345678",
  "base_imponible": 1000.00,
  "iva": 210.00,
  "total": 1210.00,
  "notas": "Revisado manualmente"
}
```

Todos los campos son opcionales — solo se actualizan los que se envíen.

**Respuesta `200`:** Objeto `Documento` actualizado.

---

### `DELETE /api/documentos/:id`

Elimina un documento. Si era una factura con albaranes asociados, los desvincula (pasan a estado `PROCESADO`).

**Respuesta `200`:**
```json
{ "mensaje": "Documento eliminado correctamente" }
```

---

## Neteo

El neteo es la asociación entre una factura y uno o varios albaranes del mismo proveedor.

### `POST /api/neteo/asociar`

Asocia manualmente uno o varios albaranes a una factura.

**Body JSON:**
```json
{
  "factura_id": 10,
  "albaran_ids": [23, 24, 25]
}
```

**Respuesta `200`:**
```json
{
  "factura": { /* objeto Documento completo de la factura */ },
  "asociados": 3
}
```

**Errores:**
- `400` — `factura_id` o `albaran_ids` no proporcionados
- `404` — Factura o algún albarán no encontrado

---

### `POST /api/neteo/desasociar/:id`

Desvincula un albarán de su factura. El albarán vuelve a estado `PROCESADO`.

**Respuesta `200`:**
```json
{ "mensaje": "Albarán desasociado correctamente" }
```

---

### `GET /api/neteo/sin-asociar`

Devuelve facturas sin albarán asociado y albaranes sin factura.

**Respuesta `200`:**
```json
{
  "facturas_sin_albaran": [
    {
      "id": 10,
      "tipo": "factura",
      "numero": "F-2024-0123",
      "fecha": "2024-03-15",
      "proveedor": "García S.L.",
      "total": 1210.00,
      "estado": "PROCESADO"
    }
  ],
  "albaranes_sin_factura": [ /* mismo esquema */ ]
}
```

---

## Proveedores

### `GET /api/proveedores`

Lista proveedores con filtros y paginación.

**Query params:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `q` | string | Búsqueda en nombre y CIF |
| `activo` | boolean | `true` o `false` |
| `pagina` | int | Por defecto: `1` |
| `por_pagina` | int | Por defecto: `50` |

**Respuesta `200`:**
```json
{
  "proveedores": [
    {
      "id": 1,
      "nombre": "Distribuciones García S.L.",
      "cif": "B12345678",
      "email": "garcia@ejemplo.com",
      "telefono": "972 000 000",
      "direccion": "Calle Mayor 1, Girona",
      "notas": null,
      "fecha_alta": "2024-01-10T09:00:00",
      "activo": true,
      "num_documentos": 15
    }
  ],
  "total": 8,
  "pagina": 1,
  "paginas": 1
}
```

---

### `POST /api/proveedores`

Crea un nuevo proveedor.

**Body JSON:**
```json
{
  "nombre": "Distribuciones García S.L.",
  "cif": "B12345678",
  "email": "garcia@ejemplo.com",
  "telefono": "972 000 000",
  "direccion": "Calle Mayor 1, Girona",
  "notas": ""
}
```

Solo `nombre` es obligatorio. El CIF debe ser único si se proporciona.

**Respuesta `201`:** Objeto `Proveedor` creado.

**Errores:**
- `400` — `nombre` no proporcionado
- `409` — Ya existe un proveedor con ese CIF

---

### `GET /api/proveedores/:id`

Obtiene el detalle de un proveedor, incluyendo los últimos 20 documentos asociados.

**Respuesta `200`:**
```json
{
  "id": 1,
  "nombre": "Distribuciones García S.L.",
  "cif": "B12345678",
  "email": "garcia@ejemplo.com",
  "telefono": "972 000 000",
  "direccion": "Calle Mayor 1, Girona",
  "notas": null,
  "fecha_alta": "2024-01-10T09:00:00",
  "activo": true,
  "num_documentos": 15,
  "ultimos_documentos": [ /* array de Documento simple */ ]
}
```

---

### `PUT /api/proveedores/:id`

Actualiza datos de un proveedor. Todos los campos son opcionales.

**Body JSON:** mismos campos que `POST /api/proveedores`.

**Respuesta `200`:** Objeto `Proveedor` actualizado.

---

### `DELETE /api/proveedores/:id`

Elimina un proveedor. Solo es posible si no tiene documentos asociados.

**Respuesta `200`:**
```json
{ "mensaje": "Proveedor eliminado" }
```

**Error `409`:** El proveedor tiene documentos asociados. Desvincula los documentos primero.

---

### `POST /api/proveedores/desde-documento/:doc_id`

Crea o reutiliza un proveedor a partir de los datos extraídos de un documento ya procesado. Asocia automáticamente todos los documentos de la BD que coincidan por CIF exacto o nombre similar (similitud ≥ 80%).

**Respuesta `200`:**
```json
{
  "proveedor": { /* objeto Proveedor */ },
  "documentos_asociados": 7
}
```

**Error `409`:** El documento ya tiene proveedor asignado.

---

## Reportes

Todos los endpoints de reportes devuelven un fichero `.xlsx` como descarga directa.

### `POST /api/reportes/generar`

Genera el reporte Excel estándar: portada con KPIs, listado de documentos y tabla de neteo.

**Body JSON (todos opcionales):**
```json
{
  "fecha_desde": "2024-01-01",
  "fecha_hasta": "2024-12-31"
}
```

**Respuesta:** Fichero `reporte_YYYYMMDD_HHMMSS.xlsx`

---

### `POST /api/reportes/contable`

Genera el informe contable agrupado por proveedor con subtotales de base imponible, IVA y total.

**Body JSON (todos opcionales):**
```json
{
  "fecha_desde": "2024-01-01",
  "fecha_hasta": "2024-12-31",
  "proveedor_id": 1
}
```

**Respuesta:** Fichero `informe_contable_YYYY-MM-DD.xlsx`

---

### `POST /api/reportes/analitico`

Genera el análisis de Coste Por Producto (CPP) usando las líneas de detalle extraídas por OCR. Solo incluye documentos que tengan líneas de detalle.

**Body JSON (todos opcionales):**
```json
{
  "fecha_desde": "2024-01-01",
  "fecha_hasta": "2024-12-31",
  "proveedor_id": 1
}
```

**Respuesta:** Fichero `analitico_YYYYMMDD_HHMMSS.xlsx`

**Error `404`:** No hay documentos con líneas de detalle para los filtros seleccionados.

---

## Alertas

### `GET /api/alertas/sin-netear`

Devuelve un resumen de facturas pendientes de neteo, clasificadas por urgencia según antigüedad.

**Criterios de urgencia:**
- `normal` — menos de 15 días pendiente
- `aviso` — entre 15 y 29 días pendiente
- `critico` — 30 días o más pendiente

**Respuesta `200`:**
```json
{
  "total": 5,
  "criticos": 1,
  "avisos": 2,
  "normales": 2,
  "importe_pendiente": 6050.00,
  "documentos": [
    {
      "id": 10,
      "numero": "F-2024-0100",
      "proveedor": "García S.L.",
      "fecha": "2024-01-15",
      "total": 1210.00,
      "dias_pendiente": 45,
      "urgencia": "critico"
    }
  ]
}
```

> Los `documentos` devueltos son los 10 más antiguos, ordenados por `dias_pendiente` descendente.

---

## Logs de auditoría

> Estos endpoints son **exclusivos para administradores**. Devuelven `403` para otros roles.

### `GET /api/logs`

Lista el registro de actividad con filtros.

**Query params:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `usuario` | string | Filtrar por nombre de usuario |
| `accion` | string | `LOGIN`, `ESCANEAR`, `EDITAR_DOC`, `BORRAR_DOC`, `NETEAR`, `DESNETEAR`, `CREAR_PROV`, `EDITAR_PROV`, `BORRAR_PROV`, `PROV_DOC`, `REPORTE`, `VER_ALERTAS` |
| `resultado` | string | `ok` o `error` |
| `fecha_desde` | date | Fecha inicio `YYYY-MM-DD` |
| `fecha_hasta` | date | Fecha fin `YYYY-MM-DD` |
| `pagina` | int | Por defecto: `1` |
| `por_pagina` | int | Por defecto: `50`. Máximo: `200` |

**Respuesta `200`:**
```json
{
  "logs": [
    {
      "id": 500,
      "timestamp": "2024-03-20T10:30:00",
      "usuario": "admin",
      "accion": "ESCANEAR",
      "entidad": "documento",
      "entidad_id": 42,
      "detalle": "factura F-2024-0123",
      "ip": "127.0.0.1",
      "resultado": "ok"
    }
  ],
  "total": 500,
  "pagina": 1,
  "paginas": 10
}
```

---

### `DELETE /api/logs`

Purga logs anteriores a N días. Solo administradores.

**Query param:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `dias` | int | Elimina logs con más de N días de antigüedad |

**Ejemplo:**
```
DELETE /api/logs?dias=90
```

**Respuesta `200`:**
```json
{ "mensaje": "Logs eliminados: 120 registros" }
```

---

### `GET /api/documentos/:id/archivo`

Descarga el fichero original del documento (PDF o imagen) tal como fue subido.

**Respuesta `200`:** El fichero binario con el `Content-Type` correspondiente (`application/pdf`, `image/png`, etc.) y cabecera `Content-Disposition: attachment`.

**Error `404`:** Documento no encontrado o fichero eliminado del servidor.

---

### `POST /api/logs/evento`

Endpoint interno para registrar un evento de log desde el frontend o servicios externos. Solo administradores.

**Body JSON:**
```json
{
  "accion": "LOGIN",
  "entidad": "usuario",
  "entidad_id": 1,
  "detalle": "Login correcto desde interfaz web",
  "resultado": "ok"
}
```

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `accion` | string | Sí | Código de acción (ver tabla de acciones en `modelos_bd.md`) |
| `entidad` | string | No | Tipo de objeto afectado |
| `entidad_id` | int | No | ID del objeto afectado |
| `detalle` | string | No | Descripción legible |
| `resultado` | string | No | `ok` (por defecto) o `error` |

**Respuesta `200`:**
```json
{ "ok": true }
```

---

## Estadísticas

### `GET /api/estadisticas`

Devuelve los KPIs generales del sistema para el dashboard.

**Respuesta `200`:**
```json
{
  "total_documentos": 120,
  "facturas": 60,
  "albaranes": 60,
  "procesados": 110,
  "pendientes": 5,
  "errores": 5,
  "neteados": 45,
  "importe_facturas": 75000.00,
  "importe_albaranes": 68000.00,
  "importe_total": 143000.00
}
```

---

## Salud del sistema

### `GET /api/health`

Endpoint público (no requiere autenticación). Útil para verificar que el backend está activo.

**Respuesta `200`:**
```json
{
  "status": "ok",
  "timestamp": "2024-03-20T10:30:00.000000"
}
```

---

## Esquemas de objetos

### Documento (completo)

```json
{
  "id": 42,
  "tipo": "factura",
  "numero": "F-2024-0123",
  "fecha": "2024-03-15",
  "proveedor": "Distribuciones García S.L.",
  "cif": "B12345678",
  "base_imponible": 1000.00,
  "iva": 210.00,
  "total": 1210.00,
  "porcentaje_iva": 21.0,
  "estado": "PROCESADO",
  "archivo_original": "factura_garcia.pdf",
  "fecha_subida": "2024-03-20T10:30:00",
  "notas": null,
  "factura_id": null,
  "albaranes_asociados": [],
  "proveedor_id": 1,
  "proveedor_normalizado": true,
  "lineas": [
    {
      "id": 1,
      "documento_id": 42,
      "descripcion": "Aceite de oliva virgen extra 5L",
      "cantidad": 10.0,
      "unidad": "ud",
      "precio_unitario": 12.50,
      "importe_linea": 125.00,
      "orden": 1
    }
  ]
}
```

### Documento (simple — usado en listados de neteo)

```json
{
  "id": 42,
  "tipo": "factura",
  "numero": "F-2024-0123",
  "fecha": "2024-03-15",
  "proveedor": "García S.L.",
  "total": 1210.00,
  "estado": "PROCESADO"
}
```

### Estados del documento

| Estado | Descripción |
|--------|-------------|
| `PENDIENTE` | Recién subido, esperando procesamiento OCR |
| `PROCESADO` | OCR completado, campos extraídos |
| `ERROR` | Falló el OCR o la validación del documento |
| `FACTURA_ASOCIADA` | Albarán que ya tiene factura asignada |
