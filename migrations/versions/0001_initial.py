"""Initial schema and PostgreSQL tenant RLS.

Revision ID: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None


def upgrade():
    op.create_table("tenants", sa.Column("id", sa.String(36), primary_key=True), sa.Column("name", sa.String(160), nullable=False))
    op.create_table("users", sa.Column("id", sa.String(36), primary_key=True), sa.Column("email", sa.String(254), nullable=False, unique=True), sa.Column("name", sa.String(160), nullable=False), sa.Column("password_hash", sa.String(512), nullable=False), sa.Column("platform_admin", sa.Boolean(), nullable=False))
    op.create_table("memberships", sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), primary_key=True), sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), primary_key=True), sa.Column("role", sa.String(40), nullable=False))
    op.create_table("auth_sessions", sa.Column("token_hash", sa.String(64), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_table("records", sa.Column("id", sa.String(36), primary_key=True), sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("kind", sa.String(40), nullable=False), sa.Column("data", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_records_tenant_kind", "records", ["tenant_id", "kind"])
    op.create_table("audit_events", sa.Column("id", sa.String(36), primary_key=True), sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("actor_id", sa.String(36), nullable=False), sa.Column("action", sa.String(100), nullable=False), sa.Column("resource_id", sa.String(80), nullable=False), sa.Column("details", sa.JSON(), nullable=False), sa.Column("previous_hash", sa.String(64), nullable=False), sa.Column("event_hash", sa.String(64), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_audit_tenant_time", "audit_events", ["tenant_id", "created_at"])
    if op.get_bind().dialect.name == "postgresql":
        for table in ("records", "audit_events"):
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
            op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
            op.execute(f"CREATE POLICY tenant_isolation ON {table} USING (tenant_id = current_setting('app.tenant_id', true)) WITH CHECK (tenant_id = current_setting('app.tenant_id', true))")
        op.execute("CREATE FUNCTION prevent_audit_mutation() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'Audit events are append-only'; END; $$")
        op.execute("CREATE TRIGGER audit_no_mutation BEFORE UPDATE OR DELETE ON audit_events FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation()")


def downgrade():
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TRIGGER audit_no_mutation ON audit_events")
        op.execute("DROP FUNCTION prevent_audit_mutation()")
    for table in ("audit_events", "records", "auth_sessions", "memberships", "users", "tenants"):
        op.drop_table(table)
