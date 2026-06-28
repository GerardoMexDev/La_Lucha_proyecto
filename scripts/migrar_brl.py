#!/usr/bin/env python3
"""
Migración puntual: agrega soporte para BRL como moneda válida.

SQLite no permite modificar CHECK constraints con ALTER TABLE, así que
se recrea la tabla movimientos con la constraint actualizada.

Uso:  python scripts/migrar_brl.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "instance" / "caja_chica.db"


def migrar():
    if not DB_PATH.exists():
        print(f"ERROR: No se encontró la base de datos: {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cur  = conn.cursor()

    # Verificar si ya está migrada
    cur.execute("PRAGMA table_info(movimientos)")
    # Leer el SQL actual de la tabla
    row = cur.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='movimientos'"
    ).fetchone()

    if row and 'BRL' in row[0]:
        print("La base de datos ya soporta BRL. No se requiere migración.")
        conn.close()
        return

    print("Aplicando migración: agregando BRL a la tabla movimientos...")

    cur.executescript("""
        BEGIN;

        CREATE TABLE movimientos_new (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha         TEXT    NOT NULL,
            tipo          TEXT    NOT NULL CHECK(tipo IN ('ingreso', 'egreso')),
            moneda        TEXT    NOT NULL CHECK(moneda IN ('UYU', 'USD', 'BRL')),
            monto         REAL    NOT NULL CHECK(monto > 0),
            concepto      TEXT    NOT NULL,
            categoria_id  INTEGER REFERENCES categorias(id),
            metodo_pago   TEXT    NOT NULL CHECK(metodo_pago IN ('Efectivo', 'Tarjeta', 'Transferencia', 'Cheque')),
            observaciones TEXT,
            creado_en     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        INSERT INTO movimientos_new SELECT * FROM movimientos;

        DROP TABLE movimientos;

        ALTER TABLE movimientos_new RENAME TO movimientos;

        COMMIT;
    """)

    conn.close()
    print("Migración completada correctamente.")


if __name__ == "__main__":
    migrar()
