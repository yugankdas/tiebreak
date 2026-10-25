"""FastAPI dependency injection."""
from functools import lru_cache

from app.services.graph_engine import GraphEngine
from app.services.deadlock_detector import DeadlockDetector
from app.services.constraint_validator import ConstraintValidator
from app.services.groq_provider import GroqProvider
from app.services.resolution_generator import ResolutionGenerator
from app.services.action_executor import ActionExecutor
from app.services.outcome_verifier import OutcomeVerifier
from app.services.audit_service import AuditService, get_audit_service
from app.services.failproof_adapter import FailproofAdapter, get_failproof_adapter
from app.services.approval_service import ApprovalRoutingService
from app.services.project_service import ProjectService


@lru_cache(maxsize=1)
def get_groq_provider() -> GroqProvider:
    return GroqProvider()


@lru_cache(maxsize=1)
def get_approval_service() -> ApprovalRoutingService:
    return ApprovalRoutingService()


@lru_cache(maxsize=1)
def get_project_service() -> ProjectService:
    engine = GraphEngine()
    detector = DeadlockDetector(engine)
    validator = ConstraintValidator()
    groq = get_groq_provider()
    generator = ResolutionGenerator(groq)
    executor = ActionExecutor(validator)
    verifier = OutcomeVerifier(engine, detector)
    audit = get_audit_service()
    failproof = get_failproof_adapter()
    approvals = get_approval_service()

    return ProjectService(
        engine=engine,
        detector=detector,
        validator=validator,
        generator=generator,
        executor=executor,
        verifier=verifier,
        audit=audit,
        failproof=failproof,
        approvals=approvals,
    )
