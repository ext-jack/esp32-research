# esp32-research

Utilities and notes for inspecting ESP32 firmware artifacts.

## FSFROG Parser

`esp32-fs-frog-parser.py` extracts files and directories from an ESP32 FSFROG filesystem image.

The parser currently:

- Reads the FSFROG filesystem header and validates the file magic.
- Parses the object offset table.
- Recreates directory entries in an output folder.
- Extracts file entries to disk.
- Decompresses Heatshrink-compressed file content when needed.
- Attempts gzip decompression for entries marked with the gzip flag.

## Requirements

- Python 3
- `heatshrink2` for images that contain Heatshrink-compressed files

Install the optional dependency with:

```bash
pip install heatshrink2
```

The script can still show `--help` and parse uncompressed content without `heatshrink2`, but it will fail if an extracted file requires Heatshrink decompression and the module is not installed.

## Usage

Run the parser with the input image path:

```bash
python3 esp32-fs-frog-parser.py firmware.bin
```

Write extracted files to a custom directory:

```bash
python3 esp32-fs-frog-parser.py firmware.bin --output-dir extracted
```

If no input file is provided, the script defaults to:

```text
sample3.bin
```

If no output directory is provided, the script defaults to:

```text
result
```

You can also view the built-in CLI help:

```bash
python3 esp32-fs-frog-parser.py --help
```

## What The Script Prints

During extraction the parser prints:

- Filesystem metadata such as magic, version, binary length, and object count.
- Offset table details.
- A dictionary summary for each extracted directory or file entry.

## Output

Extracted content is written to the selected output directory, preserving the paths stored in the FSFROG image.

For example, if the image contains:

```text
www/index.html
config/settings.json
```

the parser will recreate those paths under the output directory.

## Limitations

- The parser is focused on extraction rather than full filesystem analysis.
- Gzip decompression is attempted only for entries marked with the gzip flag.
- Invalid or unexpected images raise an error when the FSFROG magic does not match.

