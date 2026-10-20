"""Reference examples for typed design mediation."""

from .collaborative_workflow_case_study import reference as collaborative_workflow
from .high_risk_operational_case_study import reference as high_risk_operational
from .material_case_study import reference as material
from .physical_service_case_study import reference as physical_service

EXAMPLE_MODULES = {
    "material_case_study": material,
    "physical_service_case_study": physical_service,
    "high_risk_operational_case_study": high_risk_operational,
    "collaborative_workflow_case_study": collaborative_workflow,
}

__all__ = [
    "EXAMPLE_MODULES",
    "collaborative_workflow",
    "high_risk_operational",
    "material",
    "physical_service",
]

