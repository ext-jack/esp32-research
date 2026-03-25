"""Extract files from an ESP32 FSFROG image."""

from __future__ import annotations

import argparse
import gzip
from pathlib import Path
from struct import Struct

ESPFS_MAGIC = 726877765
DEFAULT_INPUT_PATH = "sample3.bin"
DEFAULT_OUTPUT_DIR = "result"

FS_HEADER = Struct("<IBBHIHH")
DIR_HEADER = Struct("<BBHHH")
FILE_HEADER = Struct("<BBHHHIIHBB")
SORTTABLE_ENTRY = Struct("<I")
SINGLE_BYTE = Struct("<B")

OBJECT_TYPE_DIR = 1
COMPRESSION_HEATSHRINK = 1
FLAG_GZIP = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract files from an ESP32 FSFROG filesystem image."
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        default=DEFAULT_INPUT_PATH,
        help=f"Path to the FSFROG binary image (default: {DEFAULT_INPUT_PATH})",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to write extracted contents to (default: {DEFAULT_OUTPUT_DIR})",
    )
    return parser.parse_args()


def read_offsets(file_obj, object_count: int) -> list[int]:
    return [SORTTABLE_ENTRY.unpack(file_obj.read(SORTTABLE_ENTRY.size))[0] for _ in range(object_count)]


def decompress_file(file_content: bytes, compression: int, flags: int) -> bytes:
    if compression == COMPRESSION_HEATSHRINK:
        try:
            import heatshrink2
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "heatshrink2 is required to decompress this file content"
            ) from exc

        file_content = heatshrink2.decompress(file_content)

    if flags == FLAG_GZIP:
        try:
            file_content = gzip.decompress(file_content)
        except gzip.BadGzipFile:
            pass

    return file_content


def read_object_entry(file_obj, offset: int, output_dir: Path) -> dict:
    file_obj.seek(offset)
    object_type = SINGLE_BYTE.unpack(file_obj.read(SINGLE_BYTE.size))[0]

    if object_type == OBJECT_TYPE_DIR:
        obj_type, _, index, path_len, _ = DIR_HEADER.unpack(file_obj.read(DIR_HEADER.size))
        path = file_obj.read(path_len).decode("utf-8").rstrip("\x00")
        entry = {
            "type": obj_type,
            "index": index,
            "path_len": path_len,
            "path": path,
        }
        (output_dir / path).mkdir(parents=True, exist_ok=True)
        return entry

    (
        obj_type,
        _,
        index,
        path_len,
        _,
        data_len,
        file_len,
        flags,
        compression,
        _,
    ) = FILE_HEADER.unpack(file_obj.read(FILE_HEADER.size))

    path = file_obj.read(path_len).decode("utf-8").rstrip("\x00")
    file_content = file_obj.read(file_len)
    file_content = decompress_file(file_content, compression, flags)

    output_path = output_dir / path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(file_content)

    return {
        "type": obj_type,
        "index": index,
        "path_len": path_len,
        "path": path,
        "flags": flags,
        "compression": compression,
        "data_len": data_len,
    }


def parse_image(input_path: Path, output_dir: Path) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)

    with input_path.open("rb") as file_obj:
        (
            magic,
            header_len,
            version_major,
            version_minor,
            binary_len,
            object_count,
            _,
        ) = FS_HEADER.unpack(file_obj.read(FS_HEADER.size))

        if magic != ESPFS_MAGIC:
            raise ValueError(f"Unexpected magic value: {magic}")

        data_offset = FS_HEADER.size + (object_count * SORTTABLE_ENTRY.size)
        file_obj.seek(data_offset)
        offsets = read_offsets(file_obj, object_count)

        print(f"Magic: {magic}")
        print(f"Version: {version_major}.{version_minor}")
        print(f"header_len: {header_len}")
        print(f"bin_len: {binary_len}")
        print(f"num_objects: {object_count}")
        print(f"Offset table starts at: {data_offset}")
        print(f"Max object offset: {max(offsets) if offsets else 'n/a'}")

        entries = [read_object_entry(file_obj, offset, output_dir) for offset in offsets]

    return entries


def main() -> int:
    args = parse_args()
    input_path = Path(args.input_file)
    output_dir = Path(args.output_dir)

    if not input_path.is_file():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    entries = parse_image(input_path, output_dir)
    for entry in entries:
        print(entry)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
