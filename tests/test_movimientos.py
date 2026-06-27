import pytest
from app import create_app
from app.db import init_db
from app.models.movimientos import (
    calcular_saldo_efectivo,
    agregar_movimiento,
    obtener_movimientos_del_dia,
)

FECHA_TEST = '2024-01-15'


@pytest.fixture
def app():
    """App de prueba con base de datos en memoria."""
    test_app = create_app({'TESTING': True, 'DATABASE': ':memory:'})
    with test_app.app_context():
        init_db()
        yield test_app


# ── Saldo de caja en efectivo ──────────────────────────────────────────────────

def test_saldo_inicial_es_cero(app):
    assert calcular_saldo_efectivo('UYU') == 0.0
    assert calcular_saldo_efectivo('USD') == 0.0


def test_ingreso_efectivo_aumenta_saldo(app):
    agregar_movimiento(FECHA_TEST, 'ingreso', 'UYU', 1000, 'Venta', None, 'Efectivo', None)
    assert calcular_saldo_efectivo('UYU') == 1000.0


def test_egreso_efectivo_reduce_saldo(app):
    agregar_movimiento(FECHA_TEST, 'ingreso', 'UYU', 1000, 'Venta', None, 'Efectivo', None)
    agregar_movimiento(FECHA_TEST, 'egreso',  'UYU', 300,  'Gasto', None, 'Efectivo', None)
    assert calcular_saldo_efectivo('UYU') == 700.0


def test_varios_movimientos_acumulan_correctamente(app):
    agregar_movimiento(FECHA_TEST, 'ingreso', 'UYU', 5000, 'Venta A', None, 'Efectivo', None)
    agregar_movimiento(FECHA_TEST, 'ingreso', 'UYU', 3000, 'Venta B', None, 'Efectivo', None)
    agregar_movimiento(FECHA_TEST, 'egreso',  'UYU', 1500, 'Gasto',   None, 'Efectivo', None)
    assert calcular_saldo_efectivo('UYU') == 6500.0


# ── Tarjeta/Transferencia/Cheque no afectan el saldo de efectivo ───────────────

def test_tarjeta_no_afecta_saldo_efectivo(app):
    agregar_movimiento(FECHA_TEST, 'ingreso', 'UYU', 2000, 'Venta con tarjeta', None, 'Tarjeta', None)
    assert calcular_saldo_efectivo('UYU') == 0.0


def test_transferencia_no_afecta_saldo_efectivo(app):
    agregar_movimiento(FECHA_TEST, 'ingreso', 'UYU', 2000, 'Transferencia recibida', None, 'Transferencia', None)
    assert calcular_saldo_efectivo('UYU') == 0.0


def test_cheque_no_afecta_saldo_efectivo(app):
    agregar_movimiento(FECHA_TEST, 'egreso', 'UYU', 500, 'Pago con cheque', None, 'Cheque', None)
    assert calcular_saldo_efectivo('UYU') == 0.0


# ── Las monedas son independientes entre sí ────────────────────────────────────

def test_saldos_uyu_y_usd_son_independientes(app):
    agregar_movimiento(FECHA_TEST, 'ingreso', 'UYU', 10000, 'Venta UYU', None, 'Efectivo', None)
    agregar_movimiento(FECHA_TEST, 'ingreso', 'USD', 200,   'Venta USD', None, 'Efectivo', None)
    assert calcular_saldo_efectivo('UYU') == 10000.0
    assert calcular_saldo_efectivo('USD') == 200.0


def test_egreso_usd_no_afecta_saldo_uyu(app):
    agregar_movimiento(FECHA_TEST, 'ingreso', 'UYU', 5000, 'Venta', None, 'Efectivo', None)
    agregar_movimiento(FECHA_TEST, 'egreso',  'USD', 100,  'Gasto', None, 'Efectivo', None)
    assert calcular_saldo_efectivo('UYU') == 5000.0
    assert calcular_saldo_efectivo('USD') == -100.0


# ── Movimientos del día ────────────────────────────────────────────────────────

def test_obtener_movimientos_del_dia_retorna_solo_esa_fecha(app):
    agregar_movimiento('2024-01-10', 'ingreso', 'UYU', 1000, 'Venta día A', None, 'Efectivo', None)
    agregar_movimiento('2024-01-11', 'ingreso', 'UYU', 2000, 'Venta día B', None, 'Efectivo', None)
    movs = obtener_movimientos_del_dia('2024-01-10')
    assert len(movs) == 1
    assert movs[0]['concepto'] == 'Venta día A'


def test_movimientos_dia_vacio_retorna_lista_vacia(app):
    movs = obtener_movimientos_del_dia('2024-01-01')
    assert movs == []
