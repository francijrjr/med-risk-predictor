import hashlib
import io
import json

from src.utils.auth import AuthManager
from src.utils.document_manager import DocumentManager


class Upload(io.BytesIO):
    name = "../../historico.csv"


def test_uploaded_document_is_validated_and_can_feed_analysis(tmp_path):
    manager = DocumentManager(tmp_path)
    payload = Upload(b"medicamento,data,consumo,estoque_atual\nMED,2024-01,100,120\n")
    success, _, file_id = manager.save_uploaded_file(payload, "alice")
    assert success
    assert manager.get_file_path(file_id).parent == tmp_path
    assert manager.load_csv_to_dataframe(file_id).iloc[0]["consumo"] == 100
    assert not manager.get_user_files("bob")
    assert not manager.delete_file(file_id, "bob")[0]
    assert manager.delete_file(file_id, "alice")[0]


def test_invalid_upload_is_not_saved(tmp_path):
    manager = DocumentManager(tmp_path)
    success, _, _ = manager.save_uploaded_file(Upload(b"wrong\nvalue\n"), "alice")
    assert not success
    assert manager.get_all_files() == []


def test_legacy_password_migrates_only_after_valid_login(tmp_path):
    path = tmp_path / "users.json"
    original = hashlib.sha256(b"oldpassword").hexdigest()
    path.write_text(
        json.dumps(
            {
                "alice": {
                    "password_hash": original,
                    "role": "user",
                    "full_name": "Alice",
                    "email": "a@example.org",
                }
            }
        )
    )
    auth = AuthManager(path)
    assert not auth.authenticate("alice", "wrong")[0]
    assert json.loads(path.read_text())["alice"]["password_hash"] == original
    assert auth.authenticate("alice", "oldpassword")[0]
    assert json.loads(path.read_text())["alice"]["password_hash"].startswith("pbkdf2_sha256$")
    assert auth.change_password("alice", "oldpassword", "newpassword")[0]
    assert not auth.authenticate("alice", "oldpassword")[0]
    assert auth.authenticate("alice", "newpassword")[0]
