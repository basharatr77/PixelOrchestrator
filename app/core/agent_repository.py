"""Persistent storage for canonical remote-agent identities."""

import sqlite3

from app.core.agent_registry import Agent


class AgentRepository:
    """SQLite-backed persistence for remote agents."""

    def __init__(self, db_path) -> None:
        self.db_path = str(db_path)
        self._init()

    def _init(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    last_seen_at TEXT
                )
                """
            )

            columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(agents)"
                ).fetchall()
            }

            if "last_seen_at" not in columns:
                conn.execute(
                    "ALTER TABLE agents ADD COLUMN last_seen_at TEXT"
                )

    def save(self, agent: Agent) -> None:
        if not isinstance(agent, Agent):
            raise TypeError("Agent must be a canonical Agent.")

        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    "INSERT INTO agents (agent_id, last_seen_at) VALUES (?, ?)",
                    (agent.agent_id, agent.last_seen_at),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError(
                    f"Agent '{agent.agent_id}' already exists."
                ) from exc

    def list_ids(self) -> list[str]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT agent_id FROM agents ORDER BY agent_id"
            ).fetchall()

        return [row[0] for row in rows]

    def get(self, agent_id: str) -> Agent | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT agent_id, last_seen_at FROM agents WHERE agent_id = ?",
                (agent_id,),
            ).fetchone()

        if row is None:
            return None

        return Agent(agent_id=row[0], last_seen_at=row[1])

    def update_last_seen(self, agent_id: str, last_seen_at: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE agents
                SET last_seen_at = ?
                WHERE agent_id = ?
                """,
                (last_seen_at, agent_id),
            )

            if cursor.rowcount == 0:
                raise KeyError(f"Unknown agent '{agent_id}'.")
