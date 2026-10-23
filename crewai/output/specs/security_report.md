# Security review · onboarding W1

> **EJECUCIÓN REAL.** Este informe se redactó a partir del código y la documentación existentes. No fue generado por el agente Security de CrewAI: `main.py` no se ejecutó, no hubo llamada a modelo ni a MCP. No es una auditoría de seguridad.

## Alcance y evidencia

- Historia: onboarding W1 en `hackaton-group-8/`.
- Contrato: `docs/mockups/W1-Registro-y-activación.md`.
- Estado OpenSpec: `complete-user-onboarding`, 20/20 tareas; validación del cambio correcta.
- Código relevante: `backend/src/main/java/pe/wallet/W1KycClient.java`, `WalletResource.java` y `Wallet.java`.

## Activos y límites de confianza

El cliente web envía datos ficticios al backend Quarkus local. Solo el backend debe llamar al proveedor W1, mediante `W1_BASE_URL`. El adaptador envía `documentType: TEST` y un identificador aleatorio `TEST-*`; no necesita nombre, celular ni PIN. El fixture HTTP local está dentro de las pruebas Playwright y no forma parte del runtime productivo.

## Riesgos y controles

| Riesgo | Nivel | Evidencia / impacto | Control observado o pendiente | Verificación |
|---|---|---|---|---|
| Servicio W1 no configurado | Bloqueo operativo | `W1_BASE_URL` no está configurada en este entorno; el alta no puede consultar KYC real. | Devuelve `503 W1_NOT_CONFIGURED`; no activa la wallet mediante un fallback local. Configurar la URL asignada al grupo antes de operar. | Caso cubierto con URL ausente; integración con W1 desplegado: **NO EJECUTADA**. |
| Demo local sin autenticación real | Alto para publicación | La identidad y los perfiles OPS son sintéticos, según `docs/architecture.md`. | Mantener el servidor enlazado a `127.0.0.1`; no exponerlo a Internet ni usar datos o dinero reales. | Revisado en configuración y documentación; no es auditoría externa. |
| Documento real enviado por error | Alto | La API W1 solo acepta documentos de prueba. | El cliente construye únicamente un `TEST-*` y el test de contrato comprueba que no se serializan campos de identidad o PIN. | Prueba `W1KycClientTest`. |
| Respuesta de red perdida tras crear verificación | Medio | W1 no promete idempotencia ni evita altas repetidas; un timeout puede dejar el resultado externo sin confirmar. | No reportar éxito/rechazo ni reintentar automáticamente; el cliente devuelve error explícito. La conciliación en vivo requiere la URL W1. | Pruebas de contrato locales; comportamiento ante timeout remoto real: **NO VERIFICADO**. |
| Decisión final contradictoria | Medio | Cambiar un resultado final podría dejar discrepancia entre la app y W1. | La ruta de OPS delega la decisión en W1; un conflicto `409 DECISION_CONFLICT` se propaga y el estado local no se cambia. | Pruebas de repetición y conflicto con fixture local. |

## Criterios para un Security real

1. Configurar la URL W1 asignada y ejecutar creación, consulta y decisión en un grupo aislado de pruebas.
2. Confirmar que logs y trazas no contienen `TEST-*`, alias, teléfono o PIN.
3. No habilitar controladores de laboratorio al publicar el demo.
4. No presentar el mock ni los perfiles de evaluación como autenticación o KYC productivo.

No se ejecutaron escáneres, análisis de dependencias ni pruebas contra un servicio W1 desplegado.
