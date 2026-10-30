import argparse
import getpass
import secrets
import sys
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import create_db_engine, create_session_factory
from app.core.security import ApiClientKind, PasswordHasher, UserRole, hash_api_key

MIN_ADMIN_PASSWORD_LENGTH = 12
API_KEY_BYTES = 32


@dataclass(frozen=True)
class Category:
    name: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class DeviceGroup:
    name: str
    department_code: str
    branch_code: str


DEPARTMENTS = (
    ("IT", "Information Technology"),
    ("HR", "Human Resources"),
    ("FIN", "Finance"),
    ("SALES", "Sales"),
    ("OPS", "Operations"),
)

BRANCHES = (
    ("HQ", "Head Office"),
    ("HCM", "Ho Chi Minh City"),
    ("HN", "Hanoi"),
    ("DN", "Da Nang"),
)

SOFTWARE = (
    "Microsoft Outlook",
    "Microsoft Teams",
    "Microsoft Office",
    "VPN Client",
    "Antivirus",
    "ERP",
    "Google Chrome",
    "Windows",
)

DEVICE_GROUPS = (
    DeviceGroup("HQ Workstations", "IT", "HQ"),
    DeviceGroup("HQ Finance Laptops", "FIN", "HQ"),
    DeviceGroup("HCM Sales Laptops", "SALES", "HCM"),
    DeviceGroup("HN Operations Desktops", "OPS", "HN"),
    DeviceGroup("DN HR Desktops", "HR", "DN"),
)

CATEGORIES = (
    Category("Network", ("network", "wifi", "internet", "dns", "connection lost", "timeout")),
    Category("Email", ("email", "outlook", "mailbox", "smtp", "cannot send mail")),
    Category("VPN", ("vpn", "remote access", "tunnel")),
    Category("Login and access", ("login", "password", "locked out", "access denied", "sso")),
    Category("Printer", ("printer", "print", "spooler", "toner")),
    Category("Software", ("install", "crash", "update failed", "license", "application error")),
    Category("Hardware", ("laptop", "monitor", "keyboard", "disk failure", "battery")),
    Category("Performance", ("slow", "freezing", "high cpu", "out of memory")),
    Category("Security", ("virus", "malware", "phishing", "antivirus", "blocked")),
)

INSERT_DEPARTMENT = text(
    "INSERT INTO departments (code, name) VALUES (:code, :name) ON CONFLICT (code) DO NOTHING"
)
INSERT_BRANCH = text(
    "INSERT INTO branches (code, name) VALUES (:code, :name) ON CONFLICT (code) DO NOTHING"
)
INSERT_SOFTWARE = text("INSERT INTO software (name) VALUES (:name) ON CONFLICT (name) DO NOTHING")
INSERT_DEVICE_GROUP = text(
    "INSERT INTO device_groups (name, department_id, branch_id) "
    "SELECT :name, d.id, b.id FROM departments d, branches b "
    "WHERE d.code = :department_code AND b.code = :branch_code "
    "ON CONFLICT (name) DO NOTHING"
)
INSERT_CATEGORY = text(
    "INSERT INTO categories (name, keywords) VALUES (:name, :keywords) "
    "ON CONFLICT (name) DO NOTHING"
)
INSERT_SETTINGS = text("INSERT INTO settings (id) VALUES (1) ON CONFLICT (id) DO NOTHING")
INSERT_ADMIN = text(
    "INSERT INTO app_users (full_name, email, password_hash, role) "
    "VALUES (:full_name, :email, :password_hash, :role) ON CONFLICT (email) DO NOTHING RETURNING id"
)
INSERT_API_CLIENT = text(
    "INSERT INTO api_clients (name, kind, key_hash) VALUES (:name, :kind, :key_hash) "
    "ON CONFLICT (name) DO NOTHING RETURNING id"
)
ROTATE_API_CLIENT = text(
    "UPDATE api_clients SET key_hash = :key_hash WHERE name = :name RETURNING id"
)


class SeedError(Exception):
    pass


def seed_reference_data(session: Session) -> None:
    session.execute(INSERT_SETTINGS)
    session.execute(INSERT_DEPARTMENT, [{"code": c, "name": n} for c, n in DEPARTMENTS])
    session.execute(INSERT_BRANCH, [{"code": c, "name": n} for c, n in BRANCHES])
    session.execute(INSERT_SOFTWARE, [{"name": name} for name in SOFTWARE])
    session.execute(
        INSERT_DEVICE_GROUP,
        [
            {"name": g.name, "department_code": g.department_code, "branch_code": g.branch_code}
            for g in DEVICE_GROUPS
        ],
    )
    session.execute(
        INSERT_CATEGORY,
        [{"name": c.name, "keywords": list(c.keywords)} for c in CATEGORIES],
    )


def seed_administrator(session: Session, email: str, full_name: str, password: str) -> bool:
    if len(password) < MIN_ADMIN_PASSWORD_LENGTH:
        raise SeedError(f"Password must have at least {MIN_ADMIN_PASSWORD_LENGTH} characters")
    result = session.execute(
        INSERT_ADMIN,
        {
            "full_name": full_name,
            "email": email,
            "password_hash": PasswordHasher().hash(password),
            "role": UserRole.ADMIN.value,
        },
    )
    return result.first() is not None


def create_api_client(session: Session, name: str, kind: ApiClientKind) -> str:
    api_key = secrets.token_urlsafe(API_KEY_BYTES)
    result = session.execute(
        INSERT_API_CLIENT, {"name": name, "kind": kind.value, "key_hash": hash_api_key(api_key)}
    )
    if result.first() is None:
        raise SeedError(f"API client '{name}' already exists; use rotate-api-client")
    return api_key


def rotate_api_client(session: Session, name: str) -> str:
    api_key = secrets.token_urlsafe(API_KEY_BYTES)
    result = session.execute(ROTATE_API_CLIENT, {"name": name, "key_hash": hash_api_key(api_key)})
    if result.first() is None:
        raise SeedError(f"API client '{name}' does not exist")
    return api_key


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.seed")
    commands = parser.add_subparsers(dest="command", required=True)

    seed = commands.add_parser(
        "seed", help="Insert default settings, lookups, and the Administrator"
    )
    seed.add_argument("--admin-email", required=True)
    seed.add_argument("--admin-name", default="Administrator")

    create = commands.add_parser("create-api-client", help="Create an API client and print its key")
    create.add_argument("--name", required=True)
    create.add_argument("--kind", required=True, choices=[kind.value for kind in ApiClientKind])

    rotate = commands.add_parser("rotate-api-client", help="Replace an API client's key")
    rotate.add_argument("--name", required=True)
    return parser


def run(session: Session, arguments: argparse.Namespace) -> str:
    if arguments.command == "seed":
        seed_reference_data(session)
        password = getpass.getpass("Administrator password: ")
        if password != getpass.getpass("Repeat password: "):
            raise SeedError("Passwords do not match")
        created = seed_administrator(session, arguments.admin_email, arguments.admin_name, password)
        return "Administrator created" if created else "Administrator already exists"
    if arguments.command == "create-api-client":
        kind = ApiClientKind(arguments.kind)
        return f"API key (shown once): {create_api_client(session, arguments.name, kind)}"
    return f"API key (shown once): {rotate_api_client(session, arguments.name)}"


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    settings = Settings()
    engine = create_db_engine(settings)
    try:
        with create_session_factory(engine).begin() as session:
            print(run(session, arguments))
    except SeedError as error:
        print(error, file=sys.stderr)
        return 1
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
