from typing import Annotated, Literal
from datetime import date
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

PreservedText = Annotated[str, StringConstraints(strip_whitespace=False)]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


Role = Literal["organisation_admin", "governance_manager", "security_engineer", "auditor", "viewer"]


class Login(Strict):
    email: str = Field(max_length=254)
    password: PreservedText = Field(min_length=1, max_length=1024)


class Member(Strict):
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: PreservedText = Field(min_length=12, max_length=1024)
    name: str = Field(min_length=1, max_length=160)
    role: Role


class TenantCreate(Strict):
    name: str = Field(min_length=1, max_length=160)


class SystemCreate(Strict):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=10000)
    owner: str = Field(default="", max_length=254)
    risk_level: Literal["unassessed", "minimal", "limited", "high", "unacceptable"] = "unassessed"


class RiskCreate(Strict):
    system_id: str | None = None
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    severity: Literal["info", "low", "medium", "high", "critical"] = "medium"
    status: Literal["open", "in_progress", "resolved", "accepted", "closed"] = "open"
    owner: str = Field(default="", max_length=254)
    due_date: str | None = None
    finding_id: str | None = None

    @field_validator("due_date")
    @classmethod
    def valid_date(cls, value):
        return date.fromisoformat(value).isoformat() if value else None


class EvidenceCreate(Strict):
    system_id: str | None = None
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    content: PreservedText = Field(max_length=2_000_000)
    media_type: Literal["text/plain", "application/json", "application/xml", "text/csv"] = "text/plain"


class AssessmentCreate(Strict):
    system_id: str
    framework: Literal["eu_ai_act", "iso42001", "nist_ai_rmf"]
    name: str = Field(min_length=1, max_length=200)


class ControlUpdate(Strict):
    status: Literal["not_started", "in_progress", "implemented", "not_applicable", "gap"] = "not_started"
    notes: str = Field(default="", max_length=10000)
    evidence_ids: list[str] = Field(default_factory=list, max_length=100)
    owner: str = Field(default="", max_length=254)
    due_date: str | None = None


class PolicyConfig(Strict):
    pii_action: Literal["allow", "block", "sanitize", "review"] = "sanitize"
    blocked_terms: list[str] = Field(default_factory=list, max_length=100)
    error_action: Literal["block", "review"] = "block"
    @field_validator("blocked_terms")
    @classmethod
    def term_bounds(cls, value):
        if any(not term.strip() or len(term) > 200 for term in value):
            raise ValueError("Terms must have 1–200 characters")
        return value


class PolicyCreate(Strict):
    name: str = Field(min_length=1, max_length=200)
    enabled: bool = True
    config: PolicyConfig = Field(default_factory=PolicyConfig)


class GuardrailRequest(Strict):
    text: PreservedText = Field(min_length=1, max_length=32000)
    policy_id: str | None = None


class IntegrationConfig(Strict):
    enabled: bool = False
    config: dict = Field(default_factory=dict)


class ExecutionCreate(Strict):
    integration_id: str
    system_id: str | None = None
    input: dict = Field(default_factory=dict)


class BomCreate(Strict):
    system_id: str
    document: dict


class SettingsUpdate(Strict):
    name: str = Field(default="", max_length=160)
    retention_days: int = Field(default=365, ge=30, le=3650)
    notification_email: str = Field(default="", max_length=254)


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    platform_admin: bool


class MembershipResponse(BaseModel):
    tenant_id: str
    tenant_name: str
    role: Role


class IdentityResponse(BaseModel):
    user: UserResponse
    memberships: list[MembershipResponse]


class LoginResponse(IdentityResponse):
    access_token: str
    token_type: Literal["bearer"]


class RecordMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    created_at: str
    updated_at: str


class EvidenceResponse(RecordMetadata):
    title: str
    description: str
    system_id: str | None
    media_type: str
    sha256: str
    size_bytes: int
    validation: dict
    provenance: dict


class GuardrailResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    decision: Literal["allow", "block", "sanitize", "review"]
    sanitized_text: str | None
    checks: list[dict]
    latency_ms: float
    engine: str
    event_id: str
