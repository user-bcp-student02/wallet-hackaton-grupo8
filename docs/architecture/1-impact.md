# Issue #1: W1 onboarding impact

## Estado del gate

El `Status: approved` de este impacto se toma como evidencia de aprobación humana del alcance, los componentes, los contratos protegidos, los riesgos y la estrategia de pruebas aquí descritos. Los estados `approved` de la propuesta y de ambas specs corroboran que la revisión previa a arquitectura está cubierta; la frase final de la propuesta describe esa revisión como requisito previo y no invalida sus estados actuales.

Esta aprobación habilita cerrar el análisis arquitectónico, no implementar en este checkout. Las decisiones de Producto/Cumplimiento y la identificación del repositorio consumidor siguen siendo prerrequisitos para comenzar esa implementación.

## Impacto

El cambio afecta al flujo de onboarding de la aplicación consumidora: guía de pasos, validación de entradas, presentación de resultados KYC y acceso al punto de entrada de pagos cuando la wallet esté activa. También requiere instrumentación analítica de inicio, finalización de pasos y cierre, además de una salida mensual para evaluar duración, nuevos usuarios activos, MAU y CAC.

El checkout actual contiene documentación de historias, contratos del mock y un harness CrewAI; no se encontró una aplicación wallet ni una implementación de backend de producto que pueda asignarse a este cambio. El diseño funcional debe ubicarse en el repositorio de la aplicación que consuma W1, sin convertir el harness o el mock en esa aplicación.

## Componentes afectados

- Aplicación cliente consumidora de W1: recorrido guiado, validación, estados y navegación al punto de entrada de pagos. No está presente en este checkout.
- Integración KYC/wallet: cliente HTTP de la aplicación que usa las APIs W1 existentes; no se identifica implementación local.
- Analítica de onboarding: responsabilidad de la aplicación, incluido el vínculo de eventos a un mismo recorrido y la agregación mensual. El mock no ofrece esta capacidad.
- Contrato de referencia: [W1 Registro y activación](../mockups/W1-Registro-y-activación.md), junto con [Cobertura y límites](../mockups/Cobertura-y-límites.md).

No se propone modificar el harness CrewAI ni agregar endpoints al mock para cumplir esta historia.

## Contratos protegidos

- `POST /kyc/verifications` recibe `documentType: TEST`, un documento ficticio con prefijo `TEST-` y el escenario simulado. No enviar documentos reales.
- `APPROVED` crea una wallet `ACTIVE` con saldo cero; onboarding no acredita fondos.
- `MANUAL_REVIEW` deja la cuenta `PENDING` y abre un caso de soporte. La decisión posterior usa `POST /kyc/verifications/{id}/decision` con `ACTIVE` o `REJECTED`.
- `REJECTED` no habilita pagos; el intento de pago con esa wallet responde `409`.
- `UNAVAILABLE` responde `503` y no crea una wallet.
- Repetir la misma decisión final conserva el resultado; intentar cambiarla responde `409 DECISION_CONFLICT`.
- Se preservan rutas, métodos, cuerpos, campos de respuesta y códigos HTTP documentados por W1. No ampliar los contratos W1–W6 como parte de este issue.
- Duración, MAU, CAC y atribución de adquisición son métricas de la aplicación; no atribuirlas al mock.

## Estrategia incremental

1. En el repositorio consumidor, caracterizar los flujos y respuestas W1 antes de cambiar la integración; confirmar que el cliente no depende de campos o estados no documentados.
2. Con Producto y Cumplimiento, definir los pasos y datos obligatorios, los mensajes y el tratamiento operativo de los estados sin inventar reglas KYC.
3. Implementar el recorrido y sus estados usando las APIs existentes, en cambios pequeños: validación y progreso, integración/resultado KYC, y navegación solo para wallets activas.
4. Añadir eventos de inicio, paso y cierre desde la aplicación; acordar identidad/correlación, frontera temporal y atribución antes de publicar métricas.
5. Añadir la salida mensual en la aplicación y verificar que permite observar las metas comprometidas. Mantener separadas las mediciones de resultado y cualquier afirmación causal sobre el flujo.

El límite de implementación es el repositorio de la aplicación consumidora, que no está presente en este checkout. El harness CrewAI y el mock no deben convertirse en sustitutos de esa aplicación ni recibir endpoints o responsabilidades analíticas para completar la historia.

## Pruebas necesarias

- Pruebas de contrato HTTP para creación/consulta KYC y decisión manual: escenarios `APPROVED`, `MANUAL_REVIEW`, `REJECTED` y `UNAVAILABLE`, incluyendo códigos, campos, saldo inicial y ausencia de wallet en `503`.
- Pruebas de idempotencia/conflicto para repetir o intentar cambiar decisiones finales; prueba de que una wallet rechazada no accede a pagos.
- Pruebas de interfaz/flujo para orden y paso actual, bloqueo ante datos ausentes o inválidos, mensajes accionables y acceso a pagos solo cuando corresponda.
- Pruebas de instrumentación que comprueben inicio, cada paso y cierre asociados al mismo recorrido, incluso para recorridos pendientes, rechazados o interrumpidos según la definición acordada.
- Pruebas de la salida mensual, frontera de duración y cálculo/atribución de MAU y CAC una vez fijadas sus definiciones; verificar cohortes y primeros tres meses posteriores al lanzamiento.
- Pruebas negativas que aseguren que solo se usan datos ficticios `TEST-` y que no se atribuyen capacidades analíticas al mock.

## Riesgos / trade-offs

- La aplicación consumidora no está en el checkout; no se pueden asignar módulos, estimar cambios de código ni ejecutar pruebas de producto aquí.
- Producto y Cumplimiento aún deben definir datos/pasos requeridos y reglas KYC. Implementarlos antes de esa definición podría inventar requisitos regulatorios o funcionales.
- La frontera de inicio/fin cambia la duración observada y su comparación con la línea base de 8 minutos y el objetivo de 3 minutos.
- Sin una fuente y regla de atribución acordadas, el CAC de PEN 10 no es verificable. La instrumentación habilita observación, no garantiza MAU, CAC ni causalidad.
- El mock es simulado, en memoria y sin movimiento de dinero real; pasar sus pruebas no demuestra por sí solo el comportamiento de una aplicación productiva.

## Decisiones abiertas

- Producto y Cumplimiento: pasos, datos obligatorios y contenido de corrección antes de implementar.
- Producto: eventos exactos que delimitan duración y definición operativa de usuario activo/MAU para la cohorte MVP.
- Producto/Adquisición: fuente, ventana y reglas de atribución del gasto que se usará para CAC.
- Equipo técnico: identificar el repositorio y los componentes de la aplicación consumidora donde se ubicará el cambio, y acordar el destino de eventos/salida analítica.

Las decisiones abiertas anteriores condicionan el diseño detallado y la implementación; no reabren el gate de aprobación de este impacto. Antes de codificar, el equipo consumidor debe resolverlas con Producto, Cumplimiento y Adquisición según corresponda, y caracterizar los contratos W1 existentes sin ampliarlos.