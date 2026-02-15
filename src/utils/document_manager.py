import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import json
import pandas as pd


class DocumentManager:
    def __init__(self, upload_dir: str = "data/uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.upload_dir / "metadata.json"
        
        if not self.metadata_file.exists():
            self._save_metadata({})
    
    def _load_metadata(self) -> Dict:
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_metadata(self, metadata: Dict):
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar metadata: {e}")
    
    def save_uploaded_file(self, uploaded_file, username: str, description: str = "") -> tuple:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_id = f"{username}_{timestamp}_{uploaded_file.name}"
            file_path = self.upload_dir / file_id
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            metadata = self._load_metadata()
            metadata[file_id] = {
                'original_name': uploaded_file.name,
                'username': username,
                'description': description,
                'upload_date': datetime.now().isoformat(),
                'size_bytes': uploaded_file.size,
                'type': uploaded_file.type
            }
            self._save_metadata(metadata)
            
            return True, f"Arquivo '{uploaded_file.name}' enviado com sucesso!", file_id
            
        except Exception as e:
            return False, f"Erro ao salvar arquivo: {str(e)}", None
    
    def get_user_files(self, username: str) -> List[Dict]:
        metadata = self._load_metadata()
        
        user_files = []
        for file_id, info in metadata.items():
            if info['username'] == username:
                user_files.append({
                    'file_id': file_id,
                    **info
                })
        user_files.sort(key=lambda x: x['upload_date'], reverse=True)
        
        return user_files
    
    def get_all_files(self) -> List[Dict]:

        metadata = self._load_metadata()
        
        all_files = []
        for file_id, info in metadata.items():
            all_files.append({
                'file_id': file_id,
                **info
            })
        
        all_files.sort(key=lambda x: x['upload_date'], reverse=True)
        
        return all_files
    
    def delete_file(self, file_id: str, username: str, is_admin: bool = False) -> tuple:
        metadata = self._load_metadata()
        
        if file_id not in metadata:
            return False, "Arquivo não encontrado"

        if not is_admin and metadata[file_id]['username'] != username:
            return False, "Sem permissão para deletar este arquivo"
        
        try:
            file_path = self.upload_dir / file_id
            if file_path.exists():
                file_path.unlink()
            
            original_name = metadata[file_id]['original_name']
            del metadata[file_id]
            self._save_metadata(metadata)
            
            return True, f"Arquivo '{original_name}' removido com sucesso!"
            
        except Exception as e:
            return False, f"Erro ao remover arquivo: {str(e)}"
    
    def load_csv_to_dataframe(self, file_id: str) -> Optional[pd.DataFrame]:
        try:
            file_path = self.upload_dir / file_id
            
            if not file_path.exists():
                return None
            
            for encoding in ['utf-8', 'latin-1', 'iso-8859-1']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    return df
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"Erro ao carregar CSV: {e}")
            return None
    
    def validate_medication_csv(self, df: pd.DataFrame) -> tuple:
        required_columns = ['medicamento', 'data', 'consumo', 'estoque_atual']
        
        if df is None or df.empty:
            return False, "Arquivo vazio ou inválido"
        
        missing_cols = set(required_columns) - set(df.columns)
        
        if missing_cols:
            return False, f"Colunas faltando: {', '.join(missing_cols)}"
        
        return True, "CSV válido!"
    
    def get_file_path(self, file_id: str) -> Optional[Path]:
        file_path = self.upload_dir / file_id
        
        if file_path.exists():
            return file_path
        
        return None
