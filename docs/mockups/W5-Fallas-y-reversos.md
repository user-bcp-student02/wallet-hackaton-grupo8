# W5 · Fallas y reversos

Esta sección permite probar qué ocurre cuando falta una confirmación, el proveedor falla o necesitas devolver un pago aprobado. Un error de comunicación no demuestra que el pago haya fallado.

## Recuperar un resultado incierto

1. Crea un pago con `scenario: TIMEOUT_AFTER_PROCESSING` y una nueva `Idempotency-Key`. Recibirás `504` con `paymentId`, aunque el proveedor ya procesó el pago.
2. Guarda ese `paymentId` y envía `POST /payments/{id}/resolve`. Esta llamada consulta al proveedor y actualiza el pago sin crear otro cobro.
3. Consulta `GET /payments/{id}` para mostrar el resultado confirmado. Si necesitas reenviar la creación original, conserva su clave y su cuerpo como explica W4.

## Probar un pendiente o una caída

- Con `PENDING`, la consulta `/resolve` devuelve `202` y abre un caso de soporte. Consulta `GET /support/cases` para ver el seguimiento.
- Para finalizar el pendiente, envía `POST /control/provider/{id}/complete` con `{"status":"SUCCEEDED"}` o `{"status":"REJECTED"}`. Usa el ID del pago y entrega el evento generado.
- Si simulaste un callback perdido al no entregarlo, puedes usar `/resolve` para consultar el resultado o entregar el evento después.
- `PROVIDER_ERROR` devuelve `503` antes de procesar. No crea una operación ni reserva saldo.

## Devolver un pago aprobado

1. Confirma un pago hasta que esté en `SUCCEEDED`.
2. Envía `POST /payments/{id}/reversals`. Guarda el ID del reverso devuelto.
3. Busca el evento de reverso en `GET /control/events` y entrégalo. La wallet devuelve el saldo y registra asientos que compensan el pago original.
4. Consulta `GET /reversals/{id}` con el ID del reverso y `GET /payments/{id}` con el ID del pago para comprobar el resultado.

Una aprobación tardía después de resolver el pago y completar su reverso se acepta sin nuevos cargos ni cambio de estado. El reverso es completo y único por pago. Permanece pendiente hasta entregar su evento. Los escenarios avanzan mediante llamadas manuales; el `504` simulado no representa una espera real de red.

## APIs de esta historia

### `GET /reversals/{id}`

Consulta usando el ID rev del reverso. PENDING espera confirmación y SUCCEEDED significa saldo devuelto. No usar el ID pay del pago en esta ruta. Inexistente: 404.

Respuestas HTTP: `200`, `404`.

Campos de respuesta: `id`, `payment_id`, `status`.

### `POST /payments/{id}/resolve`

Consulta al proveedor sin crear otro cobro. Si sigue PENDING devuelve 202 con escalated:true y abre un único caso de soporte. Si ya terminó, aplica el resultado y devuelve 200 con el pago. Repetir conserva el resultado. También puede completar un reverso pendiente. No requiere cuerpo ni Idempotency-Key. Pago inexistente: 404.

Respuestas HTTP: `200`, `202`, `404`, `409`, `400`, `413`, `429`.

Campos de respuesta: `id`, `wallet_id`, `recipient`, `amount`, `status`, `scenario`, `idem`, `fingerprint`.

### `POST /payments/{id}/reversals`

Solicita un reverso completo de un pago SUCCEEDED. Devuelve 202 con reverso PENDING, cambia el proveedor a REVERSED y crea el evento REVERSED. Hasta confirmar, la wallet conserva el cargo. Repetir devuelve 200 con el mismo reverso. Otro estado inicial: 409 PAYMENT_NOT_REVERSIBLE. Pago inexistente: 404. No requiere cuerpo ni Idempotency-Key.

Respuestas HTTP: `200`, `202`, `404`, `409`, `400`, `413`, `429`.

Campos de respuesta: `id`, `payment_id`, `status`.

### `GET /support/cases`

Lista casos OPEN y RESOLVED por revisión KYC o resultado de pago pendiente. La decisión KYC o confirmación del pago resuelve el caso. No envía notificaciones externas ni ofrece edición directa.

Respuestas HTTP: `200`.

Respuesta: lista de objetos con `id`, `resource`, `reason`, `status`. Una lista vacía se representa como `[]`.

## Material relacionado

[Leer la historia de usuario](/dia-05/packages/user-stories/payment-failure-reversal-handling.sp.html)

[Conectar y confirmar pagos](/dia-04/mocks/)

[Controles para preparar escenarios](/dia-04/mocks/controles.html)

[Cobertura frente a los criterios del reto](/dia-04/mocks/alcance.html)
