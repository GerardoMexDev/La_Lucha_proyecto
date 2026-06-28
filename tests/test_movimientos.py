import pytest
from app import create_app
from app.db import init_db
from app.models.movimientos import (
    calcular_saldo_efectivo,
    agregar_movimiento,
    editar_movimiento,
    eliminar_movimiento,
    obtener_movimientos_del_dia,
    obtener_adelantos_por_semana,
    obtener_fondo_caja,
    establecer_fondo_caja,
    calcular_neto_efectivo_dia,
    calcular_totales_dia_por_tipo,
)

FECHA_TEST = '2024-01-15'


@pytest.fixture
def app():
    """App de prueba con base de datos en memoria."""
    test_app = create_app({'TESTING': True, 'DATABASE': ':memory:'})
    with test_app.app_context():
        init_db()
        yield test_app


def _id_categoria_adelanto(app):
    """Helper: retorna el ID de la categoría 'Adelanto de sueldo'."""
    from app.db import get_db
    fila = get_db().execute(
        "SELECT id FROM categorias WHERE nombre = 'Adelanto de sueldo'"
    ).fetchone()
    assert fila is not None, "La categoría 'Adelanto de sueldo' debe existir"
    return fila['id']


# ── Saldo de caja en efectivo ──────────────────────────────────────────────────

def test_saldo_inicial_es_cero(app):
    assert calcular_saldo_efectivo('UYU') == 0.0
    assert calcular_saldo_efectivo('USD') == 0.0
    assert calcular_saldo_efectivo('BRL') == 0.0


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
    agregar_movimiento(FECHA_TEST, 'ingreso', 'UYU', 2000, 'Venta tarjeta', None, 'Tarjeta', None)
    assert calcular_saldo_efectivo('UYU') == 0.0


def test_transferencia_no_afecta_saldo_efectivo(app):
    agregar_movimiento(FECHA_TEST, 'ingreso', 'UYU', 2000, 'Transferencia', None, 'Transferencia', None)
    assert calcular_saldo_efectivo('UYU') == 0.0


def test_cheque_no_afecta_saldo_efectivo(app):
    agregar_movimiento(FECHA_TEST, 'egreso', 'UYU', 500, 'Pago cheque', None, 'Cheque', None)
    assert calcular_saldo_efectivo('UYU') == 0.0


# ── Las monedas son independientes entre sí ────────────────────────────────────

def test_saldos_uyu_y_usd_son_independientes(app):
    agregar_movimiento(FECHA_TEST, 'ingreso', 'UYU', 10000, 'Venta UYU', None, 'Efectivo', None)
    agregar_movimiento(FECHA_TEST, 'ingreso', 'USD', 200,   'Venta USD', None, 'Efectivo', None)
    assert calcular_saldo_efectivo('UYU') == 10000.0
    assert calcular_saldo_efectivo('USD') == 200.0


def test_brl_independiente_de_uyu_y_usd(app):
    agregar_movimiento(FECHA_TEST, 'ingreso', 'BRL', 500, 'Servicio en reales', None, 'Efectivo', None)
    assert calcular_saldo_efectivo('BRL') == 500.0
    assert calcular_saldo_efectivo('UYU') == 0.0
    assert calcular_saldo_efectivo('USD') == 0.0


def test_retiro_brl_reduce_saldo(app):
    agregar_movimiento(FECHA_TEST, 'ingreso', 'BRL', 500, 'Cobro en reales',    None, 'Efectivo', None)
    agregar_movimiento(FECHA_TEST, 'egreso',  'BRL', 500, 'Retiro para cambio', None, 'Efectivo', None)
    assert calcular_saldo_efectivo('BRL') == 0.0


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
    assert obtener_movimientos_del_dia('2024-01-01') == []


# ── Editar movimientos ─────────────────────────────────────────────────────────

def test_editar_movimiento_actualiza_campos(app):
    agregar_movimiento(FECHA_TEST, 'ingreso', 'UYU', 1000, 'Original', None, 'Efectivo', None)
    mov_id = obtener_movimientos_del_dia(FECHA_TEST)[0]['id']
    editar_movimiento(mov_id, FECHA_TEST, 'egreso', 'UYU', 500, 'Corregido', None, 'Efectivo', None)
    mov = obtener_movimientos_del_dia(FECHA_TEST)[0]
    assert mov['concepto'] == 'Corregido'
    assert mov['tipo'] == 'egreso'
    assert mov['monto'] == 500.0


def test_editar_movimiento_recalcula_saldo(app):
    agregar_movimiento(FECHA_TEST, 'ingreso', 'UYU', 1000, 'Venta', None, 'Efectivo', None)
    mov_id = obtener_movimientos_del_dia(FECHA_TEST)[0]['id']
    editar_movimiento(mov_id, FECHA_TEST, 'ingreso', 'UYU', 800, 'Venta corregida', None, 'Efectivo', None)
    assert calcular_saldo_efectivo('UYU') == 800.0


# ── Eliminar movimientos ───────────────────────────────────────────────────────

def test_eliminar_movimiento_borra_el_registro(app):
    agregar_movimiento(FECHA_TEST, 'ingreso', 'UYU', 1000, 'Para borrar', None, 'Efectivo', None)
    mov_id = obtener_movimientos_del_dia(FECHA_TEST)[0]['id']
    eliminar_movimiento(mov_id)
    assert obtener_movimientos_del_dia(FECHA_TEST) == []


def test_eliminar_movimiento_actualiza_saldo(app):
    agregar_movimiento(FECHA_TEST, 'ingreso', 'UYU', 1000, 'Para borrar', None, 'Efectivo', None)
    mov_id = obtener_movimientos_del_dia(FECHA_TEST)[0]['id']
    eliminar_movimiento(mov_id)
    assert calcular_saldo_efectivo('UYU') == 0.0


# ── Reporte de adelantos por semana ───────────────────────────────────────────

def test_adelantos_vacio_retorna_lista_vacia(app):
    assert obtener_adelantos_por_semana() == []


def test_adelantos_no_incluye_otras_categorias(app):
    agregar_movimiento(FECHA_TEST, 'egreso', 'UYU', 500, 'Insumos', None, 'Efectivo', None)
    assert obtener_adelantos_por_semana() == []


def test_adelantos_agrupa_por_semana(app):
    cat_id = _id_categoria_adelanto(app)
    # Lunes 15/01 y miércoles 17/01 → mismo sábado de cierre: 20/01
    agregar_movimiento('2024-01-15', 'egreso', 'UYU', 2000, 'Adelanto empleado A', cat_id, 'Efectivo', None)
    agregar_movimiento('2024-01-17', 'egreso', 'UYU', 1500, 'Adelanto empleado B', cat_id, 'Efectivo', None)
    # Lunes 22/01 → sábado de cierre: 27/01 (semana siguiente)
    agregar_movimiento('2024-01-22', 'egreso', 'UYU', 3000, 'Adelanto empleado A', cat_id, 'Efectivo', None)

    semanas = obtener_adelantos_por_semana()
    assert len(semanas) == 2
    # Más reciente primero
    assert semanas[0]['total_uyu'] == 3000.0   # semana del 22-27/01
    assert semanas[1]['total_uyu'] == 3500.0   # semana del 15-20/01
    # La semana 15-20/01 tiene 2 empleados distintos, 1 movimiento cada uno
    empleados_sem1 = semanas[1]['empleados']
    assert len(empleados_sem1) == 2
    total_movs = sum(len(e['movimientos']) for e in empleados_sem1)
    assert total_movs == 2


def test_adelantos_sabado_cierra_en_su_propia_semana(app):
    cat_id = _id_categoria_adelanto(app)
    # 20/01/2024 es sábado: el cierre debe ser ese mismo día
    agregar_movimiento('2024-01-20', 'egreso', 'UYU', 1000, 'Adelanto sábado', cat_id, 'Efectivo', None)
    semanas = obtener_adelantos_por_semana()
    assert len(semanas) == 1
    assert semanas[0]['sabado'].isoformat() == '2024-01-20'


def test_adelantos_usd_y_uyu_se_totalizan_por_separado(app):
    cat_id = _id_categoria_adelanto(app)
    agregar_movimiento('2024-01-15', 'egreso', 'UYU', 5000, 'Adelanto UYU', cat_id, 'Efectivo', None)
    agregar_movimiento('2024-01-15', 'egreso', 'USD', 100,  'Adelanto USD', cat_id, 'Efectivo', None)
    semanas = obtener_adelantos_por_semana()
    assert len(semanas) == 1
    assert semanas[0]['total_uyu'] == 5000.0
    assert semanas[0]['total_usd'] == 100.0


# ── Fondo de caja ──────────────────────────────────────────────────────────────

def test_fondo_caja_inicial_es_cero(app):
    assert obtener_fondo_caja(FECHA_TEST, 'UYU') == 0.0


def test_establecer_fondo_caja(app):
    establecer_fondo_caja(FECHA_TEST, 'UYU', 5000)
    assert obtener_fondo_caja(FECHA_TEST, 'UYU') == 5000.0


def test_fondo_caja_se_actualiza(app):
    establecer_fondo_caja(FECHA_TEST, 'UYU', 5000)
    establecer_fondo_caja(FECHA_TEST, 'UYU', 3000)
    assert obtener_fondo_caja(FECHA_TEST, 'UYU') == 3000.0


def test_fondo_caja_se_hereda_de_fecha_anterior(app):
    # Fondo puesto el día 10 debe estar vigente el día 15
    establecer_fondo_caja('2024-01-10', 'UYU', 2000)
    assert obtener_fondo_caja('2024-01-15', 'UYU') == 2000.0


def test_fondo_caja_no_afecta_otra_moneda(app):
    establecer_fondo_caja(FECHA_TEST, 'UYU', 5000)
    assert obtener_fondo_caja(FECHA_TEST, 'USD') == 0.0


def test_saldo_dia_con_fondo(app):
    establecer_fondo_caja(FECHA_TEST, 'UYU', 2000)
    agregar_movimiento(FECHA_TEST, 'ingreso', 'UYU', 1000, 'Venta', None, 'Efectivo', None)
    agregar_movimiento(FECHA_TEST, 'egreso',  'UYU', 300,  'Gasto', None, 'Efectivo', None)
    fondo = obtener_fondo_caja(FECHA_TEST, 'UYU')
    neto  = calcular_neto_efectivo_dia(FECHA_TEST, 'UYU')
    assert fondo + neto == 2700.0


def test_totales_dia_por_tipo(app):
    agregar_movimiento(FECHA_TEST, 'ingreso', 'USD', 200, 'Cobro USD', None, 'Efectivo', None)
    agregar_movimiento(FECHA_TEST, 'egreso',  'USD', 50,  'Gasto USD', None, 'Efectivo', None)
    totales = calcular_totales_dia_por_tipo(FECHA_TEST, 'USD')
    assert totales['total_ingresos'] == 200.0
    assert totales['total_egresos']  == 50.0
