import hashlib
import secrets
from datetime import timedelta, timezone
from threading import Lock
from time import monotonic
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from .config import settings
from .db import AuthSession, Membership, Tenant, User, get_db, now, set_tenant
from .schemas import IdentityResponse, Login, LoginResponse, Member, TenantCreate, Strict, PreservedText, Role
from pydantic import Field

router = APIRouter()
hasher = PasswordHasher()
_dummy_hash = hasher.hash(secrets.token_urlsafe(32))
_attempts: dict[str, list[float]] = {}
_rate_lock = Lock()


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def rate_limit(key: str, limit: int, window: int = 60):
    if settings.execution_mode == "redis":
        from redis import Redis
        try:
            client = Redis.from_url(settings.redis_url, socket_timeout=2)
            bucket = "rate:" + token_hash(key)
            count = client.eval("local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end; return n", 1, bucket, window)
            if count > limit:
                raise HTTPException(429, "Rate limit exceeded")
            return
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(503, "Rate limiter unavailable")
    with _rate_lock:
        stamp = monotonic()
        # Prune expired keys as well as the current window to bound memory.
        for old_key in list(_attempts):
            if not _attempts[old_key] or _attempts[old_key][-1] <= stamp - window:
                del _attempts[old_key]
        values = [x for x in _attempts.get(key, []) if x > stamp - window]
        if len(values) >= limit:
            raise HTTPException(429, "Rate limit exceeded")
        _attempts[key] = values + [stamp]


def current_user(authorization: str = Header(default=""), db: Session = Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required")
    session = db.get(AuthSession, token_hash(authorization[7:]))
    if not session or session.expires_at.replace(tzinfo=timezone.utc) <= now():
        raise HTTPException(401, "Session expired or invalid")
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(401, "Unknown identity")
    return user


def context(x_tenant_id: str = Header(default=""), user: User = Depends(current_user), db: Session = Depends(get_db)):
    membership = db.get(Membership, (user.id, x_tenant_id))
    if not membership:
        raise HTTPException(403, "Tenant membership required")
    set_tenant(db, x_tenant_id)
    rate_limit("api:" + user.id, 600)
    return {"tenant_id": x_tenant_id, "user_id": user.id, "role": membership.role, "user": user}


def require_write(ctx=Depends(context)):
    if ctx["role"] not in {"organisation_admin", "governance_manager", "security_engineer", "contributor"}:
        raise HTTPException(403, "This role is read-only")
    return ctx


def require_admin(ctx=Depends(context)):
    if ctx["role"] != "organisation_admin":
        raise HTTPException(403, "Organisation administrator required")
    return ctx


def identity(db, user):
    memberships = db.execute(select(Membership, Tenant).join(Tenant).where(Membership.user_id == user.id)).all()
    return {"user": {"id": user.id, "email": user.email, "name": user.name, "platform_admin": user.platform_admin}, "memberships": [{"tenant_id": m.tenant_id, "tenant_name": t.name, "role": m.role} for m, t in memberships]}


@router.post("/auth/login", response_model=LoginResponse)
def login(body: Login, request: Request, db: Session = Depends(get_db)):
    rate_limit("login-ip:" + (request.client.host if request.client else "unknown"), 20, 300)
    rate_limit("login-user:" + body.email.lower(), 10, 300)
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    try:
        hasher.verify(user.password_hash if user else _dummy_hash, body.password)
    except VerificationError:
        raise HTTPException(401, "Invalid email or password")
    if not user:
        raise HTTPException(401, "Invalid email or password")
    token = secrets.token_urlsafe(48)
    db.add(AuthSession(token_hash=token_hash(token), user_id=user.id, expires_at=now() + timedelta(hours=settings.session_hours)))
    db.commit()
    return {"access_token": token, "token_type": "bearer", **identity(db, user)}


@router.get("/auth/me", response_model=IdentityResponse)
def me(user=Depends(current_user), db: Session = Depends(get_db)):
    return identity(db, user)


@router.post("/auth/logout", status_code=204)
def logout(authorization: str = Header(), user=Depends(current_user), db: Session = Depends(get_db)):
    db.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash(authorization[7:])))
    db.commit()


@router.get("/memberships")
def memberships(ctx=Depends(context), db: Session = Depends(get_db)):
    return [{"id": u.id, "email": u.email, "name": u.name, "role": m.role} for m, u in db.execute(select(Membership, User).join(User).where(Membership.tenant_id == ctx["tenant_id"])).all()]


@router.post("/memberships", status_code=201)
def add_member(body: Member, ctx=Depends(require_admin), db: Session = Depends(get_db)):
    from .resources import audit
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user:
        # A tenant admin must never reset another tenant's identity or enrol it silently.
        raise HTTPException(409, "Identity already exists; cross-organisation invitations require platform administration")
    user = User(email=body.email.lower(), name=body.name, password_hash=hasher.hash(body.password))
    db.add(user)
    db.flush()
    db.add(Membership(user_id=user.id, tenant_id=ctx["tenant_id"], role=body.role))
    audit(db, ctx, "membership.created", user.id, {"role": body.role})
    db.commit()
    return {"id": user.id, "email": user.email, "name": user.name, "role": body.role}


@router.post("/tenants", status_code=201)
def add_tenant(body: TenantCreate, user=Depends(current_user), db: Session = Depends(get_db)):
    if not user.platform_admin:
        raise HTTPException(403, "Platform administrator required")
    tenant = Tenant(name=body.name)
    db.add(tenant)
    db.flush()
    db.add(Membership(user_id=user.id, tenant_id=tenant.id, role="organisation_admin"))
    db.commit()
    return {"id": tenant.id, "name": tenant.name}


class PasswordChange(Strict):
    current_password: PreservedText = Field(min_length=1, max_length=1024)
    new_password: PreservedText = Field(min_length=12, max_length=1024)


@router.post('/auth/password', status_code=204)
def change_password(body: PasswordChange, user=Depends(current_user), db: Session=Depends(get_db)):
    rate_limit('password:'+user.id, 5, 300)
    try:
        hasher.verify(user.password_hash, body.current_password)
    except VerificationError:
        raise HTTPException(403, 'Current password is incorrect')
    user.password_hash = hasher.hash(body.new_password)
    db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    db.commit()


class MembershipChange(Strict):
    role: Role


def membership_target(db, ctx, identifier):
    from .resources import lock_tenant
    lock_tenant(db, ctx)
    member = db.get(Membership, (identifier, ctx['tenant_id']))
    if not member:
        raise HTTPException(404, 'Membership not found')
    return member


def protect_last_admin(db, ctx, member, new_role=None):
    if member.role == 'organisation_admin' and new_role != 'organisation_admin':
        administrators = list(db.scalars(select(Membership).where(Membership.tenant_id == ctx['tenant_id'], Membership.role == 'organisation_admin')))
        if len(administrators) <= 1:
            raise HTTPException(409, 'Keep at least one organisation administrator')


@router.patch('/memberships/{identifier}')
def change_membership(identifier: str, body: MembershipChange, ctx=Depends(require_admin), db: Session=Depends(get_db)):
    from .resources import audit
    member = membership_target(db, ctx, identifier)
    protect_last_admin(db, ctx, member, body.role)
    member.role = body.role
    audit(db, ctx, 'membership.role_changed', identifier, {'role':body.role})
    db.commit()
    return {'id':identifier, 'role':body.role}


@router.delete('/memberships/{identifier}', status_code=204)
def remove_membership(identifier: str, ctx=Depends(require_admin), db: Session=Depends(get_db)):
    from .resources import audit
    member = membership_target(db, ctx, identifier)
    protect_last_admin(db, ctx, member)
    db.delete(member)
    audit(db, ctx, 'membership.removed', identifier)
    db.commit()
