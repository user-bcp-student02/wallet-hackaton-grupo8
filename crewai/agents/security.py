"""Revision preventiva de seguridad antes de implementar el Issue."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'security'
LABEL = 'Security'
SPEC_FILE = 'security_report.md'
EXTRACT_CODE = False

INSTRUCTIONS = """
Actua como Security antes de la implementacion. Usa el Issue seleccionado y la
documentacion de producto `docs/` que se adjunta al contexto. Esta es una evaluacion
preventiva de requisitos, no una auditoria de codigo que aun no existe.

1. Identifica activos, actores, limites de confianza y amenazas del flujo concreto:
   wallet, usuario, comercio, navegador, backend y API mock cuando apliquen.
2. Usa los limites documentados del mock como hechos: no mueve dinero, no ofrece
   autenticacion, opera con datos compartidos/en memoria y `/control/*` prepara
   escenarios; no es una API de negocio ni evidencia de seguridad productiva.
3. Evalua validacion, autorizacion, secretos, datos sensibles, errores, CORS,
   dependencias, telemetria y abuso de endpoints segun el Issue. Para pagos revisa
   idempotencia, concurrencia, estados asincronos, timeouts, callbacks y reversos.
4. Entrega a Developer controles concretos y criterios de aceptacion de seguridad.
   Para cada riesgo indica evidencia documental, impacto, severidad, mitigacion y
   como Testing puede verificarlo. Separa hechos, supuestos y preguntas abiertas.
5. No amplies el Issue a toda la epica, no cambies contratos ni inventes controles
   ya implementados. Declara lo que no se puede verificar antes de tener codigo.
   No afirmes haber ejecutado escaneos ni declares el sistema seguro.
"""
agent = Agent(role=LABEL, goal="Anticipar riesgos del Issue y fijar controles verificables antes de implementar.",
              backstory="Proteges usuarios, comercios y operaciones con analisis de amenazas basado en evidencia y alcance.", llm=llm,
              verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='Contenido de security_report.md: activos y limites de confianza; riesgos preventivos priorizados con severidad, evidencia de docs, impacto y mitigacion; controles obligatorios para Developer; pruebas de seguridad para Testing; preguntas abiertas y limites de verificacion. Distingue hechos de supuestos. No declares controles implementados ni resultados de escaneo.', agent=agent)
