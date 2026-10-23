# Capability: Onboarding de usuario

## ADDED Requirements

### Requirement: Guided onboarding progress
El flujo de onboarding MUST mostrar la secuencia de pasos requeridos y el paso actual durante todo el recorrido.

#### Scenario: Usuario inicia el recorrido
- **WHEN** el usuario inicia el onboarding
- **THEN** el flujo muestra la secuencia requerida y señala el paso actual

#### Scenario: Usuario completa un paso
- **WHEN** el usuario completa un paso y avanza
- **THEN** el flujo actualiza el paso actual y mantiene visible la secuencia

### Requirement: Validation blocks incomplete or invalid progress
El flujo MUST impedir avanzar si falta información obligatoria o si los datos ingresados son inválidos, y MUST mostrar un mensaje accionable para corregirlos.

#### Scenario: Falta información obligatoria
- **WHEN** el usuario intenta avanzar con un dato obligatorio ausente
- **THEN** permanece en el paso actual y recibe un mensaje que identifica la corrección necesaria

#### Scenario: Los datos no son válidos
- **WHEN** el usuario intenta avanzar con datos inválidos
- **THEN** permanece en el paso actual y recibe un mensaje que permite corregirlos

### Requirement: Successful onboarding activates the wallet
Al finalizar correctamente el onboarding, el sistema MUST dejar la wallet activa y permitir al usuario acceder al punto de entrada de pagos de bajo monto.

#### Scenario: Verificación aprobada
- **WHEN** el proveedor KYC simulado aprueba el registro y el usuario completa los pasos requeridos
- **THEN** la wallet queda `ACTIVE` con saldo cero y el usuario puede acceder al punto de entrada de pagos de bajo monto

### Requirement: Pending review is communicated
El flujo MUST comunicar que el usuario está pendiente de una decisión cuando el resultado de KYC sea `MANUAL_REVIEW`.

#### Scenario: KYC requiere revisión manual
- **WHEN** la verificación devuelve `MANUAL_REVIEW`
- **THEN** la cuenta queda `PENDING`, se abre un caso de soporte y la interfaz informa que falta una decisión

### Requirement: Rejected registration remains ineligible for payment
El flujo MUST representar el resultado rechazado y MUST NOT presentar la cuenta como activa ni permitir que pague.

#### Scenario: KYC rechaza el registro
- **WHEN** la verificación devuelve `REJECTED`
- **THEN** la cuenta queda rechazada y un intento de pago con esa wallet es rechazado con `409`

### Requirement: KYC unavailability does not create a wallet
El flujo MUST informar que el servicio de verificación no está disponible y MUST NOT tratar el intento como una activación.

#### Scenario: Proveedor KYC no disponible
- **WHEN** la verificación devuelve `UNAVAILABLE`
- **THEN** el servicio responde `503`, no se crea una wallet y el usuario recibe un estado de indisponibilidad

### Requirement: Final KYC decisions are stable
Las decisiones finales `ACTIVE` o `REJECTED` MUST conservarse al repetir la misma decisión; intentar cambiar una decisión final MUST devolver `409`.

#### Scenario: Se repite una decisión final
- **WHEN** se envía de nuevo la decisión final ya registrada
- **THEN** se conserva el mismo resultado

#### Scenario: Se intenta cambiar una decisión final
- **WHEN** se envía una decisión final distinta a la ya registrada
- **THEN** la operación se rechaza con `409` y el resultado original se conserva

### Requirement: Mock registration uses fictitious test documents only
El recorrido que integra el mock MUST enviar únicamente `documentType: TEST` y documentos ficticios con prefijo `TEST-`; MUST NOT solicitar ni enviar documentos reales.

#### Scenario: Registro contra el KYC simulado
- **WHEN** el recorrido inicia una verificación en el mock
- **THEN** utiliza el tipo `TEST` y un documento con prefijo `TEST-`
- **AND** no envía información de documentos reales