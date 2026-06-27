# Plan de Proyecto: Sistema de Caja Chica (Gomería)

> **Propósito de este documento:** este `.md` es el contexto de planeación para reemplazar el control de caja en Excel por un programa propio. Antes de escribir código, leer este documento completo para entender qué se va a construir, por qué, y en qué orden. Esto cubre solo la **Fase 1**. Las fases siguientes se planean recién cuando se analicen las otras hojas del Excel.

---

## 1. Contexto del negocio

La empresa es una **gomería** (taller de neumáticos) que además usa la misma planilla para controlar **sueldos, adelantos y viáticos de empleados**. El archivo Excel actual (`Control_Contable_Sueldos_Gomeria_Monedas_2.xlsx`) tiene 6 hojas:

| Hoja | Contenido | Estado en este plan |
|---|---|---|
| **Caja Diaria** | Movimientos de caja día a día | ✅ Analizada — es el alcance de la Fase 1 |
| Adelantos y Extras | Adelantos de sueldo por empleado | ⏳ Fase futura |
| Liquidación Semanal | Cálculo de sueldo neto semanal | ⏳ Fase futura |
| Combustible | Consumo de combustible | ⏳ Fase futura |
| Bancos | Movimientos bancarios | ⏳ Fase futura |
| Cheques | Control de cheques | ⏳ Fase futura |

---

## 2. Qué hace hoy la hoja "Caja Diaria" (diagnóstico)

Cada movimiento de caja tiene estos campos:

- **Fecha**
- **Concepto** (texto libre: "Trabajo", "Venta cubierta", "Adelanto sueldo Rodrigo", "Pinchazo", etc.)
- **Categoría** (existe la columna pero casi nunca se completa)
- **Ingreso USD / Ingreso UYU** — columnas separadas por moneda
- **Egreso USD / Egreso UYU** — columnas separadas por moneda
- **Método de pago**: Efectivo, Tarjeta (TC / Tarjeta Brou), Transferencia, Cheque
- **Observaciones**

**Cómo está armada hoy (y por qué cuesta mantenerla en Excel):**
- Cada semana es un bloque de columnas nuevo (9 columnas), y dentro de cada bloque cada día es una sub-tabla con su propio encabezado, sus movimientos, y un resumen manual.
- El resumen de cada día/semana se calcula a mano con fórmulas tipo `Fondo Inicial + Ingresos - Egresos = Caja Final`, y la "Caja Final" hay que copiarla manualmente como "Fondo Inicial" del período siguiente.
- Se manejan **dos monedas en paralelo** (UYU y USD) sin convertir entre ellas — son dos cajas separadas que se controlan juntas.
- La "Categoría" casi no se usa, así que hoy no es posible sacar un reporte de "cuánto gastamos en sueldos" vs "cuánto en insumos", por ejemplo.

Esto confirma el problema que describiste: cada semana se repite la estructura a mano, y armar un resumen significa ir bloque por bloque.

---

## 3. Decisiones de arquitectura (confirmadas con el usuario)

| Decisión | Resultado |
|---|---|
| Dónde se usa | **Una sola computadora de la oficina**, estilo app de escritorio (no se necesita acceso remoto ni multi-dispositivo) |
| Quién lo usa | **Una sola persona** (vos) — no se necesita login ni permisos por usuario |
| Reportes fase 1 | **Resúmenes y totales en pantalla** (diario y semanal). Exportar a Excel/PDF queda para una fase posterior, pero el diseño lo va a permitir sin rehacer nada |

---

## 4. Alcance de la Fase 1

Reemplazar la hoja "Caja Diaria" por un programa que corre localmente en la computadora de la oficina, con:

1. **Registrar movimientos** (ingreso/egreso, en UYU o USD, con método de pago, concepto, categoría y observaciones) — sin tener que armar tablas nuevas cada semana.
2. **Saldo automático**: el sistema calcula solo el saldo de caja en cada momento (por moneda), sin que haya que copiar a mano la "Caja Final" de una semana al "Fondo Inicial" de la siguiente. Esto elimina el paso manual que más errores genera hoy.
3. **Resumen diario**: ver, para una fecha elegida, el detalle de movimientos + total de ingresos, egresos y saldo final, en UYU y en USD.
4. **Resumen semanal**: lo mismo pero agregado por semana (o por rango de fechas).
5. **Categorías reales**: para que el resumen pueda mostrar, por ejemplo, cuánto se gastó en sueldos/adelantos vs insumos vs combustible — algo que hoy el Excel no permite porque la categoría no se completa.

**Fuera de alcance en la Fase 1** (se evalúa después): exportar a Excel/PDF, gráficos, multiusuario, manejo de Adelantos/Liquidación/Bancos/Cheques.

---

## 5. Modelo de datos propuesto (Fase 1)

En vez de columnas separadas por moneda (Ingreso USD, Ingreso UYU, Egreso USD, Egreso UYU) como en el Excel, se usa una sola tabla de movimientos con tipo y moneda explícitos — más simple de consultar y de sumar.

### Tabla `movimientos`
| Campo | Tipo | Notas |
|---|---|---|
| id | entero, autoincremental | |
| fecha | fecha | |
| tipo | "ingreso" / "egreso" | |
| moneda | "UYU" / "USD" | |
| monto | decimal | siempre positivo; el signo lo da `tipo` |
| concepto | texto | igual que hoy (texto libre) |
| categoria_id | referencia a `categorias` | ver tabla abajo |
| metodo_pago | "Efectivo" / "Tarjeta" / "Transferencia" / "Cheque" | detectado de los datos reales |
| observaciones | texto, opcional | |
| creado_en | fecha/hora | para auditoría, no editable |

### Tabla `categorias`
Lista editable, para no repetir el problema de "categoría vacía". Se arranca con categorías sugeridas a partir de los conceptos que ya aparecen en tu Excel (las podés cambiar antes de codificar):

- **Ingresos:** Ventas y trabajos, Otros ingresos
- **Egresos:** Sueldos y adelantos, Viáticos, Insumos y suministros, Combustible, Papelería / administrativo, Alquiler local, Envíos, Retiros, Otros gastos

> 📝 Esta lista es una propuesta basada en lo que vi en tus conceptos (cubiertas, pinchazos, adelantos por nombre de empleado, viáticos, papelería, nafta de mandados, renta local). La confirmamos o ajustamos antes de empezar a programar.

### Saldo de caja (cálculo, no tabla)
El "Fondo Inicial" de un día/semana ya **no se escribe a mano**: se calcula automáticamente como el saldo acumulado de movimientos anteriores, por moneda. Si en algún momento el conteo físico de la caja no coincide con lo que dice el sistema (pasa en cualquier negocio), se puede agregar más adelante un movimiento tipo "Ajuste de caja" para corregirlo — no es necesario para arrancar.

**Efectivo separado de los demás métodos de pago (decisión confirmada):**
- El **"Saldo de Caja"** (lo que físicamente hay en la caja) se calcula **solo con movimientos en Efectivo** — es el único saldo que se "arrastra" de un día al siguiente, por moneda (UYU y USD).
- **Tarjeta, Transferencia y Cheque** no entran en ese saldo arrastrado (ese dinero no está físicamente en la caja). Se muestran como **totales informativos por período** (cuánto entró/salió por cada uno de esos métodos), sin acumularse como "fondo" de un día a otro.

---

## 6. Pantallas / funcionalidades de la Fase 1

1. **Pantalla principal / Inicio**: saldo de caja en efectivo (UYU y USD), + totales del día por Tarjeta, Transferencia y Cheque.
2. **Movimientos del día**: cargar, editar y borrar movimientos de la fecha seleccionada (cualquier método de pago).
3. **Reporte diario**: elegís una fecha → lista de movimientos + saldo de caja en efectivo (UYU/USD) + totales separados por Tarjeta, Transferencia y Cheque.
4. **Reporte semanal**: lo mismo agregado por semana o rango de fechas.
5. **Filtros básicos**: por categoría, por método de pago, por moneda.

---

## 7. Stack técnico propuesto

Dado que es **una sola computadora, un solo usuario, sin necesidad de internet**, se propone:

- **Backend:** Python + Flask (liviano, fácil de mantener)
- **Base de datos:** SQLite — un solo archivo, fácil de respaldar copiando un archivo
- **Interfaz:** páginas web simples (HTML/CSS/JS) servidas localmente, abiertas en el navegador con un acceso directo (doble clic) que arranca el programa — se siente "como una app" aunque por dentro use el navegador
- **Reportes:** tablas y totales calculados con consultas SQL directas, mostrados en pantalla

**Por qué esta opción:** es rápida de construir y mantener, no depende de instalar nada complejo, y deja la puerta abierta para más adelante (sin rehacer nada) agregar exportación a Excel/PDF o, si algún día se necesita, acceso desde el celular o desde otra computadora.

*Alternativa descartada por ahora:* envolver lo mismo en una ventana nativa de escritorio (con `pywebview`) en vez de abrir el navegador. Se puede agregar después como un detalle estético, sin cambiar nada del backend ni de la base de datos.

---

## 8. Qué mejora esto respecto al Excel actual

- No hay que armar una tabla nueva cada semana — los movimientos se cargan en una sola lista continua.
- El saldo de caja (en ambas monedas) se calcula solo, eliminando el paso de copiar "Caja Final" a "Fondo Inicial" a mano.
- Reportes diarios/semanales en un clic, en vez de ir bloque por bloque sumando manualmente.
- Categorías reales → se puede ver cuánto se gasta en sueldos, insumos, combustible, etc., algo que hoy no es posible.
- Base lista para crecer hacia Adelantos, Liquidación Semanal, Bancos y Cheques sin rehacer la base de datos.

---

## 9. Roadmap de fases futuras (alto nivel, a definir cuando lleguemos)

| Fase | Tema | Qué agregaría |
|---|---|---|
| 2 | Adelantos y Extras | Registro de adelantos por empleado y saldo pendiente |
| 3 | Liquidación Semanal | Cálculo de sueldo neto semanal restando adelantos |
| 4 | Combustible | Registro de consumo de combustible |
| 5 | Bancos | Control de cuentas y movimientos bancarios |
| 6 | Cheques | Control de cheques emitidos/recibidos y vencimientos |
| 7 | Exportación y extras | Exportar reportes a Excel/PDF, gráficos, respaldo automático |

---

## 10. Decisiones confirmadas (cierre de planeación)

1. **Categorías**: se arranca con la lista sugerida en la sección 5. Se podrán agregar/quitar más adelante sin problema.
2. **Saldo de caja**: se separa el **Efectivo** (saldo que se arrastra día a día) de **Tarjeta, Transferencia y Cheque** (totales informativos por período, sin arrastre).

Con esto, la planeación de la Fase 1 queda cerrada. El siguiente paso es arrancar la codificación: estructura del proyecto, base de datos SQLite, y la primera pantalla (carga de movimientos + saldo de caja en efectivo del día).
