import json
import hashlib
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict


class AuthManager:
    def __init__(self, users_file: str = "data/users.json"):
        self.users_file = Path(users_file)
        self.users_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.users_file.exists():
            self._save_users({})
    
    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _load_users(self) -> Dict:
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar usuários: {e}")
            return {}
    
    def _save_users(self, users: Dict):
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar usuários: {e}")
    
    def register_user(self, username: str, password: str, email: str, full_name: str) -> tuple:
        users = self._load_users()
        if not username or len(username) < 3:
            return False, "Nome de usuário deve ter no mínimo 3 caracteres"
        
        if username in users:
            return False, "Nome de usuário já existe"
        
        if not password or len(password) < 6:
            return False, "Senha deve ter no mínimo 6 caracteres"
        
        if not email or '@' not in email:
            return False, "Email inválido"
        users[username] = {
            'password_hash': self._hash_password(password),
            'email': email,
            'full_name': full_name,
            'created_at': datetime.now().isoformat(),
            'role': 'user',
            'active': True
        }
        
        self._save_users(users)
        return True, "Usuário registrado com sucesso!"
    
    def authenticate(self, username: str, password: str) -> tuple:
        users = self._load_users()
        
        if username not in users:
            return False, None
        
        user = users[username]
        
        if not user.get('active', True):
            return False, None
        
        password_hash = self._hash_password(password)
        
        if password_hash == user['password_hash']:
            user_data = {
                'username': username,
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user.get('role', 'user'),
                'created_at': user.get('created_at')
            }
            return True, user_data
        
        return False, None
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        users = self._load_users()
        
        if username not in users:
            return None
        
        user = users[username]
        return {
            'username': username,
            'email': user['email'],
            'full_name': user['full_name'],
            'role': user.get('role', 'user'),
            'created_at': user.get('created_at')
        }
    
    def change_password(self, username: str, old_password: str, new_password: str) -> tuple:
        success, _ = self.authenticate(username, old_password)
        
        if not success:
            return False, "Senha atual incorreta"
        
        if len(new_password) < 6:
            return False, "Nova senha deve ter no mínimo 6 caracteres"
        
        users = self._load_users()
        users[username]['password_hash'] = self._hash_password(new_password)
        self._save_users(users)
        
        return True, "Senha alterada com sucesso!"
    
    def create_admin_user(self):
        users = self._load_users()
        
        if 'admin' not in users:
            users['admin'] = {
                'password_hash': self._hash_password('admin123'),
                'email': 'admin@saude.gov.br',
                'full_name': 'Administrador do Sistema',
                'created_at': datetime.now().isoformat(),
                'role': 'admin',
                'active': True
            }
            self._save_users(users)
            print("Usuário administrador criado: admin / admin123")
