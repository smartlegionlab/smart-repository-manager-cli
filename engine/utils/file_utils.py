# Copyright (©) 2025, Alexander Suvorov. All rights reserved.
import shutil
from pathlib import Path


class FileUtils:
    @staticmethod
    def safe_delete_directory(path: Path) -> bool:
        try:
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)
                return True
        except Exception as e:
            print(e)
            pass
        return False

    @staticmethod
    def get_directory_size(path: Path) -> int:
        total_size = 0
        if path.exists():
            for file in path.rglob('*'):
                if file.is_file():
                    total_size += file.stat().st_size
        return total_size

    @staticmethod
    def ensure_directory_exists(path: Path) -> bool:
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(e)
            return False
