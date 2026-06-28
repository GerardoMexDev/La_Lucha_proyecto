from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import date

from ..models.movimientos import (
    obtener_movimientos_del_dia,
    calcular_totales_dia,
    obtener_categorias,
    agregar_movimiento,
    editar_movimiento,
    eliminar_movimiento,
    obtener_adelantos_por_semana,
    obtener_fondo_caja,
    establecer_fondo_caja,
    calcular_totales_dia_por_tipo,
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

    fondo_uyu    = obtener_fondo_caja(fecha, 'UYU')
    totales_uyu  = calcular_totales_dia(fecha, 'UYU')

    # Extraer ingresos y egresos efectivo UYU del día
    ef_uyu = next((t for t in totales_uyu if t['metodo_pago'] == 'Efectivo'), None)
    ingresos_ef_uyu = float(ef_uyu['total_ingresos']) if ef_uyu else 0.0
    egresos_ef_uyu  = float(ef_uyu['total_egresos'])  if ef_uyu else 0.0

    return render_template(
        'movimientos/cargar.html',
        fecha=fecha,
        hoy=date.today().isoformat(),
        # Caja UYU: fondo + efectivo del día
        fondo_uyu=fondo_uyu,
        ingresos_ef_uyu=ingresos_ef_uyu,
        egresos_ef_uyu=egresos_ef_uyu,
        saldo_dia_uyu=fondo_uyu + ingresos_ef_uyu - egresos_ef_uyu,
        # USD y BRL: solo totales informativos del día
        totales_dia_usd=calcular_totales_dia_por_tipo(fecha, 'USD'),
        totales_dia_brl=calcular_totales_dia_por_tipo(fecha, 'BRL'),
        # Tabla de movimientos del día
        movimientos=obtener_movimientos_del_dia(fecha),
        # Desglose por método (para la tabla de totales)
        totales_uyu=totales_uyu,
        totales_usd=calcular_totales_dia(fecha, 'USD'),
        totales_brl=calcular_totales_dia(fecha, 'BRL'),
        categorias=obtener_categorias(),
    )


@bp.route('/fondo_caja', methods=['POST'])
def guardar_fondo_caja():
    fecha  = request.form.get('fecha', date.today().isoformat())
    moneda = request.form.get('moneda', 'UYU')
    monto_str = request.form.get('monto', '').strip().replace(',', '.')
    try:
        monto = float(monto_str)
        if monto < 0:
            raise ValueError
    except (ValueError, TypeError):
        flash('El fondo de caja debe ser un número mayor o igual a 0.', 'error')
        return redirect(url_for('movimientos.index', fecha=fecha))

    establecer_fondo_caja(fecha, moneda, monto)
    flash(f'Fondo de caja {moneda} actualizado: {monto:,.0f}', 'success')
    return redirect(url_for('movimientos.index', fecha=fecha))


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
