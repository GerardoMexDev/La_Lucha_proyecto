from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import date

from ..models.movimientos import (
    calcular_saldo_efectivo,
    obtener_movimientos_del_dia,
    calcular_totales_dia,
    obtener_categorias,
    agregar_movimiento,
)

bp = Blueprint('movimientos', __name__)


@bp.route('/', methods=['GET'])
def index():
    fecha = request.args.get('fecha', date.today().isoformat())
    return render_template(
        'movimientos/cargar.html',
        fecha=fecha,
        hoy=date.today().isoformat(),
        saldo_uyu=calcular_saldo_efectivo('UYU'),
        saldo_usd=calcular_saldo_efectivo('USD'),
        movimientos=obtener_movimientos_del_dia(fecha),
        totales_uyu=calcular_totales_dia(fecha, 'UYU'),
        totales_usd=calcular_totales_dia(fecha, 'USD'),
        categorias=obtener_categorias(),
    )


@bp.route('/movimiento/nuevo', methods=['POST'])
def nuevo_movimiento():
    fecha = request.form.get('fecha', date.today().isoformat())
    tipo = request.form.get('tipo', 'ingreso')
    moneda = request.form.get('moneda', 'UYU')
    monto_str = request.form.get('monto', '').strip().replace(',', '.')
    concepto = request.form.get('concepto', '').strip()
    categoria_id = request.form.get('categoria_id') or None
    metodo_pago = request.form.get('metodo_pago', 'Efectivo')
    observaciones = request.form.get('observaciones', '').strip() or None

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

    if errores:
        for mensaje in errores:
            flash(mensaje, 'error')
        return redirect(url_for('movimientos.index', fecha=fecha))

    agregar_movimiento(fecha, tipo, moneda, monto, concepto,
                       categoria_id, metodo_pago, observaciones)
    flash('Movimiento registrado correctamente.', 'success')
    return redirect(url_for('movimientos.index', fecha=fecha))
