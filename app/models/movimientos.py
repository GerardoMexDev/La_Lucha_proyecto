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


def obtener_adelantos_por_semana():
    """
    Retorna los adelantos de sueldo agrupados por semana.
    Cada semana cierra el sábado (corte semanal del negocio).
    """
    db = get_db()
    filas = db.execute(
        """
        SELECT m.id, m.fecha, m.concepto, m.moneda, m.monto,
               m.metodo_pago, m.observaciones
        FROM movimientos m
        JOIN categorias c ON m.categoria_id = c.id
        WHERE c.nombre = 'Adelanto de sueldo'
        ORDER BY m.fecha, m.creado_en
        """
    ).fetchall()

    hoy = date_type.today()
    semanas = {}

    for fila in filas:
        fecha = datetime.strptime(fila['fecha'], '%Y-%m-%d').date()
        # Sábado de cierre de la semana que contiene esta fecha
        # Python weekday(): lunes=0 ... sábado=5 ... domingo=6
        dias_hasta_sabado = (5 - fecha.weekday()) % 7
        sabado = fecha + timedelta(days=dias_hasta_sabado)
        lunes = sabado - timedelta(days=5)
        clave = sabado.isoformat()

        if clave not in semanas:
            semanas[clave] = {
                'sabado': sabado,
                'lunes': lunes,
                'es_semana_actual': sabado >= hoy,
                'movimientos': [],
                'total_uyu': 0.0,
                'total_usd': 0.0,
            }
        semanas[clave]['movimientos'].append(dict(fila))
        if fila['moneda'] == 'UYU':
            semanas[clave]['total_uyu'] += fila['monto']
        else:
            semanas[clave]['total_usd'] += fila['monto']

    return sorted(semanas.values(), key=lambda s: s['sabado'], reverse=True)
