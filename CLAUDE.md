# CLAUDE.md — Instrucciones del proyecto para Claude Code

## Qué es este proyecto
Programa de caja chica para una gomería que también controla sueldos y adelantos de empleados. Reemplaza el control que se hacía en Excel.

**Antes de tomar decisiones de diseño, leer `plan_caja_chica.md`** (raíz del proyecto) — ahí está el contexto del negocio, el modelo de datos y las decisiones de arquitectura ya confirmadas con el usuario (Fase 1).

## Privacidad (repo público)
El repositorio de este proyecto es **público** (por ahora — se evaluará pasar a privado cuando se agreguen más módulos con datos de empleados). Por eso:
- **Nunca usar nombres reales de personas** en código, comentarios, datos de ejemplo/semilla (seed data), fixtures de tests, ni mensajes de commit. Usar nombres genéricos (ej. "Empleado A", "Cliente 1") o inventados.
- El archivo real de base de datos (con los movimientos y montos reales de la empresa) **nunca se commitea** — debe estar en `.gitignore`, sin excepción, sea el repo público o privado.
- Si en algún momento se necesita un dato de ejemplo realista para mostrar cómo funciona algo, inventarlo (montos y conceptos ficticios), nunca copiar un dato real de la empresa.

## Memoria entre sesiones (importante)
Este proyecto se trabaja en sesiones separadas de Claude Code, que no tienen memoria entre sí. Para mantener continuidad:

- **Al EMPEZAR una sesión**: leer las últimas 1-2 entradas de `HISTORIAL_SESIONES.md` para saber en qué quedó la sesión anterior y qué queda pendiente.
- **Al TERMINAR una sesión** (cuando el usuario avise que va a cerrar, o al cerrar una tarea grande): agregar una entrada nueva al final de `HISTORIAL_SESIONES.md` con fecha, qué se hizo, qué se decidió, y qué queda pendiente. **No reescribir ni borrar entradas anteriores**, solo agregar.

## Buenas prácticas de código
- Python, seguir PEP8.
- Mantener nombres de variables/funciones consistentes (en español, ya que así está pensado el dominio: `movimiento`, `categoria`, `saldo_caja`, etc.).
- Separar la lógica de negocio (cálculo de saldo, validaciones, totales) de las rutas/endpoints web — que las rutas sean lo más finitas posible y deleguen el cálculo a funciones aparte, fáciles de testear.
- Comentar el *por qué* de decisiones no obvias, no el *qué* (el código ya dice el qué).
- Commits chicos y descriptivos en git (ver sección de Git más abajo).
- No hardcodear valores que deberían ser configurables (ej. lista de categorías, métodos de pago) — mantenerlos en la base de datos o en un archivo de configuración, no en el código.

## Tests
- Usar `pytest`.
- Toda función de cálculo (saldo de caja en efectivo, totales por categoría, totales por método de pago, etc.) debe tener al menos un test.
- Ubicación: carpeta `tests/`, un archivo de test por módulo (ej. `tests/test_movimientos.py`, `tests/test_saldo.py`).
- Antes de dar una tarea por terminada, correr `pytest` y confirmar que todos los tests pasan. Si algo falla, arreglarlo antes de seguir.

## Git
- Cuando termines una funcionalidad que ya funciona y tiene sus tests pasando:
  1. Correr `pytest` y confirmar que todo pasa.
  2. `git add` de los archivos relacionados.
  3. `git commit` con un mensaje claro (ej. `git commit -m "Agregar cálculo de saldo de caja en efectivo"`).
  4. `git push` a `origin main`.
- Hacer esto **sin pedir confirmación en el chat** — los permisos ya están configurados en `.claude/settings.json` para correr estos comandos sin interrupciones.
- Nunca usar `git push --force` ni `git reset --hard` — quedan bloqueados a propósito en `.claude/settings.json`.
- Nunca commitear el archivo de base de datos con datos reales (sueldos, adelantos) — debe estar en `.gitignore`.
- Si el cambio es grande o podría romper algo que ya funcionaba, preguntar antes de hacer commit/push, aunque el resto sea automático.

## Estructura del proyecto

```
caja_chica/
├── run.py                        # Punto de entrada: arranca Flask y abre el navegador
├── requirements.txt
├── .gitignore
├── plan_caja_chica.md            # Contexto de negocio y decisiones de arquitectura
├── CLAUDE.md                     # Este archivo
├── HISTORIAL_SESIONES.md         # Bitácora de sesiones
│
├── app/                          # Paquete Flask
│   ├── __init__.py               # Factory: create_app()
│   ├── db.py                     # Conexión SQLite + init_db()
│   ├── schema.sql                # DDL + seed de categorías
│   ├── models/
│   │   └── movimientos.py        # Lógica de negocio (saldo, totales, queries)
│   ├── routes/
│   │   └── movimientos.py        # Rutas Flask (/, /movimiento/nuevo)
│   ├── static/
│   │   ├── css/style.css
│   │   ├── js/main.js
│   │   └── img/logo.png          # Logo de la empresa (no generado, copiar manualmente)
│   └── templates/
│       ├── base.html
│       └── movimientos/
│           └── cargar.html       # Pantalla principal: saldo + formulario + tabla del día
│
├── tests/
│   └── test_movimientos.py       # Tests de lógica de negocio (pytest)
│
├── instance/                     # Creada automáticamente, NO se commitea
│   └── caja_chica.db             # Base de datos SQLite real
│
└── venv/                         # Entorno virtual, NO se commitea
```

## Cómo correr el proyecto localmente
Ver `README.md`.
