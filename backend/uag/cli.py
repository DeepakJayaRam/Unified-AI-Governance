"""Local administrative bootstrap; no passwords in command arguments."""
import argparse
import getpass
import os
from pathlib import Path
from sqlalchemy import select
from .auth import hasher
from .db import Membership, SessionLocal, Tenant, User


def main():
    parser = argparse.ArgumentParser(prog="uag")
    commands = parser.add_subparsers(dest="command", required=True)
    boot = commands.add_parser("bootstrap")
    boot.add_argument("--email", required=True)
    boot.add_argument("--name", default="Platform Administrator")
    boot.add_argument("--tenant", required=True)
    commands.add_parser("worker")
    commands.add_parser("drain")
    key = commands.add_parser("keygen")
    key.add_argument("--path", required=True)
    args = parser.parse_args()
    if args.command == "drain":
        from .jobs import reconcile
        reconcile()
        return
    if args.command == "worker":
        from .jobs import worker
        worker()
        return
    if args.command == "keygen":
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        target = Path(args.path)
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = Ed25519PrivateKey.generate().private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
        with open(target, "xb") as handle:
            handle.write(raw)
        os.chmod(target, 0o600)
        print("Created private signing key. Restrict Windows ACLs to the service identity when applicable.")
        return
    password = os.getenv("UAG_BOOTSTRAP_PASSWORD") or getpass.getpass("Administrator password (12+ characters): ")
    if len(password) < 12 or len(password) > 1024:
        parser.error("Password must contain 12–1024 characters")
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == args.email.lower())):
            parser.error("User already exists; bootstrap will not overwrite credentials")
        tenant = Tenant(name=args.tenant)
        user = User(email=args.email.lower(), name=args.name, password_hash=hasher.hash(password), platform_admin=True)
        db.add_all([tenant, user])
        db.flush()
        db.add(Membership(user_id=user.id, tenant_id=tenant.id, role="organisation_admin"))
        db.commit()
        print(f"Created administrator and tenant {tenant.id}")


if __name__ == "__main__":
    main()
