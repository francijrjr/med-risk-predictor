from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_and_empty_filters():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not app.exception
    assert not app.error
    app.multiselect[1].set_value([]).run()
    assert not app.exception
    assert len(app.info) > 0


def test_profile_navigation():
    app = AppTest.from_file(str(ROOT / "app_auth.py"), default_timeout=60)
    app.session_state["user"] = {
        "username": "test",
        "full_name": "Pessoa de teste",
        "email": "test@example.org",
        "role": "user",
    }
    app.run()
    assert not app.exception
    app.radio[0].set_value("Perfil").run()
    assert not app.exception
    assert any("Minha conta" in item.value for item in app.markdown)
