"""Orden de ejecución de los cuatro roles activos del flujo wallet."""
from agents import security, developer, testing, product_owner

ROLES = (security, developer, testing, product_owner)


def workflow_steps():
    return tuple(
        (role.KEY, role.LABEL, role.agent, role.SPEC_FILE, role.EXTRACT_CODE)
        for role in ROLES
    )


STEPS = workflow_steps()


def build_tasks(feature: dict) -> dict:
    return {role.KEY: role.build_task(feature) for role in ROLES}
