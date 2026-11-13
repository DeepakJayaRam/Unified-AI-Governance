from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
from sqlalchemy import text
from .config import settings
from .db import engine
from . import auth, governance, runtime, jobs, evidence

app = FastAPI(title="Unified AI Governance & Security", version="0.1.0", openapi_url="/api/v1/openapi.json", docs_url="/api/v1/docs", redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=False, allow_methods=["GET", "POST", "PUT", "PATCH"], allow_headers=["Authorization", "Content-Type", "X-Tenant-ID"], expose_headers=["Content-Disposition"])


@app.middleware("http")
async def security_headers(request: Request, call_next):
    # Reject oversized request bodies even when Transfer-Encoding is chunked.
    limit = 3_000_000
    length = request.headers.get("content-length")
    if length and (not length.isdigit() or int(length) > limit):
        return JSONResponse({"detail": "Request exceeds 3 MB"}, status_code=413)
    if request.method in {"POST", "PUT", "PATCH"}:
        data = bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data) > limit:
                return JSONResponse({"detail": "Request exceeds 3 MB"}, status_code=413)
        request._body = bytes(data)
        if data and request.headers.get("content-type", "").split(";")[0] == "application/json":
            try:
                def invalid_constant(value):
                    raise ValueError("Non-finite JSON number")
                parsed = json.loads(data, parse_constant=invalid_constant)
                pending = [(parsed, 0)]
                while pending:
                    value, depth = pending.pop()
                    if depth > 40:
                        raise ValueError("JSON nesting exceeds 40 levels")
                    if isinstance(value, dict):
                        pending.extend((item, depth + 1) for item in value.values())
                    elif isinstance(value, list):
                        pending.extend((item, depth + 1) for item in value)
            except (ValueError, RecursionError, UnicodeDecodeError):
                return JSONResponse({"detail": "Invalid JSON or excessive nesting"}, status_code=422)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    if settings.secure_environment:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.get("/health")
def health():
    try:
        with engine.connect() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok", "version": "0.1.0", "execution_mode": settings.execution_mode}
    except Exception:
        return JSONResponse({"status": "unavailable"}, status_code=503)


for router in (auth.router, governance.router, runtime.router, jobs.router, evidence.router):
    app.include_router(router, prefix="/api/v1")
