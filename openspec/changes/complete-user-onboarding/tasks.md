# Tasks: Completar el onboarding de usuario

## 1. Caracterización previa al cambio funcional

- [ ] 1.1 Identificar el repositorio consumidor de W1, ejecutar su suite actual de onboarding y registrar el resultado baseline sin cambiar comportamiento.
- [ ] 1.2 Añadir o completar pruebas de contrato para `POST /kyc/verifications`, consulta KYC, consulta wallet y `GET /support/cases`, usando solo documentos `TEST-*` y los campos/códigos publicados.
- [ ] 1.3 Caracterizar los escenarios `APPROVED`, `MANUAL_REVIEW`, `REJECTED` y `UNAVAILABLE`, incluyendo wallet con saldo cero, caso de soporte para revisión manual y ausencia de wallet ante `503`.
- [ ] 1.4 Caracterizar decisiones finales repetidas y conflicto al intentar cambiarlas (`409 DECISION_CONFLICT`); verificar que una wallet rechazada no pueda pagar (`409`).
- [ ] 1.5 Añadir o completar pruebas del comportamiento actual de navegación, estado de progreso, validación y acceso al punto de entrada de pagos en la aplicación consumidora.
- [ ] 1.6 Revisar las pruebas y capacidades analíticas existentes en la aplicación consumidora y registrar el baseline de eventos/reportes sin añadir instrumentación funcional.

## 2. Resolver definiciones bloqueantes

- [ ] 2.1 Acordar con Producto y Cumplimiento la secuencia de pasos, los datos obligatorios, las validaciones y los mensajes accionables del onboarding.
- [ ] 2.2 Acordar con Producto la frontera temporal de inicio/fin, la definición operativa de usuario activo/MAU y la correlación de eventos de un recorrido.
- [ ] 2.3 Confirmar con Producto/Adquisición la fuente, ventana y reglas de atribución del gasto para evaluar CAC; identificar la infraestructura analítica y de reportes existente en la aplicación consumidora.

## 3. Implementación incremental

- [ ] 3.1 Implementar la secuencia de onboarding y la indicación persistente del paso actual según los pasos acordados; verificar con pruebas de flujo.
- [ ] 3.2 Implementar validación que bloquee el avance para datos obligatorios ausentes o inválidos y muestre cómo corregirlos; verificar ambos casos.
- [ ] 3.3 Integrar el inicio de KYC con el endpoint W1 existente usando únicamente `documentType: TEST` y documentos ficticios `TEST-*`; verificar solicitud y manejo de respuestas.
- [ ] 3.4 Representar `APPROVED` como wallet `ACTIVE` con saldo cero y habilitar el punto de entrada de pagos solo para ese estado; verificar navegación y saldo.
- [ ] 3.5 Representar `MANUAL_REVIEW` como `PENDING`, consultar el caso de soporte existente y comunicar que falta una decisión; verificar el estado y el mensaje.
- [ ] 3.6 Representar `REJECTED` y `UNAVAILABLE` sin presentar la cuenta como activa ni habilitar pagos; verificar rechazo y estado de indisponibilidad.
- [ ] 3.7 Emitir desde la aplicación eventos correlacionados de inicio, finalización de cada paso y cierre, usando la frontera temporal acordada; verificar eventos para recorridos completados e interrumpidos según la definición aprobada.
- [ ] 3.8 Generar la salida mensual desde la infraestructura existente para observar nuevos usuarios activos, MAU y gasto atribuido/CAC durante los primeros tres meses; verificar definiciones, cohortes y cálculos acordados.

## 4. Validación de aceptación

- [ ] 4.1 Ejecutar las pruebas de caracterización y regresión junto con las pruebas de cada corte funcional; confirmar que los contratos W1–W6 no cambiaron.
- [ ] 4.2 Verificar que no se solicitan ni envían documentos reales y que el onboarding no acredita fondos ni atribuye al mock cálculos de duración, MAU o CAC.
- [ ] 4.3 Revisar los escenarios de las specs de onboarding y analítica contra la implementación en el repositorio consumidor y documentar resultados de aceptación.

La sección 2 bloquea las tareas funcionales que dependan de esas definiciones. Este checklist no autoriza cambios fuera de la historia ni cambios en los endpoints del mock.