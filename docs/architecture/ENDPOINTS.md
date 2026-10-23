# Endpoints W1 · Registro y activación

Este documento inventaría los contratos existentes del mock que usa W1. No define endpoints nuevos ni describe una implementación local: este checkout no contiene la aplicación wallet consumidora.

## Impacto

La aplicación consumidora usa los endpoints de KYC y wallet para crear y consultar el registro, mostrar su resultado y habilitar pagos solo cuando la cuenta está activa. En revisión manual puede consultar los casos de soporte. La instrumentación y las métricas de onboarding pertenecen a la aplicación; no son capacidades del mock.

## Componentes afectados

- Cliente HTTP W1 de la aplicación consumidora, que no está presente en este checkout.
- Mock documentado en [W1 Registro y activación](../mockups/W1-Registro-y-activación.md) y [W5 Fallas y reversos](../mockups/W5-Fallas-y-reversos.md) para la lista de casos de soporte.
- No se propone modificar el harness CrewAI ni agregar endpoints al mock.

## Contratos protegidos

Las rutas se documentan sin prefijo de host o versión porque el material del mock no define uno aquí. Se deben conservar métodos, cuerpos, campos de respuesta y códigos HTTP existentes.

| Método y ruta | Uso | Solicitud | Respuesta documentada |
| --- | --- | --- | --- |
| `POST /kyc/verifications` | Crear verificación y wallet | `documentType` obligatorio, solo `TEST`; `document` obligatorio con prefijo `TEST-`; `scenario` opcional: `APPROVED` (predeterminado), `REJECTED`, `MANUAL_REVIEW` o `UNAVAILABLE`. | `201`, `400`, `503`, `413`, `429`. Campos: `id`, `wallet_id`, `scenario`, `status`. `UNAVAILABLE` devuelve `503 KYC_UNAVAILABLE` y no crea wallet. |
| `GET /kyc/verifications/{id}` | Consultar una verificación por su ID KYC, distinto de `wallet_id` | `id` de la verificación en la ruta | `200`, `404`. Campos: `id`, `wallet_id`, `scenario`, `status`. |
| `POST /kyc/verifications/{id}/decision` | Resolver una verificación `PENDING` | `decision`: obligatorio, `ACTIVE` o `REJECTED` | `200`, `400`, `404`, `409`, `413`, `429`. Campos: `id`, `wallet_id`, `scenario`, `status`. Repetir la decisión final conserva el resultado; cambiarla devuelve `409 DECISION_CONFLICT`. |
| `GET /wallets/{id}` | Consultar estado y saldos | `id` de wallet en la ruta | `200`, `404`. Campos: `id`, `status`, `balance`, `reserved`, `available`, `currency`. Importes en céntimos; `available = balance - reserved`. Una wallet creada por onboarding empieza con saldo cero. |
| `GET /support/cases` | Consultar casos abiertos y resueltos, incluidos los de revisión KYC | Sin cuerpo documentado | `200`. Lista de objetos con `id`, `resource`, `reason`, `status`; una lista vacía se representa como `[]`. |

## Estrategia incremental

1. En la aplicación consumidora, caracterizar estos contratos antes de cambiar el cliente HTTP.
2. Integrar las rutas existentes sin ampliar el mock ni asumir campos no documentados.
3. Mantener el envío restringido a documentos ficticios `TEST-*`; no solicitar ni enviar documentos reales.
4. Implementar progreso, validación, estados y analítica en la aplicación consumidora, una vez identificada y con las definiciones de Producto y Cumplimiento acordadas.

## Pruebas necesarias

- Contrato de creación KYC para `APPROVED`, `REJECTED`, `MANUAL_REVIEW` y `UNAVAILABLE`, incluidos campos, códigos y saldo inicial.
- Consulta de verificación y wallet, incluyendo IDs inexistentes y separación entre `id` KYC y `wallet_id`.
- Decisión manual: decisión válida, repetición idempotente, decisión inválida y conflicto al cambiar una decisión final.
- Consulta de casos de soporte para revisión manual.
- Pruebas de flujo que impidan pagos para cuentas rechazadas y que no traten `PENDING` o `UNAVAILABLE` como activas.
- Pruebas negativas que aseguren el uso exclusivo de documentos ficticios `TEST-*`.

## Riesgos / trade-offs

- Son contratos de un mock simulado; no validan documentos reales ni representan movimientos de dinero reales.
- La ruta no documenta una respuesta para cada posible error de validación más allá de los códigos listados; no se deben inventar cuerpos de error.
- Los pasos y datos obligatorios del onboarding, la frontera temporal de analítica y la atribución de adquisición siguen dependiendo de acuerdos fuera del contrato HTTP.
- La aplicación consumidora y su URL base no están identificadas en este checkout; no se puede asignar aquí configuración o código cliente.

## Decisiones abiertas

- Identificar el repositorio y los componentes de la aplicación consumidora.
- Definir con Producto y Cumplimiento los pasos y datos que se envían en cada paso; el contrato publicado solo define los campos KYC anteriores.
- Acordar las definiciones de eventos, duración, MAU y atribución de CAC en la aplicación, sin trasladar esas responsabilidades al mock.
- Confirmar URL base y configuración de entorno del mock en el repositorio consumidor.