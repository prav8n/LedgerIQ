"""One-off migration: copy a single account's data from a SQLite DB into the
configured (production) database, with a new login email + password.

Designed to run inside the backend container, which can reach Postgres and has
the app models available:

    docker compose cp ledgeriq.db backend:/tmp/source.db
    docker compose exec backend python scripts/migrate_account.py \
        --source /tmp/source.db --user-id 1 --email you@example.com

It copies the chosen user plus everything that belongs to them (cards, reward
rules, expenses, income, budgets, subscriptions, etc.), preserving primary keys,
in foreign-key-safe order, then resets the Postgres id sequences. The new
password is prompted for (kept out of your shell history).
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import os
import sys

# Make the app importable when run as a plain script (cwd may differ).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import insert, select, text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

import app.models  # noqa: E402,F401  -- register all tables on Base.metadata
from app.core.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.models.credit_card import CreditCard  # noqa: E402


async def run(source_path: str, user_id: int, new_email: str, new_password: str) -> None:
    src_engine = create_async_engine(f"sqlite+aiosqlite:///{source_path}")
    dst_engine = create_async_engine(settings.DATABASE_URL)
    hashed = hash_password(new_password)
    new_email = new_email.strip().lower()

    # 1) Read everything for this user from the source DB.
    async with src_engine.connect() as src:
        card_ids = [
            r[0]
            for r in (
                await src.execute(
                    select(CreditCard.__table__.c.id).where(
                        CreditCard.__table__.c.user_id == user_id
                    )
                )
            ).all()
        ]

        plan: dict[str, list[dict]] = {}
        for table in Base.metadata.sorted_tables:
            cols = table.c
            if table.name == "alembic_version":
                continue
            if table.name == "users":
                stmt = select(table).where(cols.id == user_id)
            elif table.name == "reward_rules":
                if not card_ids:
                    continue
                stmt = select(table).where(cols.card_id.in_(card_ids))
            elif "user_id" in cols:
                stmt = select(table).where(cols.user_id == user_id)
            else:
                continue
            plan[table.name] = [dict(r._mapping) for r in (await src.execute(stmt)).all()]

    if not plan.get("users"):
        raise SystemExit(f"No user with id={user_id} found in {source_path}")

    # Override the login credentials on the user row.
    for row in plan["users"]:
        row["email"] = new_email
        row["hashed_password"] = hashed

    # 2) Safety: refuse to clobber a non-empty target.
    async with dst_engine.connect() as dst:
        existing = await dst.scalar(text("SELECT COUNT(*) FROM users"))
        if existing:
            raise SystemExit(
                f"Target database already has {existing} user(s). Migrate into a "
                "fresh DB only (e.g. `docker compose down -v` then `up`), or you "
                "risk id collisions. Aborting."
            )

    # 3) Insert in FK-safe order, then fix sequences (Postgres only).
    async with dst_engine.begin() as dst:
        for table in Base.metadata.sorted_tables:
            rows = plan.get(table.name)
            if rows:
                await dst.execute(insert(table), rows)
        if dst_engine.dialect.name == "postgresql":
            for table in Base.metadata.sorted_tables:
                if table.name == "alembic_version" or "id" not in table.c:
                    continue
                await dst.execute(
                    text(
                        f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), "
                        f"(SELECT COALESCE(MAX(id), 1) FROM {table.name}))"
                    )
                )

    await src_engine.dispose()
    await dst_engine.dispose()

    counts = ", ".join(f"{name}={len(rows)}" for name, rows in plan.items() if rows)
    print(f"Migrated account -> {new_email}")
    print(f"Rows copied: {counts}")
    print("Log in with the new email and the password you just entered.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate one account into the prod DB.")
    parser.add_argument("--source", required=True, help="Path to the source SQLite .db file")
    parser.add_argument("--user-id", type=int, default=1, help="Source user id to migrate")
    parser.add_argument("--email", required=True, help="New login email for the account")
    args = parser.parse_args()

    password = getpass.getpass("New password for the account: ")
    confirm = getpass.getpass("Confirm new password: ")
    if password != confirm:
        raise SystemExit("Passwords do not match.")
    if len(password) < 8:
        raise SystemExit("Password must be at least 8 characters.")

    asyncio.run(run(args.source, args.user_id, args.email, password))


if __name__ == "__main__":
    main()
