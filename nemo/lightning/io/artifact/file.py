# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil
from pathlib import Path
from pathlib_abc import PathBase
from typing import Union
import fiddle as fdl

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
            return fdl.Config(FileArtifact, attr=value, skip=True)
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
    output = pathize(path) / str(relative_path)
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
        (absolute_dir / str(relative_dir)).mkdir(exist_ok=True)
        for file in value.iterdir():
            copy_file(file, absolute_dir, relative_dir)
        return str(relative_dir)

    def load(self, path: str) -> str:
        return path


class DirOrStringArtifact(DirArtifact):
    def dump(self, value: str, absolute_dir: Path, relative_dir: Path) -> str:
        if not pathize(value).exists():
            # This is Artifact is just a string.
            return fdl.Config(DirOrStringArtifact, attr=value, skip=True)
        return super().dump(value, absolute_dir, relative_dir)

    def load(self, path: str) -> str:
        return path
