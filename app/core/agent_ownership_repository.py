"""Persistent storage for canonical agent-to-device ownership."""

import sqlite3


class AgentOwnershipRepository:
    """SQLite-backed persistence for agent-to-device ownership."""

    def __init__(self, db_path) -> None:
        self.db_path = str(db_path)
        self._init()

    def _init(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_device_ownership (
                    agent_id TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    PRIMARY KEY (agent_id, device_id),
                    UNIQUE (device_id)
                )
                """
            )

    def save(self, agent_id: str, device_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO agent_device_ownership
                        (agent_id, device_id)
                    VALUES (?, ?)
                    """,
                    (agent_id, device_id),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError(
                    f"Device '{device_id}' is already owned."
                ) from exc

    def delete(self, agent_id: str, device_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                DELETE FROM agent_device_ownership
                WHERE agent_id = ? AND device_id = ?
                """,
                (agent_id, device_id),
            )

        return cursor.rowcount > 0

    def owner_of(self, device_id: str) -> str | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT agent_id
                FROM agent_device_ownership
                WHERE device_id = ?
                """,
                (device_id,),
            ).fetchone()

        if row is None:
            return None

        return row[0]

    def list_all(self) -> list[tuple[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT agent_id, device_id
                FROM agent_device_ownership
                ORDER BY agent_id, device_id
                """
            ).fetchall()

        return [(row[0], row[1]) for row in rows]
