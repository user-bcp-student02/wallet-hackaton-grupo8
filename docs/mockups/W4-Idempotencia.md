# W4 · Idempotencia

La idempotencia evita un segundo cobro cuando el usuario pulsa dos veces o la aplicación reintenta una petición sin haber recibido la respuesta. Se aplica a `POST /payments` con el encabezado `Idempotency-Key`.

## Cómo probar los reintentos

1. Crea un pago con `Idempotency-Key: reintento-001` y guarda el ID devuelto.
2. Repite la petición con la misma wallet, clave y cuerpo. La API devuelve `200` con la operación existente y el mismo ID.
3. Conserva la clave y cambia el monto o el destinatario. La API devuelve `409`, porque la clave ya identifica otro contenido.
4. Entrega dos veces el mismo evento del pago. La segunda entrega indica `duplicate: true` y no agrega otro cargo ni nuevos asientos en `GET /ledger`.

## Qué debe hacer tu aplicación

- Genera una clave por intención de pago y consérvala durante los reintentos de esa operación.
- Usa una clave nueva para un pago nuevo. Si generas otra clave al reintentar, la API puede interpretar que quieres crear otra operación.
- Conserva también el cuerpo original, incluido `scenario` y `qrId` si lo enviaste. Cambiar esos campos con la misma clave produce un conflicto.
- Prueba solicitudes simultáneas con la misma wallet, clave y cuerpo. Debe existir una sola operación.

La clave se asocia a la wallet dentro del grupo. `scenario` elige el resultado simulado; no sustituye la clave. El reinicio del grupo borra las claves y los pagos guardados.

## APIs de esta historia

### `POST /callbacks/payments`

Entrega un evento existente mediante eventId. Primera entrega: duplicate:false y payment; repetición del mismo evento: solo duplicate:true. El éxito descuenta saldo y crea dos asientos; rechazo libera reserva; reverso devuelve saldo y compensa asientos. Una aprobación tardía de un pago ya REVERSED se acepta sin cambiar saldo ni estado. Evento inexistente: 404; transición incompatible: 409 INVALID_STATE_TRANSITION. No verifica firmas ni recibe payloads externos.

Campos del cuerpo JSON:

- `eventId`: string, obligatorio. ID evt de un evento devuelto por GET /control/events.

Respuestas HTTP: `200`, `400`, `404`, `409`, `413`, `429`.

Campos de respuesta: `duplicate`, `payment`.

## Material relacionado

[Leer la historia de usuario](/dia-05/packages/user-stories/payment-idempotency-protection.sp.html)

[Conectar y confirmar pagos](/dia-04/mocks/)

[Controles para preparar escenarios](/dia-04/mocks/controles.html)

[Cobertura frente a los criterios del reto](/dia-04/mocks/alcance.html)
