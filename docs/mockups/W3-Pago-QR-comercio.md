# W3 · Pago QR comercio

El QR identifica al comercio y puede incluir un monto fijo. Este flujo agrega la lectura y validación del QR antes de crear el mismo tipo de pago que usa W2.

## Flujo de pago con QR

1. Envía `POST /qrs` con `{"merchantId":"merchant-demo","amountCents":2200}` para crear un QR de S/ 22.00. Guarda su ID y el texto `payload` devuelto.
2. Simula la lectura con `POST /qrs/resolve` y un cuerpo `{"payload":"PAYLOAD_DEVUELTO"}`. Reemplaza el texto por el valor del paso anterior.
3. Muestra el comercio y el monto antes de pedir la confirmación del usuario.
4. Envía `POST /payments` con una nueva `Idempotency-Key` y el cuerpo `{"walletId":"wallet-demo","recipient":"merchant-demo","amountCents":2200,"qrId":"ID_DEL_QR","scenario":"APPROVED"}`. Reemplaza `ID_DEL_QR` por el ID creado.
5. Entrega el evento del pago y consulta su estado y comprobante como en W2.

## Qué debes comprobar

- Para un QR de monto abierto, omite `amountCents` al crearlo. El usuario ingresa el monto antes de pagar.
- Para probar un QR vencido, créalo con `expiresInSeconds: 0`. Resolverlo o pagar con él devuelve `410`.
- Cambiar el monto fijo o el comercio al pagar devuelve `409`. La interfaz debe pedir un QR válido.
- Un payload con formato desconocido devuelve `400`. Un ID de QR inexistente devuelve `404`.

El servicio devuelve texto con formato `qrmock:...`. Tu aplicación puede convertirlo en una imagen QR. El mock no incluye generador de imágenes, cámara ni formato bancario EMVCo. Envía `qrId` al pagar para que la API valide la relación con el QR.

## APIs de esta historia

### `POST /qrs`

Crea texto qrmock:ID para merchant-demo. Sin amountCents o con null, el monto es abierto. Con monto, el pago debe respetarlo. expiresInSeconds predeterminado 300, rango entero 0..86400; 0 vence inmediatamente. Comercio desconocido: 404 MERCHANT_NOT_FOUND; TTL inválido: 400 INVALID_TTL. No genera imagen ni valida EMVCo.

Campos del cuerpo JSON:

- `merchantId`: string, opcional. Comercio de prueba. Predeterminado merchant-demo. Valores: merchant-demo.
- `amountCents`: integer, opcional. Importe en céntimos de PEN. 1500 = S/ 15.00.
- `expiresInSeconds`: integer, opcional. Vigencia en segundos. 0 vence inmediatamente.

Respuestas HTTP: `201`, `400`, `404`, `413`, `429`.

Campos de respuesta: `id`, `payload`, `amountCents`, `currency`.

### `POST /qrs/resolve`

Resuelve el payload y devuelve comercio y monto, null si abierto. No crea pagos. 400 INVALID_QR por formato desconocido; 404 NOT_FOUND por ID desconocido; 410 QR_EXPIRED por vencimiento. Usa el ID devuelto al crear el QR como qrId del pago.

Campos del cuerpo JSON:

- `payload`: string, obligatorio. Texto qrmock:ID devuelto por POST /qrs.

Respuestas HTTP: `200`, `400`, `404`, `410`, `413`, `429`.

Campos de respuesta: `merchantId`, `merchantName`, `amountCents`, `currency`.

## Material relacionado

[Leer la historia de usuario](/dia-05/packages/user-stories/merchant-qr-payment-status-visibility.sp.html)

[Conectar y confirmar pagos](/dia-04/mocks/)

[Controles para preparar escenarios](/dia-04/mocks/controles.html)

[Cobertura frente a los criterios del reto](/dia-04/mocks/alcance.html)
