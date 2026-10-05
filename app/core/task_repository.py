"""Persistent storage for canonical execution tasks."""

import json
import sqlite3

from app.core.module_contract import ActionResult
from app.core.task import Task, TaskStatus


class TaskRepository:
    """SQLite-backed persistence for canonical Tasks."""

    def __init__(self, db_path) -> None:
        self.db_path = str(db_path)
        self._init()

    def _init(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    module_id TEXT NOT NULL,
                    action_id TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL,
                    result TEXT,
                    created_at REAL NOT NULL,
                    started_at REAL,
                    completed_at REAL
                )
                """
            )

    def save(self, task: Task) -> None:
        if not isinstance(task, Task):
            raise TypeError("Task must be a canonical Task.")

        result = None
        if task.result is not None:
            result = json.dumps({
                "success": task.result.success,
                "message": task.result.message,
                "data": task.result.data,
                "error_code": task.result.error_code,
            })

        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO tasks (
                        task_id,
                        device_id,
                        module_id,
                        action_id,
                        parameters,
                        status,
                        attempts,
                        result,
                        created_at,
                        started_at,
                        completed_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task.id,
                        task.device_id,
                        task.module_id,
                        task.action_id,
                        json.dumps(task.parameters),
                        task.status.value,
                        task.attempts,
                        result,
                        task.created_at,
                        task.started_at,
                        task.completed_at,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError(
                    f"Task '{task.id}' already exists."
                ) from exc

    def get(self, task_id: str) -> Task | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT
                    task_id,
                    device_id,
                    module_id,
                    action_id,
                    parameters,
                    status,
                    attempts,
                    result,
                    created_at,
                    started_at,
                    completed_at
                FROM tasks
                WHERE task_id = ?
                """,
                (task_id,),
            ).fetchone()

        if row is None:
            return None

        result = None
        if row[7] is not None:
            payload = json.loads(row[7])
            result = ActionResult(**payload)

        return Task(
            device_id=row[1],
            module_id=row[2],
            action_id=row[3],
            parameters=json.loads(row[4]),
            id=row[0],
            status=TaskStatus(row[5]),
            attempts=row[6],
            result=result,
            created_at=row[8],
            started_at=row[9],
            completed_at=row[10],
        )

    def update(self, task: Task) -> None:
        if not isinstance(task, Task):
            raise TypeError("Task must be a canonical Task.")

        result = None
        if task.result is not None:
            result = json.dumps({
                "success": task.result.success,
                "message": task.result.message,
                "data": task.result.data,
                "error_code": task.result.error_code,
            })

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE tasks
                SET
                    device_id = ?,
                    module_id = ?,
                    action_id = ?,
                    parameters = ?,
                    status = ?,
                    attempts = ?,
                    result = ?,
                    created_at = ?,
                    started_at = ?,
                    completed_at = ?
                WHERE task_id = ?
                """,
                (
                    task.device_id,
                    task.module_id,
                    task.action_id,
                    json.dumps(task.parameters),
                    task.status.value,
                    task.attempts,
                    result,
                    task.created_at,
                    task.started_at,
                    task.completed_at,
                    task.id,
                ),
            )

            if cursor.rowcount == 0:
                raise KeyError(f"Unknown task '{task.id}'.")

    def list(self) -> "list[Task]":
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT task_id FROM tasks ORDER BY rowid"
            ).fetchall()

        return [
            task
            for (task_id,) in rows
            if (task := self.get(task_id)) is not None
        ]

    def recover_all(self) -> "list[Task]":
        recovered_tasks = []

        for task in self.list():
            if task.status is TaskStatus.RUNNING:
                task.status = TaskStatus.PENDING
                task.started_at = None
                task.completed_at = None
                task.result = None
                self.update(task)

            recovered_tasks.append(task)

        return recovered_tasks

    def recover(self, task_id: str) -> Task | None:
        task = self.get(task_id)

        if task is None:
            return None

        if task.status is TaskStatus.RUNNING:
            task.status = TaskStatus.PENDING
            task.started_at = None
            task.completed_at = None
            task.result = None

        return task
