from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import date, datetime, timedelta
from calendar import monthrange

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
    obtener_totales_periodo,
    obtener_saldo_historico_diario,
)

WHATSAPP_NUMERO  = '59899760469'
FONDO_MINIMO_UYU = 3000

MESES_ES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre',
}

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


def _variacion_pct(actual, anterior):
    """Variación porcentual entre dos valores. Retorna None si anterior es 0."""
    if anterior == 0:
        return None
    return round(((actual - anterior) / anterior) * 100, 1)


def _construir_comparativos():
    """
    Construye comparativos de ingresos/egresos por semana, quincena, mes y año,
    desglosados por moneda (UYU, USD, BRL).
    """
    hoy = date.today()
    comparativos = {}

    for moneda in ['UYU', 'USD', 'BRL']:

        # ── Semana ──────────────────────────────────────────────────────────
        lunes_actual   = hoy - timedelta(days=hoy.weekday())
        sabado_actual  = lunes_actual + timedelta(days=6)
        lunes_anterior = lunes_actual - timedelta(days=7)
        sabado_anterior = lunes_actual - timedelta(days=1)

        act_sem = obtener_totales_periodo(lunes_actual, min(sabado_actual, hoy), moneda)
        ant_sem = obtener_totales_periodo(lunes_anterior, sabado_anterior, moneda)

        # ── Quincena ────────────────────────────────────────────────────────
        if hoy.day <= 15:
            q_desde = hoy.replace(day=1)
            q_hasta = hoy.replace(day=15)
            # Quincena anterior: 16-fin del mes pasado
            if hoy.month == 1:
                mes_q = date(hoy.year - 1, 12, 1)
            else:
                mes_q = date(hoy.year, hoy.month - 1, 1)
            _, ultimo_q = monthrange(mes_q.year, mes_q.month)
            qp_desde = mes_q.replace(day=16)
            qp_hasta = mes_q.replace(day=ultimo_q)
            label_q  = f'1–15/{hoy.strftime("%m/%Y")}'
            label_qp = f'16–{ultimo_q}/{mes_q.strftime("%m/%Y")}'
        else:
            q_desde = hoy.replace(day=16)
            _, ultimo_q = monthrange(hoy.year, hoy.month)
            q_hasta = hoy
            qp_desde = hoy.replace(day=1)
            qp_hasta = hoy.replace(day=15)
            label_q  = f'16–{hoy.day}/{hoy.strftime("%m/%Y")}'
            label_qp = f'1–15/{hoy.strftime("%m/%Y")}'

        act_qui = obtener_totales_periodo(q_desde, min(q_hasta, hoy), moneda)
        ant_qui = obtener_totales_periodo(qp_desde, qp_hasta, moneda)

        # ── Mes ─────────────────────────────────────────────────────────────
        mes_desde = hoy.replace(day=1)
        if hoy.month == 1:
            mes_ant = date(hoy.year - 1, 12, 1)
        else:
            mes_ant = date(hoy.year, hoy.month - 1, 1)
        _, ultimo_mes_ant = monthrange(mes_ant.year, mes_ant.month)
        mes_ant_hasta = mes_ant.replace(day=ultimo_mes_ant)

        act_mes = obtener_totales_periodo(mes_desde, hoy, moneda)
        ant_mes = obtener_totales_periodo(mes_ant, mes_ant_hasta, moneda)

        # ── Año ─────────────────────────────────────────────────────────────
        anio_desde     = date(hoy.year, 1, 1)
        anio_ant_desde = date(hoy.year - 1, 1, 1)
        anio_ant_hasta = date(hoy.year - 1, 12, 31)

        act_anio = obtener_totales_periodo(anio_desde, hoy, moneda)
        ant_anio = obtener_totales_periodo(anio_ant_desde, anio_ant_hasta, moneda)

        comparativos[moneda] = {
            'semana': {
                'actual':   act_sem,
                'anterior': ant_sem,
                'label_actual':   f'{lunes_actual.strftime("%d/%m")} – {min(sabado_actual, hoy).strftime("%d/%m")}',
                'label_anterior': f'{lunes_anterior.strftime("%d/%m")} – {sabado_anterior.strftime("%d/%m")}',
                'var_ingr': _variacion_pct(act_sem['ingresos'], ant_sem['ingresos']),
                'var_egr':  _variacion_pct(act_sem['egresos'],  ant_sem['egresos']),
            },
            'quincena': {
                'actual':   act_qui,
                'anterior': ant_qui,
                'label_actual':   label_q,
                'label_anterior': label_qp,
                'var_ingr': _variacion_pct(act_qui['ingresos'], ant_qui['ingresos']),
                'var_egr':  _variacion_pct(act_qui['egresos'],  ant_qui['egresos']),
            },
            'mes': {
                'actual':   act_mes,
                'anterior': ant_mes,
                'label_actual':   f'{MESES_ES[hoy.month]} {hoy.year}',
                'label_anterior': f'{MESES_ES[mes_ant.month]} {mes_ant.year}',
                'var_ingr': _variacion_pct(act_mes['ingresos'], ant_mes['ingresos']),
                'var_egr':  _variacion_pct(act_mes['egresos'],  ant_mes['egresos']),
            },
            'anio': {
                'actual':   act_anio,
                'anterior': ant_anio,
                'label_actual':   str(hoy.year),
                'label_anterior': str(hoy.year - 1),
                'var_ingr': _variacion_pct(act_anio['ingresos'], ant_anio['ingresos']),
                'var_egr':  _variacion_pct(act_anio['egresos'],  ant_anio['egresos']),
            },
        }

    return comparativos


@bp.route('/', methods=['GET'])
def index():
    fecha = request.args.get('fecha', date.today().isoformat())

    fondo_uyu   = obtener_fondo_caja(fecha, 'UYU')
    totales_uyu = calcular_totales_dia(fecha, 'UYU')

    ef_uyu = next((t for t in totales_uyu if t['metodo_pago'] == 'Efectivo'), None)
    ingresos_ef_uyu = float(ef_uyu['total_ingresos']) if ef_uyu else 0.0
    egresos_ef_uyu  = float(ef_uyu['total_egresos'])  if ef_uyu else 0.0
    saldo_dia_uyu   = fondo_uyu + ingresos_ef_uyu - egresos_ef_uyu

    # Alerta si el saldo cae debajo del mínimo configurado
    if saldo_dia_uyu < 0:
        alerta_saldo = 'critico'
    elif saldo_dia_uyu < FONDO_MINIMO_UYU:
        alerta_saldo = 'bajo'
    else:
        alerta_saldo = None

    return render_template(
        'movimientos/cargar.html',
        fecha=fecha,
        hoy=date.today().isoformat(),
        fondo_uyu=fondo_uyu,
        ingresos_ef_uyu=ingresos_ef_uyu,
        egresos_ef_uyu=egresos_ef_uyu,
        saldo_dia_uyu=saldo_dia_uyu,
        totales_dia_usd=calcular_totales_dia_por_tipo(fecha, 'USD'),
        totales_dia_brl=calcular_totales_dia_por_tipo(fecha, 'BRL'),
        movimientos=obtener_movimientos_del_dia(fecha),
        totales_uyu=totales_uyu,
        totales_usd=calcular_totales_dia(fecha, 'USD'),
        totales_brl=calcular_totales_dia(fecha, 'BRL'),
        categorias=obtener_categorias(),
        alerta_saldo=alerta_saldo,
        fondo_minimo_uyu=FONDO_MINIMO_UYU,
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
    egresos_ef_uyu  = float(ef_uyu['total_egresos'])  if ef_uyu else 0.0
    saldo_uyu = fondo_uyu + ingresos_ef_uyu - egresos_ef_uyu

    totales_dia_usd = calcular_totales_dia_por_tipo(fecha, 'USD')
    totales_dia_brl = calcular_totales_dia_por_tipo(fecha, 'BRL')
    movimientos     = obtener_movimientos_del_dia(fecha)
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
    hoy  = date.today()
    fecha_hasta = hoy.isoformat()
    fecha_desde = (hoy - timedelta(days=dias - 1)).isoformat()

    datos_grafica    = obtener_datos_grafica(dias)
    totales_cat_uyu  = obtener_totales_por_categoria(fecha_desde, fecha_hasta, 'UYU')
    totales_cat_usd  = obtener_totales_por_categoria(fecha_desde, fecha_hasta, 'USD')
    saldo_historico  = obtener_saldo_historico_diario(dias, 'UYU')
    comparativos     = _construir_comparativos()
    dias_labels      = [(hoy - timedelta(days=dias - 1 - i)).isoformat() for i in range(dias)]

    return render_template(
        'dashboard/index.html',
        hoy=hoy.isoformat(),
        datos_grafica=datos_grafica,
        dias_labels=dias_labels,
        totales_cat_uyu=totales_cat_uyu,
        totales_cat_usd=totales_cat_usd,
        saldo_historico=saldo_historico,
        comparativos=comparativos,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        dias=dias,
    )
