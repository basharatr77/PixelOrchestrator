import sys
from PySide6.QtWidgets import QApplication, QLabel

app = QApplication(sys.argv)
label = QLabel("Pixel Orchestrator - Test Window")
label.show()
print("Window should be visible now")
sys.exit(app.exec())
