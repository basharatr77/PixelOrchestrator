from abc import ABC, abstractmethod
from PySide6.QtWidgets import QWidget

class BaseModule(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Module display name (e.g., 'MediaTek')"""
        pass

    @property
    @abstractmethod
    def icon(self) -> str:
        """Icon text or emoji"""
        pass

    @abstractmethod
    def create_ui(self, parent=None) -> QWidget:
        """Return the UI widget for this module."""
        pass
