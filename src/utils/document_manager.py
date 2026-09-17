"""Local CSV storage with validation before persistence and opaque filenames."""

import io
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd

from src.preprocessing.cleaning import DataCleaner


class DocumentManager:
    def __init__(self, upload_dir="data/uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.upload_dir / "metadata.json"

    def _load_metadata(self):
        if not self.metadata_file.exists():
            return {}
        return json.loads(self.metadata_file.read_text(encoding="utf-8"))

    def _save_metadata(self, metadata):
        temporary = self.metadata_file.with_suffix(".tmp")
        temporary.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.metadata_file)

    def validate_medication_csv(self, df):
        try:
            DataCleaner().clean(df)
            return True, "Estrutura e histórico mensal válidos."
        except ValueError as error:
            return False, str(error)

    def save_uploaded_file(self, uploaded_file, username, description=""):
        payload = uploaded_file.getvalue()
        if len(payload) > 10 * 1024 * 1024:
            return False, "O limite por arquivo é 10 MB.", None
        try:
            df = pd.read_csv(io.BytesIO(payload), sep=None, engine="python")
            valid, message = self.validate_medication_csv(df)
            if not valid:
                return False, message, None
            file_id = f"{uuid4().hex}.csv"
            destination = self.upload_dir / file_id
            # Persist a normalized CSV so loading is independent of source delimiters.
            df.to_csv(destination, index=False)
            metadata = self._load_metadata()
            metadata[file_id] = {
                "original_name": Path(uploaded_file.name).name,
                "username": username,
                "description": description,
                "upload_date": datetime.now(timezone.utc).isoformat(),
                "size_bytes": len(payload),
                "type": "text/csv",
            }
            self._save_metadata(metadata)
            return True, "Documento salvo. Selecione-o no dashboard.", file_id
        except (ValueError, OSError, UnicodeError) as error:
            return False, f"Falha ao salvar documento: {error}", None

    def get_all_files(self):
        return sorted(
            [dict(file_id=key, **info) for key, info in self._load_metadata().items()],
            key=lambda item: item["upload_date"],
            reverse=True,
        )

    def get_user_files(self, username):
        return [item for item in self.get_all_files() if item["username"] == username]

    def get_file_path(self, file_id):
        if file_id not in self._load_metadata():
            return None
        path = (self.upload_dir / file_id).resolve()
        if path.parent != self.upload_dir.resolve():
            return None
        return path if path.is_file() else None

    def load_csv_to_dataframe(self, file_id):
        path = self.get_file_path(file_id)
        if path is None:
            raise ValueError("Documento não encontrado.")
        return pd.read_csv(path, sep=None, engine="python")

    def delete_file(self, file_id, username, is_admin=False):
        metadata = self._load_metadata()
        if file_id not in metadata:
            return False, "Documento não encontrado."
        if metadata[file_id]["username"] != username and not is_admin:
            return False, "Sem permissão para excluir este documento."
        path = self.get_file_path(file_id)
        if path:
            path.unlink()
        del metadata[file_id]
        self._save_metadata(metadata)
        return True, "Documento excluído."
