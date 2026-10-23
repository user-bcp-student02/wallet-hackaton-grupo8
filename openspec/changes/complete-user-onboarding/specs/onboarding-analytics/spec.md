---
Status: approved
---

# Capability: Analítica de onboarding

## ADDED Requirements

### Requirement: Onboarding lifecycle is instrumented
El sistema MUST registrar eventos observables de inicio del onboarding, finalización de cada paso y cierre del flujo.

#### Scenario: Se inicia el onboarding
- **WHEN** un usuario inicia el onboarding
- **THEN** queda registrado un evento de inicio asociado a ese recorrido

#### Scenario: Se completa un paso
- **WHEN** el usuario finaliza un paso del recorrido
- **THEN** queda registrado un evento de finalización para ese paso y recorrido

#### Scenario: Se cierra el flujo
- **WHEN** el recorrido de onboarding termina
- **THEN** queda registrado un evento de cierre asociado al mismo recorrido

### Requirement: Onboarding duration can be evaluated
La salida analítica MUST permitir calcular la mediana del tiempo de finalización de onboarding para la cohorte MVP y compararla con la línea base de 8 minutos y el objetivo de 3 minutos dentro del trimestre posterior al lanzamiento.

#### Scenario: Se evalúa la mediana de finalización
- **WHEN** se consulta la cohorte MVP durante el trimestre posterior al lanzamiento
- **THEN** la salida permite observar si la mediana de finalización bajó de 8 minutos a 3 minutos
- **AND** la medición utiliza la frontera temporal de inicio y fin acordada por Producto

### Requirement: Monthly activation and acquisition metrics are observable
La salida analítica MUST proporcionar conteos mensuales de nuevos usuarios activos y datos de atribución del gasto de adquisición suficientes para evaluar MAU entre 1,000 y 2,000 y CAC de PEN 10 por usuario nuevo durante cada uno de los primeros tres meses posteriores al lanzamiento.

#### Scenario: Se evalúa cada mes posterior al lanzamiento
- **WHEN** se consulta la salida para cualquiera de los primeros tres meses
- **THEN** se observan el conteo de nuevos usuarios activos del mes, MAU y el gasto de adquisición atribuido a los usuarios nuevos
- **AND** los datos permiten determinar si MAU está entre 1,000 y 2,000 y si CAC es PEN 10 por usuario nuevo

### Requirement: Analytics do not claim unsupported mock capabilities
La instrumentación de la aplicación MUST ser responsable de la duración, MAU, CAC y atribución de adquisición; MUST NOT atribuir esos cálculos al mock W1.

#### Scenario: Se informa cobertura analítica
- **WHEN** se describe la salida del mock W1
- **THEN** no se afirma que el mock calcula duración de onboarding, MAU, CAC o gasto de adquisición