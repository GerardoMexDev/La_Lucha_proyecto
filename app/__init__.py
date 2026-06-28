import os
from flask import Flask
from . import db as db_module


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY='caja-chica-la-lucha-local',
        DATABASE=os.path.join(app.instance_path, 'caja_chica.db'),
    )

    if test_config is not None:
        app.config.from_mapping(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    db_module.init_app(app)

    from .routes import movimientos as movimientos_routes
    app.register_blueprint(movimientos_routes.bp)

    @app.template_filter('formato_monto')
    def formato_monto(valor):
        """Formatea montos con punto de miles (estilo UY): 45000 → 45.000"""
        try:
            return "{:,.0f}".format(abs(float(valor or 0))).replace(',', '.')
        except (ValueError, TypeError):
            return '0'

    @app.template_filter('formato_fecha')
    def formato_fecha(valor):
        """Convierte 'YYYY-MM-DD' a 'DD/MM/YYYY'."""
        try:
            from datetime import datetime
            return datetime.strptime(str(valor), '%Y-%m-%d').strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            return str(valor)

    return app
