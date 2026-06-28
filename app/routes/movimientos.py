from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import date

from ..models.movimientos import (
    calcular_saldo_efectivo,
    obtener_movimientos_del_dia,
    calcular_totales_dia,
    obtener_categorias,
    agregar_movimiento,
    editar_movimiento,
    eliminar_movimiento,
    obtener_adelantos_por_semana,
)

bp = Blueprint('movimientos', __name__)


def _validar_formulario(form):
    """Extrae y valida los campos comunes de un formulario de movimiento."""
    fecha = form.get('fecha', date.today().isoformat())
    tipo = form.get('tipo', 'ingreso')
    moneda = form.get('moneda', 'UYU')
    monto_str = form.get('monto', '').strip().replace(',', '.')
    concepto = form.get('concepto', '').strip()
    categoria_id = form.get('categoria_id') or None
    metodo_pago = form.get('metodo_pago', 'Efectivo')
    observaciones = form.get('observaciones', '').strip() or None

    errores = []
    if not concepto:
        errores.append('El concepto es obligatorio.')
    monto = None
    if not monto_str:
        errores.append('El monto es obligatorio.')
    else:
        try:
            monto = float(monto_str)
            if monto <= 0:
                errores.append('El monto debe ser mayor a 0.')
        except ValueError:
            errores.append('El monto debe ser un número válido.')

    return (fecha, tipo, moneda, monto, concepto, categoria_id,
            metodo_pago, observaciones, errores)


@bp.route('/', methods=['GET'])
def index():
    fecha = request.args.get('fecha', date.today().isoformat())
    return render_template(
        'movimientos/cargar.html',
        fecha=fecha,
        hoy=date.today().isoformat(),
        saldo_uyu=calcular_saldo_efectivo('UYU'),
        saldo_usd=calcular_saldo_efectivo('USD'),
        saldo_brl=calcular_saldo_efectivo('BRL'),
        movimientos=obtener_movimientos_del_dia(fecha),
        totales_uyu=calcular_totales_dia(fecha, 'UYU'),
        totales_usd=calcular_totales_dia(fecha, 'USD'),
        totales_brl=calcular_totales_dia(fecha, 'BRL'),
        categorias=obtener_categorias(),
    )


@bp.route('/movimiento/nuevo', methods=['POST'])
def nuevo_movimiento():
    fecha, tipo, moneda, monto, concepto, categoria_id, \
        metodo_pago, observaciones, errores = _validar_formulario(request.form)

    if errores:
        for msg in errores:
            flash(msg, 'error')
        return redirect(url_for('movimientos.index', fecha=fecha))

    agregar_movimiento(fecha, tipo, moneda, monto, concepto,
                       categoria_id, metodo_pago, observaciones)
    flash('Movimiento registrado correctamente.', 'success')
    return redirect(url_for('movimientos.index', fecha=fecha))


@bp.route('/movimiento/<int:id>/editar', methods=['POST'])
def editar_movimiento_route(id):
    fecha, tipo, moneda, monto, concepto, categoria_id, \
        metodo_pago, observaciones, errores = _validar_formulario(request.form)

    if errores:
        for msg in errores:
            flash(msg, 'error')
        return redirect(url_for('movimientos.index', fecha=fecha))

    editar_movimiento(id, fecha, tipo, moneda, monto, concepto,
                      categoria_id, metodo_pago, observaciones)
    flash('Movimiento actualizado.', 'success')
    return redirect(url_for('movimientos.index', fecha=fecha))


@bp.route('/movimiento/<int:id>/eliminar', methods=['POST'])
def eliminar_movimiento_route(id):
    fecha = request.form.get('fecha', date.today().isoformat())
    eliminar_movimiento(id)
    flash('Movimiento eliminado.', 'success')
    return redirect(url_for('movimientos.index', fecha=fecha))


@bp.route('/reporte/adelantos')
def reporte_adelantos():
    return render_template(
        'reportes/adelantos.html',
        semanas=obtener_adelantos_por_semana(),
        hoy=date.today(),
    )
