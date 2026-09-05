import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("app.data.repository.get_app_dir", lambda: str(tmp_path))
    monkeypatch.setattr("app.config.get_app_dir", lambda: str(tmp_path))


@pytest.fixture(scope="session")
def qapp():
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def messages(monkeypatch):
    from PyQt5.QtWidgets import QMessageBox
    calls = []
    for name in ("information", "warning", "critical", "question"):
        def respond(*args, _name=name, **kwargs):
            calls.append((_name, args[1], args[2]))
            return QMessageBox.No if _name == "question" else QMessageBox.Ok
        monkeypatch.setattr(QMessageBox, name, respond)
    return calls
