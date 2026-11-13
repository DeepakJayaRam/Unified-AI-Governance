FROM node@sha256:dc26ae92c9fb15cf6b1d63e20f0944b2efe0f115b20e00be48fb23fceb061c54 AS discovery
WORKDIR /tooling
COPY integrations/tooling/package.json integrations/tooling/package-lock.json ./
RUN npm ci --ignore-scripts --omit=optional --no-audit

FROM python@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
COPY --from=discovery /usr/local/bin/node /usr/local/bin/node
COPY --from=discovery /tooling /app/integrations/tooling
COPY pyproject.toml LICENSE alembic.ini ./
COPY backend ./backend
COPY integrations ./integrations
COPY migrations ./migrations
COPY docs/research ./docs/research
RUN pip install --no-deps . && useradd --uid 10001 --create-home appuser
USER 10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "uag.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
