# Historial de sesiones

> Este archivo lo actualiza Claude Code al final de cada sesión de trabajo, y lo lee al principio de la siguiente (instrucción en `CLAUDE.md`). No se borran entradas anteriores — solo se agregan nuevas abajo de todo, en orden cronológico.

## Formato de cada entrada

```
## [AAAA-MM-DD] Resumen corto de la sesión
**Hecho:** qué se construyó o cambió.
**Decisiones:** qué se decidió y por qué (si hubo algo a definir).
**Pendiente para la próxima sesión:** qué sigue.
```

---

## [Sin iniciar] Estado del proyecto

Todavía no arrancó la codificación. La planeación completa de la Fase 1 (modelo de datos, pantallas, stack técnico) está en `plan_caja_chica.md`. Las buenas prácticas y reglas del proyecto están en `CLAUDE.md`.

**Pendiente para la próxima sesión:** armar la estructura inicial del proyecto (carpetas, entorno virtual, base de datos SQLite, primera pantalla de carga de movimientos).

---

## [2026-06-27] Estructura inicial del proyecto + primera pantalla

**Hecho:**
- Entorno virtual Python 3.14 creado en `venv/` (no se commitea).
- `requirements.txt` con Flask y pytest.
- Base de datos SQLite con esquema completo: tablas `movimientos` y `categorias` con las 11 categorías iniciales del plan; se crea sola en `instance/caja_chica.db` al correr `run.py`.
- App Flask con patrón factory (`app/__init__.py`), conexión a DB (`app/db.py`), lógica de negocio (`app/models/movimientos.py`), rutas (`app/routes/movimientos.py`).
- Primera pantalla (`/`): tarjetas de saldo en efectivo UYU y USD, formulario de carga de movimientos, tabla del día con totales por método de pago. Filtrado automático de categorías por tipo (ingreso/egreso) via JS.
- `run.py`: arranca el servidor y abre el navegador automáticamente.
- Logo de la empresa en `app/static/img/logo.png` (pendiente: el usuario debe copiar el archivo).
- 11 tests en `tests/test_movimientos.py` — todos pasan.

**Decisiones:**
- El saldo en efectivo se calcula solo con movimientos en Efectivo (Tarjeta/Transferencia/Cheque son informativos), tal como dice el plan.
- UYU y USD son cajas independientes, nunca se mezclan.

**Pendiente para la próxima sesión:**
- El usuario debe copiar `logo.png` a `app/static/img/logo.png` para que aparezca en el header.
- Siguiente funcionalidad a construir: editar/borrar movimientos + reporte diario (Pantallas 2 y 3 del plan).

---

## [2026-06-27] Categorías, tema oscuro, edición/borrado y reporte de adelantos

**Hecho:**
- Categorías: "Ventas y trabajos" separada en **"Ventas"** (cubiertas) y **"Servicios de taller"** (taller). Agregada **"Adelanto de sueldo"** (egreso).
- Tema oscuro (fondo negro) como predeterminado, con switch en el header para alternar entre claro y oscuro. La preferencia se guarda en localStorage sin flash al cargar.
- Logo colocado por el usuario en `app/static/img/logo_la_lucha.jpeg`.
- **Editar y borrar movimientos**: botones en cada fila de la tabla. Editar abre un modal con los campos pre-cargados; borrar pide confirmación. Corregido bug donde el modal no cerraba (`display:flex` sobreescribía el atributo `hidden` — solucionado con `[hidden] { display: none !important }`).
- **Reporte de adelantos** (`/reporte/adelantos`): agrupa los adelantos de sueldo por semana con corte los sábados, muestra totales UYU y USD por semana, marca la semana en curso. Accesible desde el nav del header.
- 20 tests, todos pasan.

**Decisiones:**
- La semana del reporte de adelantos cierra el sábado (día del corte del negocio). El lunes de cada semana se calcula como sábado − 5 días.
- El filtro de categorías por tipo (ingreso/egreso) funciona tanto en el formulario principal como en el modal de edición.

**Pendiente para la próxima sesión:**
- Reporte diario completo (Pantalla 3 del plan): elegir fecha, ver movimientos + saldo de efectivo + totales por método de pago en una vista de impresión/exportación.
- Reporte semanal / por rango de fechas (Pantalla 4).
- Filtros básicos por categoría, método de pago y moneda (Pantalla 5).
