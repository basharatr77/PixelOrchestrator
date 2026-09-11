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
                    agent_id TEXT PRIMARY KEY
                )
                """
            )

    def save(self, agent: Agent) -> None:
        if not isinstance(agent, Agent):
            raise TypeError("Agent must be a canonical Agent.")

        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    "INSERT INTO agents (agent_id) VALUES (?)",
                    (agent.agent_id,),
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
                "SELECT agent_id FROM agents WHERE agent_id = ?",
                (agent_id,),
            ).fetchone()

        if row is None:
            return None

        return Agent(agent_id=row[0])
