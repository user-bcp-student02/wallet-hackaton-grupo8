# Developer spec · onboarding W1

> **SIMULACIÓN LOCAL DE ARTEFACTO.** Resumen manual de la implementación existente para mantener la estructura esperada por CrewAI. El agente Developer no se ejecutó; no hubo modelo ni MCP.

## Estado de entrega

La aplicación consumidora está en `hackaton-group-8/`. El cambio OpenSpec `complete-user-onboarding` está en 20/20 tareas. La app usa Quarkus/Java 21, Angular y H2.

## Implementación observada

- `backend/src/main/java/pe/wallet/W1KycClient.java`: cliente HTTP para crear/consultar verificación, consultar wallet/casos y resolver decisiones. La URL viene de `W1_BASE_URL`.
- `WalletResource.complete`: valida el onboarding, envía solo `documentType: TEST` y `TEST-*`, comprueba el saldo y los estados W1.
- `Wallet.complete`: persiste referencias W1, correlaciona eventos por UUID local y no acredita fondos.
- `Wallet.reviewKyc`: conserva decisión estable y responde conflicto si se intenta cambiar el resultado.
- `frontend/src/app.html` y `app.ts`: tres pasos, errores accionables, estado pendiente/rechazado y entrada de pagos solo para wallet activa.
- `frontend/tests/e2e-stack.mjs`: fixture W1 aislado para las pruebas Playwright; no se empaqueta como proveedor de runtime.

## Mapeo de comportamiento

| Resultado W1 | Estado local | Efecto |
|---|---|---|
| `APPROVED` | `ACTIVE` | Wallet nueva con saldo cero; se habilita la entrada de pagos. |
| `MANUAL_REVIEW` | `PENDING` | Consulta casos de soporte; comunica que falta decisión. |
| `REJECTED` | `REJECTED` | No habilita pagos; el intento devuelve `409 WALLET_REJECTED`. |
| `UNAVAILABLE` | Registro incompleto | Propaga `503`; no crea wallet ni finaliza el registro. |

Las cuentas de evaluación presembradas mantienen su saldo sintético; no es saldo de altas nuevas.

## Configuración y comandos

`W1_BASE_URL` debe apuntar al mock W1 asignado al grupo. En este entorno no existe URL; `UNCONFIGURED` produce `503 W1_NOT_CONFIGURED` al intentar completar el alta. No se afirma integración en vivo.

```powershell
Set-Location hackaton-group-8\frontend
npm run build
npm test
Set-Location ..\backend
mvn -B '-Dquarkus.http.test-port=8083' test
mvn -B -DskipTests package
```

## Evidencia

- 39 pruebas backend aprobadas.
- 34 pruebas Playwright aprobadas, escritorio y móvil.
- El build Angular y el empaquetado Quarkus terminaron correctamente.
- Evidencia detallada: `hackaton-group-8/evidence.md`.

## Pendientes operativos

- Establecer `W1_BASE_URL` y repetir pruebas de integración con el servicio W1 real del grupo.
- Tras un timeout externo de creación, consultar con Operaciones antes de reintentar: el mock no garantiza deduplicación.
- La UI asigna `organico` a las nuevas altas; la atribución a campañas adicionales requiere una fuente aprobada.
