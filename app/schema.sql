CREATE TABLE IF NOT EXISTS categorias (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    tipo   TEXT NOT NULL CHECK(tipo IN ('ingreso', 'egreso', 'ambos'))
);

CREATE TABLE IF NOT EXISTS movimientos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha        TEXT    NOT NULL,
    tipo         TEXT    NOT NULL CHECK(tipo IN ('ingreso', 'egreso')),
    moneda       TEXT    NOT NULL CHECK(moneda IN ('UYU', 'USD')),
    monto        REAL    NOT NULL CHECK(monto > 0),
    concepto     TEXT    NOT NULL,
    categoria_id INTEGER REFERENCES categorias(id),
    metodo_pago  TEXT    NOT NULL CHECK(metodo_pago IN ('Efectivo', 'Tarjeta', 'Transferencia', 'Cheque')),
    observaciones TEXT,
    creado_en    TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Categorías iniciales (INSERT OR IGNORE = no falla si ya existen)
INSERT OR IGNORE INTO categorias (nombre, tipo) VALUES
    ('Ventas y trabajos',       'ingreso'),
    ('Otros ingresos',          'ingreso'),
    ('Sueldos y adelantos',     'egreso'),
    ('Viáticos',                'egreso'),
    ('Insumos y suministros',   'egreso'),
    ('Combustible',             'egreso'),
    ('Papelería / administrativo', 'egreso'),
    ('Alquiler local',          'egreso'),
    ('Envíos',                  'egreso'),
    ('Retiros',                 'egreso'),
    ('Otros gastos',            'egreso');
