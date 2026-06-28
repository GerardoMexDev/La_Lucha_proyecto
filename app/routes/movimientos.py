from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import date, datetime, timedelta

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
    obtener_totales_por_categoria,
    obtener_datos_grafica,
)

WHATSAPP_NUMERO = '59899760469'

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

    next_url = request.form.get('next') or url_for('movimientos.index', fecha=fecha)

    if errores:
        for msg in errores:
            flash(msg, 'error')
        return redirect(next_url)

    editar_movimiento(id, fecha, tipo, moneda, monto, concepto,
                      categoria_id, metodo_pago, observaciones)
    flash('Movimiento actualizado.', 'success')
    return redirect(next_url)


@bp.route('/movimiento/<int:id>/eliminar', methods=['POST'])
def eliminar_movimiento_route(id):
    fecha = request.form.get('fecha', date.today().isoformat())
    next_url = request.form.get('next') or url_for('movimientos.index', fecha=fecha)
    eliminar_movimiento(id)
    flash('Movimiento eliminado.', 'success')
    return redirect(next_url)


@bp.route('/reporte/adelantos')
def reporte_adelantos():
    return render_template(
        'reportes/adelantos.html',
        semanas=obtener_adelantos_por_semana(),
        categorias=obtener_categorias(),
        hoy=date.today(),
        wa_numero=WHATSAPP_NUMERO,
    )


@bp.route('/reporte/caja-diaria')
def reporte_caja_diaria():
    fecha = request.args.get('fecha', date.today().isoformat())

    fondo_uyu = obtener_fondo_caja(fecha, 'UYU')
    fondo_usd = obtener_fondo_caja(fecha, 'USD')
    fondo_brl = obtener_fondo_caja(fecha, 'BRL')

    totales_uyu = calcular_totales_dia(fecha, 'UYU')
    totales_usd = calcular_totales_dia(fecha, 'USD')
    totales_brl = calcular_totales_dia(fecha, 'BRL')

    ef_uyu = next((t for t in totales_uyu if t['metodo_pago'] == 'Efectivo'), None)
    ingresos_ef_uyu = float(ef_uyu['total_ingresos']) if ef_uyu else 0.0
    egresos_ef_uyu = float(ef_uyu['total_egresos']) if ef_uyu else 0.0
    saldo_uyu = fondo_uyu + ingresos_ef_uyu - egresos_ef_uyu

    totales_dia_usd = calcular_totales_dia_por_tipo(fecha, 'USD')
    totales_dia_brl = calcular_totales_dia_por_tipo(fecha, 'BRL')

    movimientos = obtener_movimientos_del_dia(fecha)
    totales_cat_uyu = obtener_totales_por_categoria(fecha, fecha, 'UYU')

    fecha_fmt = datetime.strptime(fecha, '%Y-%m-%d').strftime('%d/%m/%Y')
    wa_texto = (
        f"Reporte de Caja - {fecha_fmt}\n"
        f"La Lucha Gomería\n\n"
        f"CAJA UYU (efectivo)\n"
        f"Fondo: ${fondo_uyu:,.0f}\n"
        f"Ingresos ef.: ${ingresos_ef_uyu:,.0f}\n"
        f"Egresos ef.: ${egresos_ef_uyu:,.0f}\n"
        f"Saldo: ${saldo_uyu:,.0f}\n\n"
        f"USD (informativo)\n"
        f"Ingresos: ${totales_dia_usd['total_ingresos']:,.0f} / "
        f"Egresos: ${totales_dia_usd['total_egresos']:,.0f}\n\n"
        f"BRL (informativo)\n"
        f"Ingresos: R${totales_dia_brl['total_ingresos']:,.0f} / "
        f"Egresos: R${totales_dia_brl['total_egresos']:,.0f}\n\n"
        f"{len(movimientos)} movimientos registrados"
    )

    return render_template(
        'reportes/caja_diaria.html',
        fecha=fecha,
        hoy=date.today().isoformat(),
        fondo_uyu=fondo_uyu,
        fondo_usd=fondo_usd,
        fondo_brl=fondo_brl,
        ingresos_ef_uyu=ingresos_ef_uyu,
        egresos_ef_uyu=egresos_ef_uyu,
        saldo_uyu=saldo_uyu,
        totales_dia_usd=totales_dia_usd,
        totales_dia_brl=totales_dia_brl,
        movimientos=movimientos,
        totales_uyu=totales_uyu,
        totales_usd=totales_usd,
        totales_brl=totales_brl,
        totales_cat_uyu=totales_cat_uyu,
        wa_texto=wa_texto,
        wa_numero=WHATSAPP_NUMERO,
    )


@bp.route('/dashboard')
def dashboard():
    dias = int(request.args.get('dias', 30))
    hoy = date.today()
    fecha_hasta = hoy.isoformat()
    fecha_desde = (hoy - timedelta(days=dias - 1)).isoformat()

    datos_grafica = obtener_datos_grafica(dias)
    totales_cat_uyu = obtener_totales_por_categoria(fecha_desde, fecha_hasta, 'UYU')
    totales_cat_usd = obtener_totales_por_categoria(fecha_desde, fecha_hasta, 'USD')

    dias_labels = [(hoy - timedelta(days=dias - 1 - i)).isoformat() for i in range(dias)]

    return render_template(
        'dashboard/index.html',
        hoy=hoy.isoformat(),
        datos_grafica=datos_grafica,
        dias_labels=dias_labels,
        totales_cat_uyu=totales_cat_uyu,
        totales_cat_usd=totales_cat_usd,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        dias=dias,
    )
