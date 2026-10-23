# Testing report · onboarding W1

> **RESULTADOS DE PRUEBAS REALES; INFORME NO GENERADO POR CREWAI.** Los resultados siguientes se tomaron de ejecuciones reales del proyecto; no hubo llamada LLM/MCP.

## Ejecuciones realizadas

| Comando | Resultado |
|---|---|
| `npm run build` en `hackaton-group-8/frontend` | Angular producción: correcto. |
| `mvn -f hackaton-group-8/backend/pom.xml -B -Dquarkus.http.test-port=8083 test` con Java 21 | 39 pruebas; 0 fallas, 0 errores, 0 omitidas. |
| `mvn -f hackaton-group-8/backend/pom.xml -B -DskipTests package` | `BUILD SUCCESS`. |
| `npm test` en `hackaton-group-8/frontend` | 34 pruebas Playwright aprobadas en escritorio y móvil. |
| `openspec validate complete-user-onboarding --type change --json` | Cambio válido; dos advertencias no bloqueantes sobre texto previo a la primera sección de cada spec. |

## Cobertura relevante

| Criterio | Prueba / nivel | Resultado |
|---|---|---|
| Contrato W1 de creación y consulta KYC/wallet | `W1KycClientTest` | Métodos, rutas, campos y documento `TEST-*` comprobados con servidor local de contrato. |
| `APPROVED` | Playwright W1 + pruebas backend | `ACTIVE`, saldo cero y acceso a pagos visible. |
| `MANUAL_REVIEW` | Playwright W1 + contrato de casos | `PENDING`, caso consultado, mensaje visible; decisión repetida estable y cambio conflictivo `409`. |
| `REJECTED` | Playwright W1 + prueba backend | Sin entrada de pagos; intento de pago `409 WALLET_REJECTED`. |
| `UNAVAILABLE` | Playwright W1 + contrato HTTP | `503`, registro sin completar y sin wallet local. |
| Validación del flujo | Playwright escritorio/móvil | Campos ausentes o inválidos bloquean avance y muestran corrección. |
| Eventos y métricas | `WalletTest` | Inicio, pasos, cierre, correlación, MAU, cohortes y CAC del reporte local comprobados. |
| W2–W6 | Suites backend y Playwright existentes | Regresión aprobada; no se cambiaron sus contratos. |

## Límite de evidencia

El fixture de `frontend/tests/e2e-stack.mjs` simula el contrato W1 durante las pruebas. No existe `W1_BASE_URL` desplegada en este entorno: **integración con W1 real, ejecución del workflow GitHub y metas de negocio: NO EJECUTADAS / NO VERIFICADAS**. Los resultados sintéticos no demuestran KYC real, MAU objetivo, duración objetivo ni CAC real.
