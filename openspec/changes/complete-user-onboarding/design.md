# Design: Completar el onboarding de usuario

## Contexto técnico

La spec aprobada cubre el recorrido guiado, validación, resultados de KYC, activación de wallet e instrumentación. La aplicación consumidora está en `hackaton-group-8/`: Quarkus/Java 21, Angular, H2 y pruebas JUnit/Playwright. Los contratos simulados W1 están documentados en `docs/mockups/W1-Registro-y-activación.md`; el mock acepta únicamente documentos `TEST-*`, mantiene estado en memoria y no calcula duración, MAU, CAC ni atribución.

La aplicación existente usa `/api/onboarding/*`, escenarios `APPROVED/PENDING/DECLINED` y acredita S/ 500 a las altas aprobadas. Esto no cumple el contrato aprobado, que exige consumir W1 y mantener saldo cero. No hay URL de un mock W1 desplegado en este entorno. El cliente usará `W1_BASE_URL` obligatoria en ejecución; las pruebas reproducibles usarán un servidor local de contrato derivado de los campos y respuestas publicados. Esas pruebas no se describirán como integración con un W1 desplegado.

Producto/Cumplimiento confirmaron el flujo existente: identidad ficticia (nombre, alias y celular), consentimiento para datos sintéticos, confirmación con PIN de seis dígitos y KYC. También confirmaron las definiciones analíticas existentes: inicio en `onboarding_started`, cierre en `onboarding_completed`, correlación por UUID local, duración desde inicio hasta finalización, y MAU como pagadores únicos con un pago exitoso por mes calendario de Perú. Adquisición confirmó gasto mensual por campaña registrado por Operaciones, campaña capturada al alta y CAC como gasto atribuido dividido entre nuevas wallets activadas. Los datos siguen siendo sintéticos; estas definiciones no prueban metas de negocio.

## Goals

- Permitir que la aplicación consumidora implemente el flujo guiado, validación accionable y presentación de estados KYC.
- Habilitar el punto de entrada de pagos solo tras una activación exitosa; la wallet creada permanece con saldo cero.
- Hacer observables inicio, pasos y cierre del onboarding, además de permitir los reportes mensuales definidos por la spec.
- Mantener compatibilidad con los contratos publicados del mock W1 y cambios pequeños, caracterizados y reversibles.

## Non-goals

- Implementar endpoints nuevos en el mock W1 o alterar sus contratos.
- Agregar o cambiar endpoints W1-W6, validar documentos reales, prevenir registros duplicados o mover dinero real.
- Validar documentos reales, integrar proveedores de dinero real o introducir servicios externos adicionales.
- Garantizar los resultados de negocio de duración, MAU o CAC; la solución solo debe permitir medirlos.

## Contratos protegidos

- `POST /kyc/verifications` acepta `documentType: TEST`, `document` con prefijo `TEST-` y escenarios `APPROVED`, `REJECTED`, `MANUAL_REVIEW` o `UNAVAILABLE`.
- `APPROVED` activa una wallet con saldo cero; `MANUAL_REVIEW` deja la cuenta `PENDING` y abre soporte; `REJECTED` no habilita pagos; `UNAVAILABLE` responde `503` sin crear wallet.
- La consulta KYC usa el ID de verificación, distinto de `wallet_id`. Se preservan rutas, métodos, campos y respuestas documentadas por W1.
- Repetir una decisión final conserva el resultado; intentar cambiarla devuelve `409 DECISION_CONFLICT`.
- No solicitar ni enviar documentos reales. No atribuir al mock la duración, MAU, CAC o el gasto de adquisición.

## Componentes afectados

- **Aplicación consumidora `hackaton-group-8/`:** secuencia y paso actual, validación, mensajes, estados KYC, acceso a pagos e instrumentación.
- **Integración KYC/W1:** cliente HTTP configurable que invoca rutas publicadas y traduce resultados sin alterar el contrato; sin URL configurada, el alta falla explícitamente y no usa un resultado local de éxito.
- **Pruebas de contrato:** servidor local únicamente de pruebas, con fixtures sintéticos para rutas, campos y estados publicados. No se añade ningún endpoint de control al producto.
- **Analítica:** eventos y reporte mensual existentes en la aplicación/H2; el mock no recibe ni calcula métricas.
- **Mock W1 y harness CrewAI:** contratos de referencia y preparación de escenarios; no requieren cambios para esta historia.

## Decisiones técnicas y alternativas

### Integración con KYC

**Decisión:** consumir los endpoints W1 existentes desde `hackaton-group-8/`, usando `W1_BASE_URL` como configuración obligatoria en ejecución. En pruebas, un servidor HTTP local reproduce solo el contrato documentado. No se proporciona un fallback local que pueda presentar un KYC no verificado como exitoso. El alta aprobada crea el usuario local activo sin asientos de financiación.

**Alternativas consideradas:** agregar un endpoint de onboarding al mock, mover el flujo al harness CrewAI o mantener los resultados KYC locales como éxito cuando W1 no está configurado. Se descartan porque ampliarían el contrato, moverían comportamiento de producto al componente equivocado o eludirían la verificación.

### Instrumentación

**Decisión:** la aplicación consumidora emite los eventos de inicio, finalización de paso y cierre; la salida mensual también es responsabilidad de la aplicación o de su infraestructura analítica existente. No almacenar ni calcular estas métricas en el mock.

**Alternativas consideradas:** derivar duración/MAU/CAC desde las respuestas del mock o añadir endpoints analíticos al mock. Se descartan porque el mock no expone esos datos y la spec asigna esa responsabilidad a la aplicación.

**Decisión confirmada:** conservar los eventos, H2 y reporte mensual existentes en la aplicación; inicio y cierre se correlacionan por UUID local. MAU usa pagadores únicos con pago exitoso en el mes calendario de Perú. Operaciones registra el gasto por campaña/mes; CAC es gasto atribuido entre nuevas wallets activadas. El mock no calcula ninguna de estas métricas.

## Estrategia incremental

1. Ejecutar y registrar el baseline actual de la app y sus reportes antes de cambiar comportamiento.
2. Caracterizar mediante pruebas las rutas/campos W1 documentados con un servidor de contrato local; distinguirlo de una prueba contra servicio desplegado.
3. Mantener los pasos y métricas existentes según las definiciones confirmadas.
4. Cambiar el flujo para que solicite/verifique KYC en W1, persista sus identificadores, mapee los estados publicados y no acredite saldo.
5. Añadir pruebas de regresión para aprobación, revisión manual, rechazo, indisponibilidad, decisiones estables y acceso a pagos.
6. Verificar analítica mensual y contratos W1–W6 sin modificar el mock.

## Pruebas de caracterización previas

- Capturar método, ruta, cuerpos, campos de respuesta y códigos HTTP de creación/consulta KYC, decisión, wallet y soporte según los mockups, usando únicamente fixtures `TEST-*`.
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

- URL del W1 desplegado, necesaria para una prueba de integración real y el uso operativo. No existe en el entorno actual; las pruebas locales no sustituyen esa evidencia.
- Confirmar configuración de `W1_BASE_URL` al ejecutar la app. Si falta, la integración devuelve un error explícito y no activa la wallet.

Las definiciones de producto quedaron confirmadas; la URL del servicio W1 desplegado permanece pendiente y limita únicamente la verificación en vivo. No se crea un ADR separado: el cliente HTTP configurable y sus pruebas locales son decisiones reversibles dentro de esta historia.