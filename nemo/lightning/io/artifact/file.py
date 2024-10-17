import os
import shutil
from pathlib import Path
from pathlib_abc import PathBase
from typing import Union

from nemo.lightning.io.artifact.base import Artifact


class PathArtifact(Artifact[Path]):
    def dump(self, value: Path, absolute_dir: Path, relative_dir: Path) -> Path:
        new_value = copy_file(value, absolute_dir, relative_dir)
        return new_value

    def load(self, path: Path) -> Path:
        return path


class FileArtifact(Artifact[str]):
    def dump(self, value: str, absolute_dir: Path, relative_dir: Path) -> str:
        if not pathize(value).exists():
            # This is Artifact is just a string.
            self.skip = True
            return value
        new_value = copy_file(value, absolute_dir, relative_dir)
        return str(new_value)

    def load(self, path: str) -> str:
        return path


def pathize(s):
    if not isinstance(s, PathBase):
        return Path(s)
    return s


def copy_file(src: Union[os.PathLike, PathBase], path: Union[os.PathLike, PathBase], relative_dst: Union[os.PathLike, PathBase]):
    relative_path = pathize(relative_dst) / pathize(src).name
    output = pathize(path) / relative_path
    if output.exists():
        raise FileExistsError(f"Dst file already exists {str(output)}")
    if isinstance(output, (os.PathLike, Path)):
        shutil.copy2(src, output)
    else:
        with output.open('w') as writer, Path(src).open('r') as reader:
            writer.write(reader.read())
    return relative_path


class DirArtifact(Artifact[str]):
    def dump(self, value: str, absolute_dir: os.PathLike | PathBase, relative_dir: os.PathLike | PathBase) -> str:
        value = pathize(value)
        absolute_dir = pathize(absolute_dir)
        relative_dir = pathize(relative_dir)
        if not value.is_dir():
            return value

        relative_dir = relative_dir / value.name
        (absolute_dir / relative_dir).mkdir(exist_ok=True)
        for file in value.iterdir():
            copy_file(file, absolute_dir, relative_dir)
        return str(relative_dir)

    def load(self, path: str) -> str:
        return path


class DirOrStringArtifact(DirArtifact):
    def dump(self, value: str, absolute_dir: Path, relative_dir: Path) -> str:
        if not pathize(value).exists():
            # This is Artifact is just a string.
            self.skip = True
            return value
        return super().dump(value, absolute_dir, relative_dir)

    def load(self, path: str) -> str:
        return path
