from pathlib import Path


class GuiSettings:
    DEFAULT_THEME = "System"
    VALID_THEMES = {"System", "Light", "Dark"}

    def __init__(self, path=None):
        self.path = Path(path) if path is not None else None
        self.theme = self.DEFAULT_THEME
        self.load()

    def load(self):
        if self.path is None or not self.path.exists():
            return

        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.startswith("theme="):
                value = line.split("=", 1)[1].strip()
                if value in self.VALID_THEMES:
                    self.theme = value
                return

    def save(self):
        if self.path is None:
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            f"theme={self.theme}\n",
            encoding="utf-8",
        )

    def reset(self):
        self.theme = self.DEFAULT_THEME
        self.save()
