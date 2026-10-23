# Design: Completar el onboarding de usuario

## Contexto técnico

La spec aprobada cubre el recorrido guiado, validación, resultados de KYC, activación de wallet e instrumentación de onboarding. Los contratos disponibles son los endpoints simulados W1 descritos en `docs/mockups/W1-Registro-y-activación.md`; el mock acepta únicamente documentos ficticios `TEST-*`, mantiene estado en memoria y no calcula duración, MAU, CAC ni atribución.

Este checkout contiene el harness CrewAI, OpenSpec y documentación del mock, pero no la aplicación wallet consumidora. Por tanto, este diseño fija límites de integración y preservación de contratos; no asigna clases, framework, persistencia ni proveedor analítico que no estén presentes.

## Goals

- Permitir que la aplicación consumidora implemente el flujo guiado, validación accionable y presentación de estados KYC.
- Habilitar el punto de entrada de pagos solo tras una activación exitosa; la wallet creada permanece con saldo cero.
- Hacer observables inicio, pasos y cierre del onboarding, además de permitir los reportes mensuales definidos por la spec.
- Mantener compatibilidad con los contratos publicados del mock W1 y cambios pequeños, caracterizados y reversibles.

## Non-goals

- Implementar onboarding, APIs, persistencia o analítica en este repositorio, el harness CrewAI o el mock.
- Agregar o cambiar endpoints W1-W6, validar documentos reales, prevenir registros duplicados o mover dinero real.
- Definir requisitos regulatorios, documentos reales, pasos obligatorios, taxonomía analítica, proveedor o tecnología de almacenamiento.
- Garantizar los resultados de negocio de duración, MAU o CAC; la solución solo debe permitir medirlos.

## Contratos protegidos

- `POST /kyc/verifications` acepta `documentType: TEST`, `document` con prefijo `TEST-` y escenarios `APPROVED`, `REJECTED`, `MANUAL_REVIEW` o `UNAVAILABLE`.
- `APPROVED` activa una wallet con saldo cero; `MANUAL_REVIEW` deja la cuenta `PENDING` y abre soporte; `REJECTED` no habilita pagos; `UNAVAILABLE` responde `503` sin crear wallet.
- La consulta KYC usa el ID de verificación, distinto de `wallet_id`. Se preservan rutas, métodos, campos y respuestas documentadas por W1.
- Repetir una decisión final conserva el resultado; intentar cambiarla devuelve `409 DECISION_CONFLICT`.
- No solicitar ni enviar documentos reales. No atribuir al mock la duración, MAU, CAC o el gasto de adquisición.

## Componentes afectados

- **Aplicación cliente consumidora (fuera de este checkout):** secuencia y paso actual, validación, mensajes, estados KYC y navegación al punto de entrada de pagos.
- **Integración KYC/wallet (fuera de este checkout):** cliente HTTP que invoca los endpoints W1 y traduce sus resultados a estados visibles sin alterar el contrato.
- **Instrumentación y salida analítica (fuera de este checkout):** eventos correlacionados por recorrido y agregados para las métricas acordadas.
- **Mock W1 y harness CrewAI:** contratos de referencia y preparación de escenarios; no requieren cambios para esta historia.

## Decisiones técnicas y alternativas

### Integración con KYC

**Decisión:** consumir los endpoints W1 existentes desde la aplicación objetivo y representar sus estados en el flujo cliente. Mantener el mock como dependencia simulada de prueba.

**Alternativas consideradas:** agregar un endpoint de onboarding al mock, mover el flujo al harness CrewAI o introducir un backend nuevo. Se descartan dentro de este alcance: ampliarían los contratos o asignarían comportamiento de producto a componentes que no son la aplicación consumidora.

### Instrumentación

**Decisión:** la aplicación consumidora emite los eventos de inicio, finalización de paso y cierre; la salida mensual también es responsabilidad de la aplicación o de su infraestructura analítica existente. No almacenar ni calcular estas métricas en el mock.

**Alternativas consideradas:** derivar duración/MAU/CAC desde las respuestas del mock o añadir endpoints analíticos al mock. Se descartan porque el mock no expone esos datos y la spec asigna esa responsabilidad a la aplicación.

**Pendiente de selección:** tecnología, esquema de eventos, persistencia y mecanismo de reporte. No se puede elegir sin identificar el repositorio consumidor y su infraestructura actual.

## Estrategia incremental

1. Identificar el repositorio consumidor y su arquitectura existente; resolver con Producto y Cumplimiento los pasos/datos obligatorios y sus validaciones.
2. Acordar la frontera temporal de inicio/fin, la identidad de correlación del recorrido, la definición de usuario activo/MAU y la fuente/regla de atribución CAC.
3. Añadir pruebas de caracterización de los contratos y estados actuales antes de cambiar comportamiento crítico.
4. Implementar secuencia, paso actual y validación como un primer cambio acotado, sin llamadas adicionales al mock.
5. Integrar creación/consulta KYC y representar `APPROVED`, `MANUAL_REVIEW`, `REJECTED` y `UNAVAILABLE`; habilitar pagos solo para wallet activa.
6. Instrumentar eventos desde la aplicación y añadir el reporte mensual una vez acordadas sus definiciones. Mantener cada tramo revisable y revertible por separado.

## Pruebas de caracterización previas

- Capturar método, ruta, cuerpos, campos de respuesta y códigos HTTP de creación/consulta KYC, decisión, wallet y soporte según los mockups.
- Verificar los cuatro escenarios KYC, saldo inicial cero, `503` sin wallet, `PENDING` con caso de soporte y el rechazo de pago para wallets rechazadas (`409`).
- Verificar repetición idempotente de decisiones y conflicto (`409 DECISION_CONFLICT`) al intentar cambiar una decisión final.
- En la aplicación consumidora, registrar el comportamiento actual de navegación, validación, estados y acceso a pagos para proteger compatibilidad visible antes de modificarlo.
- Caracterizar los eventos y reportes existentes, si los hay, antes de añadir instrumentación; comprobar que los eventos de un flujo comparten correlación y respetan las fronteras temporales acordadas.

## Riesgos / trade-offs

- No disponer del repositorio consumidor impide seleccionar componentes concretos, estimar el trabajo de código o confirmar sus mecanismos existentes de feature flags, analytics y rollback.
- Implementar antes de que Producto/Cumplimiento definan los pasos puede inventar requisitos. La spec no resuelve esos campos.
- La frontera de eventos y la atribución afectan la comparabilidad de duración y CAC; sin definiciones acordadas, las métricas no son verificables.
- El mock es simulado y en memoria; sus pruebas no demuestran comportamiento de KYC real ni persistencia productiva.
- Mantener la analítica en la aplicación preserva la responsabilidad especificada, pero deja abierta la elección de su infraestructura hasta inspeccionar el repositorio objetivo.

## Rollback

- Mantener los cambios en la aplicación consumidora divididos por flujo, integración e instrumentación, con commits/revisiones independientes.
- Si existe un mecanismo de feature flag en la aplicación objetivo, usarlo para deshabilitar el nuevo recorrido; no crear uno en este checkout.
- Si no existe, revertir el tramo de UI/integración afectado en el repositorio consumidor y conservar intactos los endpoints del mock.
- Si falla el reporte, retirar o deshabilitar la vista de métricas por separado; no borrar eventos históricos ni reiniciar datos compartidos del mock como mecanismo de rollback.

## Decisiones abiertas

- Repositorio y arquitectura de la aplicación consumidora.
- Pasos y datos obligatorios, reglas de validación y mensajes aprobados por Producto/Cumplimiento.
- Frontera temporal de inicio/fin, definición de usuario activo/MAU, correlación de eventos y fuente/reglas de CAC.
- Infraestructura analítica existente, retención y destino del reporte mensual.
- Disponibilidad de feature flags u otro mecanismo de reversión en la aplicación consumidora.

La implementación debe detenerse hasta resolver las decisiones que condicionan los requisitos y revisar este diseño en el repositorio consumidor. No se crea un ADR separado: este diseño no selecciona una tecnología ni introduce una decisión arquitectónica irreversible.