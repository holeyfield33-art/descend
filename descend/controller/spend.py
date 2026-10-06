"""Controller-owned durable reservations; ambiguous calls keep their full hold."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4

MAX_SPEND_MICRO_USD = 20_000_000


class SpendExhausted(RuntimeError):
    pass


class SpendLedger:
    def __init__(self, path: str | Path, *, cap_micro_usd: int = MAX_SPEND_MICRO_USD):
        if type(cap_micro_usd) is not int or not 0 <= cap_micro_usd <= MAX_SPEND_MICRO_USD:
            raise ValueError("Spend cap must be between zero and the authorized $20")
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS policy (cap INTEGER NOT NULL, halted INTEGER NOT NULL DEFAULT 0)")
            row = db.execute("SELECT cap FROM policy").fetchone()
            if row is None:
                db.execute("INSERT INTO policy (cap) VALUES (?)", (cap_micro_usd,))
            elif row[0] != cap_micro_usd:
                raise ValueError("Existing ledger cap cannot be changed")
            db.execute("CREATE TABLE IF NOT EXISTS calls (id TEXT PRIMARY KEY, run_id TEXT, "
                       "reserved INTEGER NOT NULL, charged INTEGER, provider_id TEXT)")

    def reserve(self, run_id: str, amount: int) -> str:
        if type(amount) is not int or amount <= 0:
            raise ValueError("Positive bounded reservation required")
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT halted FROM policy").fetchone()[0]:
                raise SpendExhausted("Ledger halted after an accounting overrun")
            total = db.execute("SELECT COALESCE(SUM(COALESCE(charged,reserved)),0) FROM calls").fetchone()[0]
            cap = db.execute("SELECT cap FROM policy").fetchone()[0]
            if total + amount > cap:
                raise SpendExhausted("Cloud spend cap exhausted")
            call_id = uuid4().hex
            db.execute("INSERT INTO calls VALUES (?,?,?,NULL,NULL)", (call_id, run_id, amount))
            return call_id

    def settle(self, call_id: str, charged: int, provider_id: str) -> None:
        if type(charged) is not int or charged < 0:
            raise ValueError("Invalid charge")
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT reserved, charged FROM calls WHERE id=?", (call_id,)).fetchone()
            if row is None or row[1] is not None:
                raise ValueError("Unknown or settled reservation")
            if charged > row[0]:
                # Keep the observed overrun recorded; prevent further calls.
                db.execute("UPDATE calls SET charged=?,provider_id=? WHERE id=?", (charged, provider_id, call_id))
                db.execute("UPDATE policy SET halted=1")
                db.commit()
                raise SpendExhausted("Provider usage exceeded reservation; stop paid calls")
            db.execute("UPDATE calls SET charged=?,provider_id=? WHERE id=?", (charged, provider_id, call_id))

    def summary(self) -> dict:
        with closing(sqlite3.connect(self.path)) as db, db:
            cap = db.execute("SELECT cap FROM policy").fetchone()[0]
            used, pending, calls = db.execute(
                "SELECT COALESCE(SUM(COALESCE(charged,reserved)),0),"
                "SUM(CASE WHEN charged IS NULL THEN 1 ELSE 0 END), COUNT(*) FROM calls").fetchone()
        return {"cap_usd": cap / 1_000_000, "accounted_upper_bound_usd": used / 1_000_000,
                "unresolved_calls": pending or 0, "calls": calls,
                "billing_receipt": False}
