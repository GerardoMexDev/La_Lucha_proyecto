import sqlite3
import os
from flask import g, current_app


def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE']
        if db_path != ':memory:':
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        g.db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Crea las tablas si no existen y carga las categorías iniciales."""
    db = get_db()
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    with open(schema_path, encoding='utf-8') as f:
        db.executescript(f.read())


def init_app(app):
    app.teardown_appcontext(close_db)
