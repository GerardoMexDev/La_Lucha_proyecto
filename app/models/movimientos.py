from datetime import datetime, timedelta, date as date_type

from ..db import get_db


def calcular_saldo_efectivo(moneda):
    """
    Saldo acumulado de caja en efectivo para la moneda dada.
    Solo cuenta movimientos en Efectivo — Tarjeta/Transferencia/Cheque
    son informativos y no se "arrastran" como fondo disponible.
    """
    db = get_db()
    fila = db.execute(
        """
        SELECT COALESCE(
            SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE -monto END), 0
        ) AS saldo
        FROM movimientos
        WHERE moneda = ? AND metodo_pago = 'Efectivo'
        """,
        (moneda,)
    ).fetchone()
    return float(fila['saldo']) if fila else 0.0


def obtener_movimientos_del_dia(fecha):
    """Todos los movimientos de una fecha, con nombre de categoría incluido."""
    db = get_db()
    return db.execute(
        """
        SELECT m.*, c.nombre AS categoria_nombre
        FROM movimientos m
        LEFT JOIN categorias c ON m.categoria_id = c.id
        WHERE m.fecha = ?
        ORDER BY m.creado_en
        """,
        (fecha,)
    ).fetchall()


def calcular_totales_dia(fecha, moneda):
    """
    Totales de ingresos y egresos agrupados por método de pago,
    para una fecha y moneda dadas.
    """
    db = get_db()
    return db.execute(
        """
        SELECT metodo_pago,
               SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END) AS total_ingresos,
               SUM(CASE WHEN tipo = 'egreso'  THEN monto ELSE 0 END) AS total_egresos
        FROM movimientos
        WHERE fecha = ? AND moneda = ?
        GROUP BY metodo_pago
        ORDER BY metodo_pago
        """,
        (fecha, moneda)
    ).fetchall()


def obtener_categorias():
    """Lista de categorías ordenada por tipo (ingresos primero) y nombre."""
    db = get_db()
    return db.execute(
        "SELECT * FROM categorias ORDER BY tipo DESC, nombre"
    ).fetchall()


def agregar_movimiento(fecha, tipo, moneda, monto, concepto,
                       categoria_id, metodo_pago, observaciones):
    """Inserta un movimiento nuevo en la base de datos."""
    db = get_db()
    db.execute(
        """
        INSERT INTO movimientos
            (fecha, tipo, moneda, monto, concepto, categoria_id, metodo_pago, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (fecha, tipo, moneda, float(monto),
         concepto, categoria_id or None, metodo_pago, observaciones or None)
    )
    db.commit()


def editar_movimiento(id, fecha, tipo, moneda, monto, concepto,
                      categoria_id, metodo_pago, observaciones):
    """Actualiza un movimiento existente."""
    db = get_db()
    db.execute(
        """
        UPDATE movimientos
        SET fecha=?, tipo=?, moneda=?, monto=?, concepto=?,
            categoria_id=?, metodo_pago=?, observaciones=?
        WHERE id=?
        """,
        (fecha, tipo, moneda, float(monto),
         concepto, categoria_id or None, metodo_pago, observaciones or None, id)
    )
    db.commit()


def eliminar_movimiento(id):
    """Elimina un movimiento por su ID."""
    db = get_db()
    db.execute("DELETE FROM movimientos WHERE id = ?", (id,))
    db.commit()


def obtener_fondo_caja(fecha, moneda):
    """
    Devuelve el fondo de caja vigente para la fecha y moneda dadas.
    Busca la entrada más reciente con fecha <= la pedida.
    """
    db = get_db()
    fila = db.execute(
        """
        SELECT monto FROM fondo_caja
        WHERE moneda = ? AND fecha <= ?
        ORDER BY fecha DESC
        LIMIT 1
        """,
        (moneda, fecha)
    ).fetchone()
    return float(fila['monto']) if fila else 0.0


def establecer_fondo_caja(fecha, moneda, monto):
    """Guarda o actualiza el fondo de caja para una fecha y moneda."""
    db = get_db()
    db.execute(
        """
        INSERT INTO fondo_caja (fecha, moneda, monto)
        VALUES (?, ?, ?)
        ON CONFLICT(fecha, moneda) DO UPDATE SET monto = excluded.monto
        """,
        (fecha, moneda, float(monto))
    )
    db.commit()


def calcular_neto_efectivo_dia(fecha, moneda):
    """Suma neta (ingresos − egresos) de movimientos en Efectivo para un día."""
    db = get_db()
    fila = db.execute(
        """
        SELECT COALESCE(
            SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE -monto END), 0
        ) AS neto
        FROM movimientos
        WHERE fecha = ? AND moneda = ? AND metodo_pago = 'Efectivo'
        """,
        (fecha, moneda)
    ).fetchone()
    return float(fila['neto']) if fila else 0.0


def calcular_totales_dia_por_tipo(fecha, moneda):
    """Ingresos y egresos totales del día para una moneda (todos los métodos)."""
    db = get_db()
    fila = db.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END), 0) AS total_ingresos,
            COALESCE(SUM(CASE WHEN tipo = 'egreso'  THEN monto ELSE 0 END), 0) AS total_egresos
        FROM movimientos
        WHERE fecha = ? AND moneda = ?
        """,
        (fecha, moneda)
    ).fetchone()
    return {
        'total_ingresos': float(fila['total_ingresos']),
        'total_egresos':  float(fila['total_egresos']),
    }


def obtener_adelantos_por_semana():
    """
    Retorna los adelantos de sueldo agrupados por semana y luego por empleado
    (el campo concepto actúa como nombre del empleado).
    Cada semana cierra el sábado (corte semanal del negocio).
    """
    db = get_db()
    filas = db.execute(
        """
        SELECT m.id, m.fecha, m.concepto, m.moneda, m.monto,
               m.metodo_pago, m.observaciones, m.categoria_id
        FROM movimientos m
        JOIN categorias c ON m.categoria_id = c.id
        WHERE c.nombre = 'Adelanto de sueldo'
        ORDER BY m.fecha, m.concepto, m.creado_en
        """
    ).fetchall()

    hoy = date_type.today()
    semanas = {}

    for fila in filas:
        fecha = datetime.strptime(fila['fecha'], '%Y-%m-%d').date()
        dias_hasta_sabado = (5 - fecha.weekday()) % 7
        sabado = fecha + timedelta(days=dias_hasta_sabado)
        lunes = sabado - timedelta(days=5)
        clave = sabado.isoformat()

        if clave not in semanas:
            semanas[clave] = {
                'sabado': sabado,
                'lunes': lunes,
                'es_semana_actual': sabado >= hoy,
                'empleados': {},
                'total_uyu': 0.0,
                'total_usd': 0.0,
            }

        empleado = fila['concepto']
        if empleado not in semanas[clave]['empleados']:
            semanas[clave]['empleados'][empleado] = {
                'nombre': empleado,
                'movimientos': [],
                'total_uyu': 0.0,
                'total_usd': 0.0,
            }

        semanas[clave]['empleados'][empleado]['movimientos'].append(dict(fila))
        if fila['moneda'] == 'UYU':
            semanas[clave]['empleados'][empleado]['total_uyu'] += float(fila['monto'])
            semanas[clave]['total_uyu'] += float(fila['monto'])
        elif fila['moneda'] == 'USD':
            semanas[clave]['empleados'][empleado]['total_usd'] += float(fila['monto'])
            semanas[clave]['total_usd'] += float(fila['monto'])

    for sem in semanas.values():
        sem['empleados'] = sorted(sem['empleados'].values(), key=lambda e: e['nombre'])

    return sorted(semanas.values(), key=lambda s: s['sabado'], reverse=True)


def obtener_totales_por_categoria(fecha_desde, fecha_hasta, moneda='UYU'):
    """Ingresos y egresos por categoría en un rango de fechas."""
    db = get_db()
    return db.execute(
        """
        SELECT COALESCE(c.nombre, 'Sin categoría') AS categoria,
               COALESCE(c.tipo, 'ambos') AS tipo_cat,
               SUM(CASE WHEN m.tipo='ingreso' THEN m.monto ELSE 0 END) AS total_ingresos,
               SUM(CASE WHEN m.tipo='egreso'  THEN m.monto ELSE 0 END) AS total_egresos
        FROM movimientos m
        LEFT JOIN categorias c ON m.categoria_id = c.id
        WHERE m.fecha BETWEEN ? AND ? AND m.moneda = ?
        GROUP BY m.categoria_id, c.nombre
        ORDER BY total_egresos DESC, total_ingresos DESC
        """,
        (fecha_desde, fecha_hasta, moneda)
    ).fetchall()


def obtener_datos_grafica(dias=30):
    """
    Ingresos y egresos por día de los últimos N días, agrupados por moneda.
    Retorna dict { 'UYU': {'YYYY-MM-DD': {'ingresos': x, 'egresos': y}, ...}, ... }
    """
    db = get_db()
    desde = (date_type.today() - timedelta(days=dias - 1)).isoformat()
    filas = db.execute(
        """
        SELECT fecha, moneda,
               SUM(CASE WHEN tipo='ingreso' THEN monto ELSE 0 END) AS ingresos,
               SUM(CASE WHEN tipo='egreso'  THEN monto ELSE 0 END) AS egresos
        FROM movimientos
        WHERE fecha >= ?
        GROUP BY fecha, moneda
        ORDER BY fecha, moneda
        """,
        (desde,)
    ).fetchall()

    result = {'UYU': {}, 'USD': {}, 'BRL': {}}
    for fila in filas:
        m = fila['moneda']
        if m in result:
            result[m][fila['fecha']] = {
                'ingresos': float(fila['ingresos']),
                'egresos': float(fila['egresos']),
            }
    return result
