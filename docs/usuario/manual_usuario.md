# Manual de Usuario

**Sistema de Gestión de Facturas y Albaranes**  
Versión 1.2 · Soporte: raul.castro@esenex.es

---

## ¿Qué hace este sistema?

El sistema te permite gestionar facturas y albaranes de forma digital y automatizada:

- **Sube** tus documentos en PDF o imagen y el sistema lee los datos automáticamente (OCR)
- **Asocia** cada factura con sus albaranes correspondientes (neteo)
- **Controla** qué facturas llevan tiempo sin albarán asociado gracias a las alertas
- **Genera** informes Excel profesionales para contabilidad y análisis
- **Gestiona** el catálogo de proveedores de forma centralizada

---

## Acceso al sistema

Abre el navegador y ve a `http://localhost:5000`.

Introduce tu **usuario** y **contraseña** en la pantalla de login. Si es la primera vez, solicita las credenciales al administrador.

> El sistema tiene un tiempo de sesión de **8 horas**. Al cabo de ese tiempo tendrás que volver a iniciar sesión.

### Roles de usuario

| Rol | Qué puede hacer |
|-----|----------------|
| **Administrador** | Acceso total: todos los módulos, gestión de usuarios y logs de actividad |
| **Supervisor** | Todos los módulos excepto gestión de usuarios y logs |
| **Básico** | Solo los módulos que el administrador haya habilitado para su cuenta |

Si al entrar no ves alguna sección del menú, es porque no tienes permiso para ese módulo. Contacta con el administrador.

---

## Navegación

La barra lateral izquierda contiene el menú principal:

| Icono | Sección | Para qué sirve |
|-------|---------|----------------|
| 📊 | **Dashboard** | Vista general con totales e importes |
| 📤 | **Escanear** | Subir documentos nuevos |
| 📋 | **Documentos** | Ver y editar todos los documentos |
| 🔗 | **Neteo** | Asociar facturas con albaranes |
| 📥 | **Reportes Excel** | Generar y descargar informes |
| 🏢 | **Proveedores** | Gestionar el catálogo de proveedores |
| 📜 | **Logs de Actividad** | Auditoría de acciones *(solo admin)* |

En la parte inferior del menú puedes cambiar el **color de fondo** de la interfaz (Blanco, Gris, Azul hielo, Arena, Negro) y **cerrar sesión**.

---

## 📊 Dashboard

Es la pantalla principal. Se actualiza automáticamente cada vez que entras.

### Indicadores (KPIs)

En la parte superior verás cuatro tarjetas:

- **Total Documentos** — Cuántos documentos hay en el sistema
- **Facturas** — Número de facturas e importe total acumulado
- **Albaranes** — Número de albaranes e importe total acumulado
- **Neteados** — Facturas que ya tienen albarán asociado

### Panel de alertas

Si hay facturas pendientes de netear, aparece un aviso con código de color:

| Color | Significado |
|-------|-------------|
| 🟡 Amarillo | Facturas con menos de 15 días pendientes |
| 🟠 Naranja | Facturas entre 15 y 29 días sin asociar |
| 🔴 Rojo | Facturas con 30 o más días sin albarán — **acción urgente** |

El panel también muestra el **importe total en espera** de ser neteado.

### Badge en el menú

La sección **Neteo** del menú lateral muestra un badge numérico con el total de facturas pendientes. El color del badge sigue el mismo código (amarillo / naranja / rojo).

---

## 📤 Escanear — Subir documentos

Esta es la sección donde entran los documentos al sistema.

### Cómo subir un documento

1. Haz clic en **Escanear** en el menú lateral
2. Arrastra el fichero al área punteada, o haz clic en ella para abrir el explorador de archivos
3. El sistema procesa el documento automáticamente con OCR
4. Verás el resultado en pantalla: los campos extraídos (número, fecha, proveedor, CIF, importes)

**Formatos aceptados:** PDF, PNG, JPG, JPEG, TIFF, BMP  
**Tamaño máximo:** 32 MB por fichero

> Puedes subir **varios ficheros a la vez** arrastrándolos todos juntos al área de subida.

### Qué extrae el OCR automáticamente

- Tipo de documento (factura o albarán)
- Número de documento
- Fecha
- Nombre del proveedor
- CIF/NIF del proveedor
- Base imponible, IVA y total
- Líneas de detalle (artículos/servicios) cuando el formato lo permite

### Neteo automático tras la subida

Después de procesar cada documento, el sistema intenta asociarlo automáticamente:

1. Si es una **factura** y menciona un número de albarán que ya existe en el sistema → se asocian al instante
2. Si no, busca albaranes del mismo proveedor con fecha en un margen de ±30 días

Si no encuentra coincidencia, el documento queda como **Pendiente de neteo** y aparecerá en la sección Neteo para asociarlo manualmente.

### Posibles resultados tras la subida

| Resultado | Qué significa |
|-----------|--------------|
| ✅ Procesado | OCR completado, datos extraídos correctamente |
| ✅ Procesado + neteado | Procesado y ya asociado con su albarán/factura |
| ❌ Error de validación | El fichero no parece una factura ni un albarán |
| ❌ Error OCR | No se pudo extraer texto (fichero vacío, protegido o ilegible) |

> **Si el OCR extrae datos incorrectos**, no pasa nada. Puedes corregirlos manualmente en la sección Documentos.

---

## 📋 Documentos — Listado y edición

Muestra todos los documentos del sistema con sus datos y estado.

### Filtros disponibles

- **Tipo:** Todos / Facturas / Albaranes
- **Estado:** Todos / Procesado / Pendiente / Error / Asociado
- **Búsqueda:** Por número de documento, nombre de proveedor o CIF

### Editar un documento

Si el OCR extrajo algún dato incorrecto:

1. Haz clic en el documento para abrirlo
2. Modifica los campos que necesites (número, fecha, proveedor, CIF, importes)
3. Guarda los cambios

### Eliminar un documento

Haz clic en el icono de papelera junto al documento.

> Si eliminas una **factura** que tenía albaranes asociados, los albaranes se desvinculan automáticamente (no se eliminan).

---

## 🔗 Neteo — Asociar facturas con albaranes

El neteo es el proceso de vincular una factura con el albarán o albaranes que la originaron. Es necesario para cuadrar la contabilidad.

### Pantalla de neteo

La pantalla se divide en dos columnas:

- **Izquierda:** Facturas sin albarán asociado
- **Derecha:** Albaranes sin factura

### Cómo netear manualmente

1. Haz clic en una **factura** de la columna izquierda para seleccionarla
2. Se resaltan automáticamente los albaranes del mismo proveedor a la derecha
3. Haz clic en uno o varios **albaranes** de la columna derecha
4. Pulsa el botón **Asociar**

La factura desaparece de la lista (queda neteada) y los albaranes pasan a estado *Asociado*.

### Deshacer una asociación

Desde la sección **Documentos**, abre la factura asociada y haz clic en **Desasociar** junto al albarán que quieras desvincular.

---

## 📥 Reportes Excel

Genera informes profesionales listos para descargar y compartir.

### Tipos de informe

**Reporte estándar**
Incluye: portada ejecutiva con KPIs, listado completo de documentos (base, IVA, total), resumen comparativo facturas vs albaranes, y tabla de neteo con el estado de cada asociación.

**Informe contable**
Agrupado por proveedor. Incluye subtotales de base imponible, IVA y total por cada proveedor. Ideal para contabilidad y conciliación bancaria. Permite filtrar por proveedor específico.

**Análisis de compras (CPP)**
Análisis de Coste Por Producto a partir de las líneas de detalle extraídas por OCR. Solo se incluyen documentos con líneas de detalle identificadas. Útil para control de costes por artículo.

### Cómo generar un informe

1. Ve a **Reportes Excel** en el menú
2. Selecciona el tipo de informe
3. Opcionalmente filtra por **fecha desde** y **fecha hasta** (y proveedor para el contable)
4. Haz clic en **Descargar**
5. El fichero `.xlsx` se descarga directamente en tu equipo

> Si no seleccionas fechas, el informe incluirá **todos los documentos** del sistema.

---

## 🏢 Proveedores

Catálogo centralizado de todos los proveedores. Permite unificar documentos del mismo proveedor aunque el OCR haya extraído el nombre con pequeñas variaciones.

### Crear un proveedor

1. Ve a **Proveedores** en el menú
2. Haz clic en **+ Nuevo Proveedor**
3. Rellena los datos (solo el nombre es obligatorio)
4. Guarda

### Crear proveedor desde un documento

Si tienes un documento ya procesado y quieres crear el proveedor a partir de sus datos:

1. Abre el documento en la sección Documentos
2. Haz clic en **Crear proveedor desde este documento**
3. El sistema crea el proveedor con el nombre y CIF del documento, y lo asocia automáticamente a todos los documentos que coincidan por CIF o nombre similar (similitud ≥ 80%)

### Editar y desactivar proveedores

Desde el listado de proveedores puedes editar los datos de contacto (email, teléfono, dirección, notas) y marcar un proveedor como **inactivo** si ya no trabajas con él.

> Un proveedor con documentos asociados **no se puede eliminar** directamente. Primero debes desvincular sus documentos.

---

## 📜 Logs de Actividad *(solo administradores)*

Registro completo de todas las acciones realizadas en el sistema: quién hizo qué y cuándo.

### Filtros disponibles

- Por **usuario**
- Por **tipo de acción** (escanear, editar, netear, reportes, etc.)
- Por **resultado** (correcto / error)
- Por **rango de fechas**

### Limpiar logs antiguos

Haz clic en **Limpiar logs...** e indica la fecha límite. Se eliminarán todos los registros anteriores a esa fecha.

---

## Preguntas frecuentes

**El OCR no ha extraído bien los datos, ¿qué hago?**  
Ve a la sección Documentos, abre el documento y edita los campos manualmente. No es necesario subir el documento de nuevo.

**He subido un documento y aparece como Error, ¿por qué?**  
El sistema valida que el documento sea una factura o albarán real. Si el fichero está vacío, protegido por contraseña, es una imagen de muy baja calidad, o no contiene los elementos mínimos (palabra clave, importe o número de documento), se rechaza.

**¿Puedo subir el mismo documento dos veces?**  
Sí, el sistema no detecta duplicados automáticamente. Si subes el mismo documento dos veces aparecerán dos registros. Elimina el duplicado desde la sección Documentos.

**¿Por qué no veo la sección de Logs en el menú?**  
Los Logs de Actividad solo son visibles para usuarios con rol Administrador.

**¿Dónde se guardan los ficheros Excel generados?**  
Los informes se descargan directamente en tu equipo. El sistema también los guarda temporalmente en la carpeta `reports/` del servidor.

**El sistema no responde o aparece "Error de conexión"**  
El backend no está arrancado. Pide al administrador que ejecute `python start.py` en el servidor.

---

## Soporte

Para cualquier incidencia o consulta: **raul.castro@esenex.es**
