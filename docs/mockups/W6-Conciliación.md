# W6 · Conciliación

La conciliación comprueba que la wallet, el reporte del proveedor y los asientos contables registren operaciones consistentes. Úsala para construir una vista operativa que muestre coincidencias y diferencias que requieren revisión.

`GET /settlements` devuelve el reporte simulado del proveedor. `GET /ledger` devuelve los asientos contables, es decir, los registros de los movimientos. `GET /reconciliations/incidents` permite consultar las incidencias detectadas.

## Flujo de conciliación

1. Crea y confirma un pago como en W2.
2. Envía `POST /reconciliations`. Con los registros consistentes, el resultado es `MATCHED`.
3. Envía `POST /control/settlements` con `{"paymentId":"ID_DEL_PAGO","mode":"AMOUNT","amountCents":1600}`. Usa el ID del pago de S/ 15.00 para simular que el proveedor reporta S/ 16.00.
4. Ejecuta otra vez `POST /reconciliations`. El resultado es `DIFFERENCES`. Consulta `GET /reconciliations/incidents` para ver el detalle de la diferencia.
5. Elimina la alteración con `POST /control/settlements` y `{"paymentId":"ID_DEL_PAGO","mode":"CLEAR"}`. Vuelve a conciliar para marcar la incidencia como resuelta.

## Otras diferencias que puedes simular

- `MISSING` quita el pago del reporte del proveedor.
- `DUPLICATE` agrega una fila duplicada al reporte.
- `ORPHAN`, con un ID de pago nuevo y un monto, agrega una operación al reporte que no existe en la wallet.
- Un callback sin entregar deja una diferencia entre el estado del proveedor y el de la wallet. Confirma el pago y vuelve a conciliar para comprobar la resolución.

Estos controles alteran el reporte de prueba, sin cambiar la wallet ni sus asientos. Repetir la conciliación conserva la incidencia por operación y motivo en lugar de duplicarla. La conciliación detecta diferencias; no mueve dinero ni corrige saldos automáticamente. El reporte incluye todos los datos del grupo, sin cierres diarios ni filtros de fecha.

## APIs de esta historia

### `GET /ledger`

Lista asientos de partida doble del grupo. Incluye dos asientos FUNDING de la semilla. PAYMENT resta a la wallet y suma a clearing; REVERSAL hace lo contrario. No modifica saldos.

Respuestas HTTP: `200`.

Respuesta: lista de objetos con `id`, `operation`, `kind`, `account`, `amount`. Una lista vacía se representa como `[]`.

### `GET /settlements`

Devuelve el reporte completo del proveedor con las alteraciones configuradas en /control/settlements. Incluye pagos pendientes, rechazados y reversados. No concilia ni cambia la wallet.

Respuestas HTTP: `200`.

Respuesta: lista de objetos con `id`, `amount`, `status`. Una lista vacía se representa como `[]`.

### `GET /reconciliations/incidents`

Lista incidencias OPEN y RESOLVED del último proceso de conciliación. La misma combinación de recurso y motivo conserva ID en ejecuciones posteriores. Solo POST /reconciliations recalcula su estado.

Respuestas HTTP: `200`.

Respuesta: lista de objetos con `id`, `payment_id`, `reason`, `status`. Una lista vacía se representa como `[]`.

### `POST /reconciliations`

Compara todos los pagos del grupo con reporte, ledger y saldos. Devuelve MATCHED con differences:[] o DIFFERENCES con incidencias OPEN. Detecta faltantes, duplicados, montos, estados, asientos y balances. Repetir no duplica incidencias. Corregir la causa y volver a ejecutar marca las anteriores RESOLVED. No mueve dinero ni corrige saldos. No requiere cuerpo.

Respuestas HTTP: `200`, `400`, `413`, `429`.

Campos de respuesta: `status`, `differences`.

## Material relacionado

[Leer la historia de usuario](/dia-05/packages/user-stories/operations-transaction-reconciliation.sp.html)

[Conectar y confirmar pagos](/dia-04/mocks/)

[Controles para preparar escenarios](/dia-04/mocks/controles.html)

[Cobertura frente a los criterios del reto](/dia-04/mocks/alcance.html)
