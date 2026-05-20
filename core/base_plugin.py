from abc import ABC, abstractmethod
from PySide6.QtWidgets import QWidget

class BaseDevicePlugin(ABC):
    """Every chipset plugin must inherit from this class."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Chipset name (e.g., 'MediaTek', 'Qualcomm')"""
        pass
    
    @property
    @abstractmethod
    def tab_name(self) -> str:
        """Name shown on tab (e.g., '📱 MEDIATEK')"""
        pass
    
    @abstractmethod
    def create_tab(self, parent=None) -> QWidget:
        """Return a QWidget that will be added as a tab."""
        pass