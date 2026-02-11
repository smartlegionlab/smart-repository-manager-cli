import os
import zipfile
import tarfile
from abc import ABC, abstractmethod
from typing import ClassVar, Union, Optional
from pathlib import Path


class BaseArchiveCreator(ABC):

    @classmethod
    @abstractmethod
    def get_extension(cls) -> str:
        pass

    @classmethod
    def create(cls,
               folder_path: Union[str, Path],
               output_dir: Union[str, Path] = None,
               archive_name: Optional[str] = None) -> str:
        folder_path_str = str(folder_path) if isinstance(folder_path, Path) else folder_path

        if output_dir is None:
            output_dir = os.path.dirname(folder_path_str)
        else:
            output_dir = str(output_dir) if isinstance(output_dir, Path) else output_dir

        output_path = cls._get_output_path(folder_path_str, output_dir, archive_name)
        cls._create_archive(folder_path_str, output_path)
        return output_path

    @classmethod
    def _get_output_path(cls, folder_path: str, output_dir: str, archive_name: Optional[str] = None) -> str:
        if archive_name:
            if not archive_name.endswith(f".{cls.get_extension()}"):
                archive_name = f"{archive_name}.{cls.get_extension()}"
        else:
            folder_name = os.path.basename(folder_path.rstrip('/\\'))
            archive_name = f"{folder_name}.{cls.get_extension()}"

        return os.path.join(output_dir, archive_name)

    @classmethod
    @abstractmethod
    def _create_archive(cls, folder_path: str, output_path: str):
        pass

    @classmethod
    def _add_files_to_archive(cls, folder_path: str, add_file_func):
        folder_path = str(folder_path)
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, folder_path)
                add_file_func(file_path, arc_name)


class ZipArchiveCreator(BaseArchiveCreator):

    @classmethod
    def get_extension(cls) -> str:
        return "zip"

    @classmethod
    def _create_archive(cls, folder_path: str, output_path: str):
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            cls._add_files_to_archive(folder_path, zipf.write)


class TarArchiveCreator(BaseArchiveCreator):
    COMPRESSION_MODES: ClassVar[dict] = {
        '': 'w',
        'gz': 'w:gz',
        'bz2': 'w:bz2',
        'xz': 'w:xz'
    }

    @classmethod
    def get_extension(cls, compression: str = '') -> str:
        extensions = {'': 'tar', 'gz': 'tar.gz', 'bz2': 'tar.bz2', 'xz': 'tar.xz'}
        return extensions.get(compression, 'tar')

    @classmethod
    def create(cls,
               folder_path: Union[str, Path],
               output_dir: Union[str, Path] = None,
               compression: str = '',
               archive_name: Optional[str] = None) -> str:
        folder_path_str = str(folder_path) if isinstance(folder_path, Path) else folder_path

        if output_dir is None:
            output_dir = os.path.dirname(folder_path_str)
        else:
            output_dir = str(output_dir) if isinstance(output_dir, Path) else output_dir

        output_path = cls._get_output_path_with_compression(folder_path_str, output_dir, compression, archive_name)
        cls._create_archive(folder_path_str, output_path, compression)
        return output_path

    @classmethod
    def _get_output_path_with_compression(cls,
                                          folder_path: str,
                                          output_dir: str,
                                          compression: str,
                                          archive_name: Optional[str] = None) -> str:
        if archive_name:
            extension = cls.get_extension(compression)
            if not archive_name.endswith(f".{extension}"):
                archive_name = f"{archive_name}.{extension}"
        else:
            folder_name = os.path.basename(folder_path.rstrip('/\\'))
            extension = cls.get_extension(compression)
            archive_name = f"{folder_name}.{extension}"

        return os.path.join(output_dir, archive_name)

    @classmethod
    def _create_archive(cls, folder_path: str, output_path: str, compression: str = ''):
        mode = cls.COMPRESSION_MODES.get(compression, 'w')
        with tarfile.open(output_path, mode) as tarf:
            cls._add_files_to_archive(folder_path, tarf.add)


class ArchiveCreator:
    FORMATS: ClassVar[dict] = {
        'zip': ZipArchiveCreator,
        'tar': TarArchiveCreator,
        'tar.gz': TarArchiveCreator,
        'tgz': TarArchiveCreator,
        'tar.bz2': TarArchiveCreator,
        'tar.xz': TarArchiveCreator
    }

    @classmethod
    def create_archive(cls,
                       folder_path: Union[str, Path],
                       archive_format: str = 'zip',
                       output_dir: Union[str, Path] = None,
                       archive_name: Optional[str] = None,
                       **kwargs) -> str:
        creator_class = cls.FORMATS.get(archive_format)
        if not creator_class:
            raise ValueError(f"Unsupported archive format: {archive_format}")

        if creator_class == TarArchiveCreator:
            compression = 'gz' if archive_format in ['tar.gz',
                                                     'tgz'] else 'bz2' if archive_format == 'tar.bz2' else 'xz' \
                if archive_format == 'tar.xz' else ''
            return creator_class.create(folder_path, output_dir, compression, archive_name, **kwargs)
        else:
            return creator_class.create(folder_path, output_dir, archive_name, **kwargs)
