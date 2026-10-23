# Product Owner review · onboarding W1

> **EJECUCIÓN REAL.** Evaluación de escritorio basada en OpenSpec, código y pruebas disponibles. No fue generada por el agente Product Owner ni aprobada por una persona mediante CrewAI.

## Alcance

Se evalúa únicamente `complete-user-onboarding`: recorrido de tres pasos, integración KYC W1, estados de wallet, eventos y reporte mensual. OpenSpec registra **20/20 tareas completas**.

## Matriz de criterios

| Criterio | Evidencia | Estado |
|---|---|---|
| Progreso visible y persistente | `frontend/tests/wallet.spec.ts`: pasos conservados tras recargar y navegación hasta confirmación. | CUMPLE |
| Datos obligatorios y formatos | Pruebas Playwright bloquean valores vacíos/incorrectos; backend vuelve a validar. | CUMPLE |
| Alta aprobada activa wallet sin fondos | Wallet W1 `ACTIVE`, saldo inicial cero; la app muestra entrada de pagos. | CUMPLE con fixture local |
| Revisión manual | `PENDING`, caso de soporte W1 consultado y mensaje que indica que falta decisión. | CUMPLE con fixture local |
| Rechazo | Estado no activo; pago rechazado con `409 WALLET_REJECTED`. | CUMPLE |
| Indisponibilidad | `503`, no se completa alta ni se crea wallet local. | CUMPLE con fixture local |
| Instrumentación | Inicio, pasos y cierre correlacionados por UUID local; eventos interrumpidos no se cuentan como completados. | CUMPLE |
| Reporte mensual | Salida local para nuevos activos, MAU, gasto/CAC; las métricas no se presentan como metas logradas. | CUMPLE como capacidad de medición |
| Contrato de servicio desplegado | No hay `W1_BASE_URL`; el fixture prueba el cliente, no el proveedor real. | NO VERIFICADO |
| Atribución de campañas | La UI captura `organico`; reportes de otras campañas requieren fuente efectiva de adquisición. | PARCIAL |

## Riesgos y próximos responsables

- **Integración real (equipo de ejecución):** configurar la URL asignada a W1 y correr smoke tests contra el grupo correcto.
- **Adquisición (Producto/Adquisición):** proporcionar una fuente de campaña para altas no orgánicas si se necesita CAC de campañas adicionales.
- **Metas de negocio (Producto):** medir en cohortes reales; no inferirlas de fixtures o pruebas sintéticas.

## Decisión simulada

**DECISION: REQUIERE AJUSTES** para declarar aceptación operativa en W1 desplegado: no se verificó integración en vivo y la atribución actual usa `organico`. La implementación local y las suites sí pasan. Esta conclusión es una simulación y no sustituye la revisión humana del Product Owner ni la aprobación de lanzamiento.
