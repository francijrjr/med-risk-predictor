"""Local prototype accounts. Existing SHA-256 hashes migrate after valid login."""

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path


class AuthManager:
    ITERATIONS = 600_000

    def __init__(self, users_file="data/users.json"):
        self.users_file = Path(users_file)
        self.users_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_users(self):
        if not self.users_file.exists():
            return {}
        return json.loads(self.users_file.read_text(encoding="utf-8"))

    def _save_users(self, users):
        temporary = self.users_file.with_suffix(".tmp")
        temporary.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.users_file)

    def _hash_password(self, password):
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), self.ITERATIONS
        ).hex()
        return "$".join(["pbkdf2_sha256", str(self.ITERATIONS), salt, digest])

    @staticmethod
    def _verify_password(password, stored):
        if stored.startswith("pbkdf2_sha256$"):
            _, iterations, salt, expected = stored.split("$")
            actual = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), salt.encode(), int(iterations)
            ).hex()
        else:
            expected = stored
            actual = hashlib.sha256(password.encode()).hexdigest()
        return hmac.compare_digest(actual, expected)

    def register_user(self, username, password, email, full_name):
        users = self._load_users()
        username = username.strip()
        if len(username) < 3:
            return False, "Nome de usuário deve ter no mínimo 3 caracteres."
        if username in users:
            return False, "Nome de usuário já existe."
        if len(password) < 8:
            return False, "Senha deve ter no mínimo 8 caracteres."
        if "@" not in email or not full_name.strip():
            return False, "Informe nome e email válidos."
        users[username] = {
            "password_hash": self._hash_password(password),
            "email": email,
            "full_name": full_name,
            "role": "user",
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save_users(users)
        return True, "Conta criada. Entre com seu usuário e senha."

    def authenticate(self, username, password):
        users = self._load_users()
        user = users.get(username)
        if not user or not user.get("active", True):
            return False, None
        if not self._verify_password(password, user["password_hash"]):
            return False, None
        if not user["password_hash"].startswith("pbkdf2_sha256$"):
            user["password_hash"] = self._hash_password(password)
            self._save_users(users)
        return True, {
            "username": username,
            **{key: user.get(key) for key in ("email", "full_name", "role", "created_at")},
        }

    def change_password(self, username, old_password, new_password):
        success, _ = self.authenticate(username, old_password)
        if not success:
            return False, "Senha atual incorreta."
        if len(new_password) < 8:
            return False, "Nova senha deve ter no mínimo 8 caracteres."
        users = self._load_users()
        users[username]["password_hash"] = self._hash_password(new_password)
        self._save_users(users)
        return True, "Senha alterada."
