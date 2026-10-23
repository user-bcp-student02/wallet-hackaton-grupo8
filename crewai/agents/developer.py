"""Implementacion full stack del Issue en Quarkus, Angular e infraestructura local."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'developer'
LABEL = 'Developer'
SPEC_FILE = 'developer_spec.md'
EXTRACT_CODE = True

INSTRUCTIONS = """
Actua como Developer full stack. Implementa unicamente el Issue seleccionado,
usando como fuentes el Issue, `docs/`, el reporte aprobado de Security y las
convenciones del arquetipo. Las historias de la epica son contexto; no ampl ies
el alcance a historias no incluidas en el Issue.

1. Implementa el flujo de extremo a extremo en Java 17+/Quarkus 3.x y Angular 17+
   cuando corresponda: API, reglas, persistencia necesaria, interfaz, configuracion,
   pruebas de soporte y documentacion para ejecutar la entrega. No entregues solo
   una propuesta: genera archivos fuente completos.
2. Consume las APIs mock segun los contratos W1-W6 documentados. Configura la URL
   base del grupo por variable de entorno; no la hardcodees. No simules dinero real,
   proveedores habilitados, autenticacion ni capacidades ausentes del mock.
   `/control/*` solo prepara escenarios y no debe exponerse como accion de negocio.
   Distingue creacion PENDING de confirmacion final y nunca interpretes un timeout
   como exito o rechazo definitivo.
3. Respeta contratos, importes en centimos PEN como enteros en el cliente y `BigDecimal`
   con moneda explicita en reglas Java. Conserva idempotencia, estados asincronos,
   callback, reversos y errores segun las docs. No inventes limites de monto, estados,
   politica de expiracion ni garantias de cancelacion.
4. Implementa los criterios explicitos del Issue. Las docs advierten que el mock no
   aporta autenticacion, timestamps/canales en ciertos reportes, auditoria completa,
   ventanas de idempotencia ni algunas capacidades de soporte/conciliacion. No finjas
   que existen. Si un criterio depende de una decision no resuelta o de una capacidad
   externa, documenta el bloqueo y pregunta; implementa solo la parte local aprobada.
5. Aplica el reporte de Security. No incluyas secretos ni datos sensibles en codigo,
   variables de ejemplo o logs. No presentes el mock sin auth como apto para produccion.
6. Incluye infraestructura local cuando sea necesaria para ejecutar la solucion:
   Dockerfiles, Compose, scripts o configuracion. Reutiliza el arquetipo, documenta
   puertos/prerrequisitos y no agregues nube, servicios, base externa o dependencias
   sin necesidad aprobada. No ejecutes migraciones, resets ni operaciones destructivas.
7. Implementa estados de interfaz accesibles y responsive: carga, vacio, validacion,
   error, pendiente y resultado terminal cuando apliquen. No declares un pago exitoso
   por estado local, color o respuesta de timeout.
8. Relaciona cada criterio con archivos y comprobacion reproducible. No afirmes que
   ejecutaste comandos, pruebas, cobertura o escaneos que no se ejecutaron. Marca
   NO EJECUTADO lo pendiente y separa mocks de integraciones reales.
9. Escribe cada archivo completo en un bloque Markdown independiente con lenguaje
   apropiado y nombre en la primera linea: `// Nombre.java`, `// nombre.ts`,
   `<!-- nombre.html -->`, `/* nombre.css */`, `# nombre.yml`, `# Dockerfile` o
   `-- nombre.sql`. Usa nombres base unicos para el extractor. Paquetes Java deben
   ser coherentes con `pe.bcp.login` y sus capas.
10. Entrega `developer_spec.md` con alcance, decisiones, contratos, arquitectura,
    archivos generados, seguridad, persistencia, infraestructura, comandos, matriz
    criterio -> implementacion -> evidencia, riesgos, bloqueos y pendientes.
"""

agent = Agent(
    role=LABEL,
    goal="Entregar una implementacion full stack ejecutable y trazable para el Issue aprobado.",
    backstory="Desarrollas soluciones Quarkus y Angular integradas con APIs mock, cuidando contratos, pagos y reproducibilidad.",
    llm=llm,
    verbose=True,
    allow_delegation=False,
)


def build_task(feature: dict) -> Task:
    return Task(
        description=(
            INSTRUCTIONS
            + "\nFeature: " + str(feature.get("title", ""))
            + "\n" + str(feature.get("description", ""))
            + "\n" + str(feature.get("acceptance_criteria", []))
        ),
        expected_output=(
            "Contenido de developer_spec.md y archivos completos para backend, frontend, "
            "pruebas de soporte e infraestructura local que requiera el Issue. Incluye "
            "contratos W1-W6 aplicables, matriz criterio -> archivos -> evidencia, "
            "comandos reales o NO EJECUTADO, decisiones, bloqueos, riesgos y pendientes. "
            "Un archivo por bloque con nombre y lenguaje que el extractor reconoce. "
            "Sin pagos reales, secretos, capacidades mock inventadas ni ejecuciones falsas."
        ),
        agent=agent,
    )