# APIs mock del Lab 4

Usa estos mocks para desarrollar y probar la wallet con datos ficticios. Puedes elegir respuestas aprobadas, rechazadas, pendientes y fallas del proveedor. No se mueve dinero ni se conecta con bancos.

## Cómo leer esta guía

Cada sección W1–W6 corresponde a una historia del reto. W1 activa la wallet; W2 confirma pagos; W3 agrega el QR; W4 evita duplicados; W5 resuelve fallas y reversos; W6 comprueba que los registros coincidan.

Un endpoint es una ruta de la API. `GET` consulta datos y `POST` crea una operación o ejecuta una acción. Todas las rutas de esta guía se agregan a la URL base del grupo. Por ejemplo, para el Grupo 1, `GET /payments` significa `GET {URL_BASE}/payments`.

Los campos `{id}` se reemplazan por el identificador devuelto por la API, sin las llaves. Guarda los IDs de la wallet, pago, QR, reverso y evento por separado. Cada ruta espera el ID del recurso que nombra.

Usa siempre la URL base que muestra el selector. En el portal local apunta a `http://127.0.0.1:8789/groups/N`; en el publicado apunta al servicio remoto. Para los ejemplos de terminal, define `URL_BASE` con la dirección copiada de tu grupo.

## Probar con Swagger UI

Selecciona tu grupo arriba y pulsa Abrir Swagger UI. Se abre una pestaña independiente dedicada a Swagger UI. La documentación permanece en esta pantalla. El contrato del grupo se carga directamente, separado en W1–W6. Despliega una operación, pulsa Try it out, completa los datos y luego Execute para ver la respuesta real del mock. No necesitas copiar el JSON ni usar un editor.

- [Abrir Swagger UI](/dia-04/mocks/swagger.html)

Swagger UI permite enviar peticiones desde el navegador. OpenAPI es el archivo JSON que describe las rutas, los campos y los códigos HTTP. Usa el contrato de tu grupo para que las pruebas apunten a sus datos. El visor de flujos explica los escenarios, pero no ejecuta llamadas.

## Simular latencia

El header opcional `X-Mock-Latency-Ms` añade una demora a la respuesta de una petición. Acepta un entero de `0` a `5000` milisegundos. Si lo omites, la demora añadida es cero. Un segundo equivale a `1000` ms.

```bash
curl "${URL_BASE}/wallets/wallet-demo" \
  -H 'X-Mock-Latency-Ms: 1000'
```

También puedes elegir la latencia junto al grupo antes de abrir Swagger, o escribir el header en los parámetros de cada operación. La respuesta devuelve el valor aplicado en `X-Mock-Latency-Ms`. La demora se añade al tiempo de red y procesamiento. Afecta solo esa respuesta, incluidos los errores; no modifica el escenario ni la configuración del grupo. Un valor fuera del rango o no entero devuelve `400 INVALID_MOCK_LATENCY` antes de ejecutar la operación. Las solicitudes OPTIONS no se demoran.

## API publicada

- [Comprobar disponibilidad de la API](https://bcp-wallet-mock.yefri.workers.dev/health)
- [Abrir OpenAPI del servicio publicado](https://bcp-wallet-mock.yefri.workers.dev/openapi.json)
- [Explorar flujos por historia y escenario](/dia-04/mocks/flows.html)
- [Descargar servicio local y demo opcionales](/dia-04/mocks/wallet-mock.zip)

No necesitas instalar Python para consumir las APIs publicadas. Selecciona tu grupo en el menú de arriba. Hay exactamente ocho grupos, del 1 al 8, con URLs fijas. Todos los integrantes del mismo grupo comparten pagos, saldo, eventos y conciliación. Reiniciar un grupo no afecta a los demás.

## Probar desde Postman o tu frontend

1. Selecciona Grupo 1 hasta Grupo 8 y copia la URL base que aparece, La dirección ya incluye `/groups/N`.
2. Importa el OpenAPI de tu grupo en Postman o Swagger Editor. Su servidor ya apunta a la URL fija de ese grupo.
3. Envía `POST {URL_BASE}/payments` con encabezados `Content-Type: application/json` e `Idempotency-Key: prueba-001`.
4. Usa este cuerpo: `{"walletId":"wallet-demo","recipient":"contact-demo","amountCents":1500,"scenario":"APPROVED"}`.
5. Consulta `GET {URL_BASE}/control/events` y copia el `id` del evento del pago.
6. Envía `POST {URL_BASE}/callbacks/payments` con `{"eventId":"ID_DEL_EVENTO"}`.
7. Consulta `GET {URL_BASE}/payments` para ver el pago aprobado. Cambia a `REJECTED` con una nueva operación para probar el rechazo.

Consulta `GET /groups` en la raíz del servicio seleccionado (sin el sufijo `/groups/N`) para ver los ocho grupos con sus campos `groupId`, `name`, `baseUrl` y `openapiUrl`. No se crean sesiones aleatorias ni grupos adicionales. El servicio tiene CORS habilitado para aplicaciones web, sin cookies ni inicio de sesión de GitHub.

Las seis historias comparten 27 rutas y 28 operaciones del mock. El servicio remoto agrega el listado de los ocho grupos. El contrato documenta entradas, códigos HTTP y campos de respuesta. La referencia al final explica cada operación, sus efectos y sus errores.

## Cómo se confirma un pago

Crear un pago y confirmar su resultado son dos pasos distintos. `POST /payments` suele responder `202` con el pago en `PENDING`. En ese momento hay una reserva de saldo. La aplicación aún debe mostrar que el pago está pendiente.

El campo `scenario` elige qué hará el proveedor simulado. `APPROVED` genera un resultado exitoso en el proveedor, pero la wallet lo confirma cuando recibe el evento. Un callback es la llamada que entrega ese resultado a la wallet.

Para simular esa entrega, consulta `GET /control/events`, identifica el evento de tu pago y envía su `id` como `eventId` a `POST /callbacks/payments`. También puedes usar `POST /control/events/{id}/deliver`. Son dos formas de entregar el mismo evento; basta con una.

Después consulta `GET /payments/{id}`. Muestra el comprobante cuando el pago esté en `SUCCEEDED`. Para un resultado rechazado verás `REJECTED`. Si el evento no llega, W5 explica cómo consultar al proveedor.

## Elegir una historia

Cada historia tiene su propia página con el flujo, las comprobaciones y la referencia de sus APIs.

- [W1 · Registro y activación](/dia-04/mocks/w1.html)
- [W2 · Pago a contacto](/dia-04/mocks/w2.html)
- [W3 · Pago QR comercio](/dia-04/mocks/w3.html)
- [W4 · Idempotencia y callbacks](/dia-04/mocks/w4.html)
- [W5 · Fallas y reversos](/dia-04/mocks/w5.html)
- [W6 · Conciliación](/dia-04/mocks/w6.html)
- [Controles del mock](/dia-04/mocks/controles.html)
- [Cobertura y límites](/dia-04/mocks/alcance.html)

## Consultas del servicio

### `GET /health`

Comprueba disponibilidad y almacenamiento en memoria. No modifica datos. El servicio raíz remoto incluye enlaces a grupos y OpenAPI; la URL del grupo informa su entorno.

Respuestas HTTP: `200`.

Campos de respuesta: `status`, `storage`, `environment`, `startedAt`, `service`, `groups`, `openapi`.

### `GET /scenarios`

Lista las opciones exactas de scenario para KYC, pagos y alteraciones del reporte. No avanza escenarios ni modifica datos.

Respuestas HTTP: `200`.

Campos de respuesta: `kyc`, `payments`, `settlements`.

### `GET /openapi.json`

Devuelve este contrato. En cloud, el contrato raíz ofrece ocho servidores y el contrato del grupo ofrece solo su URL. Importa el del grupo en Postman o Swagger.

Respuestas HTTP: `200`.

Campos de respuesta: `openapi`, `info`, `paths`, `servers`.
