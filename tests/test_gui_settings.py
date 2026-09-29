from PyQt6.QtWidgets import QApplication
from app.gui.main_window import MainWindow
from app.gui.settings import GuiSettings


def test_settings_workspace_exposes_configuration_controls():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert hasattr(window, "settings_workspace")
    assert hasattr(window, "settings_save_button")
    assert hasattr(window, "settings_reset_button")
    assert hasattr(window, "settings_theme_combo")


def test_gui_settings_defaults_to_system_theme():
    settings = GuiSettings()

    assert settings.theme == "System"


def test_gui_settings_can_save_and_load_theme(tmp_path):
    settings = GuiSettings(tmp_path / "settings.ini")

    settings.theme = "Dark"
    settings.save()

    loaded = GuiSettings(tmp_path / "settings.ini")

    assert loaded.theme == "Dark"


def test_gui_settings_reset_restores_system_theme(tmp_path):
    settings = GuiSettings(tmp_path / "settings.ini")

    settings.theme = "Dark"
    settings.save()
    settings.reset()

    assert settings.theme == "System"


def test_main_window_loads_gui_settings_theme(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.ini"
    settings = GuiSettings(settings_path)
    settings.theme = "Dark"
    settings.save()

    monkeypatch.setattr(
        "app.gui.main_window.GuiSettings",
        lambda: GuiSettings(settings_path),
    )

    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert window.settings_theme_combo.currentText() == "Dark"


def test_main_window_save_button_persists_selected_theme(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.ini"

    monkeypatch.setattr(
        "app.gui.main_window.GuiSettings",
        lambda: GuiSettings(settings_path),
    )

    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    window.settings_theme_combo.setCurrentText("Light")
    window.settings_save_button.click()

    loaded = GuiSettings(settings_path)

    assert loaded.theme == "Light"


def test_main_window_reset_button_restores_system_theme(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.ini"

    settings = GuiSettings(settings_path)
    settings.theme = "Dark"
    settings.save()

    monkeypatch.setattr(
        "app.gui.main_window.GuiSettings",
        lambda: GuiSettings(settings_path),
    )

    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    window.settings_reset_button.click()

    assert window.settings_theme_combo.currentText() == "System"
    assert GuiSettings(settings_path).theme == "System"
from PyQt6.QtWidgets import QApplication

from app.gui.main_window import MainWindow
from app.gui.settings import GuiSettings


def test_main_window_applies_saved_dark_theme(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.ini"

    settings = GuiSettings(settings_path)
    settings.theme = "Dark"
    settings.save()

    monkeypatch.setattr(
        "app.gui.main_window.GuiSettings",
        lambda: GuiSettings(settings_path),
    )

    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert window.property("gui_theme") == "Dark"
from PyQt6.QtWidgets import QApplication

from app.gui.main_window import MainWindow
from app.gui.settings import GuiSettings


def test_main_window_applies_saved_light_theme(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.ini"

    settings = GuiSettings(settings_path)
    settings.theme = "Light"
    settings.save()

    monkeypatch.setattr(
        "app.gui.main_window.GuiSettings",
        lambda: GuiSettings(settings_path),
    )

    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert window.property("gui_theme") == "Light"


def test_main_window_save_applies_selected_theme(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.ini"

    monkeypatch.setattr(
        "app.gui.main_window.GuiSettings",
        lambda: GuiSettings(settings_path),
    )

    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    window.settings_theme_combo.setCurrentText("Dark")
    window.settings_save_button.click()

    assert window.property("gui_theme") == "Dark"


def test_main_window_reset_applies_system_theme(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.ini"

    settings = GuiSettings(settings_path)
    settings.theme = "Dark"
    settings.save()

    monkeypatch.setattr(
        "app.gui.main_window.GuiSettings",
        lambda: GuiSettings(settings_path),
    )

    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    window.settings_reset_button.click()

    assert window.property("gui_theme") == "System"
