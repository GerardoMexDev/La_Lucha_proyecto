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
    para una fecha y moneda dadas. Sirve para mostrar el resumen del día.
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
    """Lista de categorías ordenada por tipo (ingreso primero) y nombre."""
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
