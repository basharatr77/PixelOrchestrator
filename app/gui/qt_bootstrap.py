from pathlib import Path
import ctypes
import os
import sys


PYQT6_DIR = Path(sys.prefix) / "Lib" / "site-packages" / "PyQt6"
QT6_BIN = PYQT6_DIR / "Qt6" / "bin"


def bootstrap_qt6():
    """
    Prepare the PyQt6 Qt6 DLL environment on Windows.

    This must run before importing PyQt6.QtCore / QtWidgets.
    """

    if os.name != "nt":
        return

    if not QT6_BIN.is_dir():
        raise RuntimeError(
            f"PyQt6 Qt6 DLL directory does not exist:\n{QT6_BIN}"
        )

    qt_bin = str(QT6_BIN)

    # Python 3.8+ Windows DLL search path.
    os.add_dll_directory(qt_bin)

    # Keep Qt6 bin first in PATH as an additional compatibility measure.
    current_path = os.environ.get("PATH", "")
    path_entries = current_path.split(os.pathsep)

    if qt_bin not in path_entries:
        os.environ["PATH"] = qt_bin + os.pathsep + current_path

    # Preload the Qt libraries proven to work in Step 8C-30/31.
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    LoadLibraryExW = kernel32.LoadLibraryExW
    LoadLibraryExW.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_void_p,
        ctypes.c_uint32,
    ]
    LoadLibraryExW.restype = ctypes.c_void_p

    LOAD_WITH_ALTERED_SEARCH_PATH = 0x00000008

    for dll_name in (
        "Qt6Core.dll",
        "Qt6Gui.dll",
        "Qt6Widgets.dll",
    ):
        dll_path = QT6_BIN / dll_name

        handle = LoadLibraryExW(
            str(dll_path),
            None,
            LOAD_WITH_ALTERED_SEARCH_PATH,
        )

        if not handle:
            error = ctypes.get_last_error()
            raise OSError(
                error,
                f"Could not load {dll_path}: {ctypes.WinError(error)}",
            )


bootstrap_qt6()
