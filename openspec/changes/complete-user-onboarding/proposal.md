---
Status: approved
---

# Propuesta: Completar el onboarding de usuario

## Referencia

- Issue comprometido: [#1 - W1. Registro y activación](https://github.com/user-bcp-student49/wallet-hackaton-grupo8/issues/1)
- Referencias funcionales: `docs/mockups/W1-Registro-y-activación.md`, `docs/mockups/Cobertura-y-límites.md` y `docs/mockups/Controles-del-mock.md`.

## Por qué importa

El onboarding lento y confuso impide que usuarios de pagos cotidianos lleguen a la activación. El Issue #1 fija como objetivo reducir el tiempo mediano de finalización de 8 a 3 minutos dentro del trimestre posterior al lanzamiento y requiere instrumentación para verificar activación, MAU y CAC. La propuesta convierte esos compromisos en comportamientos y resultados observables, sin afirmar que la instrumentación por sí sola alcanzará las metas de negocio.

## Alcance

- Un recorrido guiado de onboarding que presenta la secuencia requerida y mantiene visible el paso actual.
- Validación que impide avanzar ante datos obligatorios ausentes o inválidos y comunica cómo corregirlos.
- Activación de la wallet y acceso al punto de entrada de pagos de bajo monto cuando el onboarding finaliza correctamente.
- Registro analítico del inicio, finalización de cada paso y cierre del flujo, más una salida mensual que permita evaluar duración, nuevos usuarios activos, MAU y CAC durante los primeros tres meses.
- Tratamiento observable de los resultados de KYC simulados descritos en el mock W1.

## Fuera de alcance

- Definir requisitos de KYC real, documentos aceptados, reglas regulatorias o decisiones de cumplimiento; el Issue los deja pendientes de Producto y Cumplimiento.
- Verificar documentos reales, evitar registros repetidos o implementar movimientos de dinero real. El mock explicita que no ofrece esas capacidades.
- Diseñar arquitectura, APIs nuevas, almacenamiento, herramientas analíticas, taxonomía de eventos o pantallas detalladas.
- Cambiar contratos de mockups W1–W6 o ampliar esta historia a pagos, conciliación u otras capacidades.
- Garantizar por sí solo el logro de MAU/CAC; el cambio debe permitir medirlos.

## Comportamiento que debe preservarse

- El KYC del mock acepta únicamente `documentType: TEST` y documentos ficticios con prefijo `TEST-`; no se deben solicitar ni enviar documentos reales.
- `APPROVED` crea una wallet `ACTIVE` con saldo cero; `MANUAL_REVIEW` deja la cuenta `PENDING` y abre un caso de soporte; `REJECTED` produce una cuenta rechazada; `UNAVAILABLE` responde `503` y no crea una wallet.
- Una wallet rechazada no puede pagar (`409`). Las decisiones finales repetidas conservan el resultado y cambiar una decisión final devuelve `409`.
- La wallet creada no recibe fondos por el onboarding; el punto de entrada de pagos no implica saldo disponible.
- La instrumentación del onboarding pertenece a la aplicación. El mock no calcula duración, MAU, CAC ni atribución de adquisición.

## Preguntas abiertas y restricciones

- Producto y Cumplimiento deben definir los datos y pasos obligatorios antes de implementar; esta propuesta no los inventa.
- El Issue deja abierta la frontera de eventos que determina inicio y fin de duración. Debe acordarse antes de usar la mediana como criterio de aceptación del lanzamiento.
- Deben confirmarse la fuente y las reglas de atribución de gasto de adquisición para interpretar CAC. El objetivo comprometido sigue siendo PEN 10 por usuario nuevo.
- La mediana objetivo es 3 minutos, con línea base de 8 minutos, dentro del trimestre posterior al lanzamiento. Los objetivos de MAU (1,000–2,000) y CAC (PEN 10) se evalúan en cada uno de los primeros tres meses.

## Verificación

Los escenarios de `specs/onboarding/spec.md` comprueban el recorrido y los resultados de los escenarios KYC del mock. Los escenarios de `specs/onboarding-analytics/spec.md` comprueban emisión de eventos y que la salida mensual permita evaluar las metas del Issue. Los umbrales de negocio son resultados a observar en la cohorte MVP, no una garantía causal del flujo.

La propuesta y las specs requieren revisión humana antes de pasar a arquitectura. El diseño técnico y las tareas quedan deliberadamente pendientes.