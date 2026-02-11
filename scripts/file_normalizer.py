#!/usr/bin/env python3
"""
File Name Normalizer
Handles file name special characters and conversions for sermon organization.
"""

import re
import unicodedata
from pathlib import Path


def normalize_sermon_name(name: str) -> str:
    """
    Normalize sermon name to filesystem-safe format.

    Transformations:
    - Apostrophes: ' -> (removed)
    - Ampersands: & -> _and_
    - Colons, semicolons: : ; -> _
    - Spaces: ' ' -> _
    - Multiple underscores: __ -> _
    - Removes leading/trailing underscores

    Examples:
        "Jesus' Model" -> "Jesus_Model"
        "Work & Grace" -> "Work_and_Grace"
        "Love: The Foundation" -> "Love_The_Foundation"
    """
    # Remove or replace special characters
    name = name.replace("'", "")  # Remove apostrophes
    name = name.replace("'", "")  # Remove curly apostrophes
    name = name.replace("'", "")  # Remove curly apostrophes (reverse)
    name = name.replace("&", "_and_")  # Ampersand to 'and'
    name = name.replace(":", "_")  # Colon to underscore
    name = name.replace(";", "_")  # Semicolon to underscore
    name = name.replace(",", "")  # Remove commas
    name = name.replace("(", "")  # Remove parentheses
    name = name.replace(")", "")
    name = name.replace("[", "")  # Remove brackets
    name = name.replace("]", "")
    name = name.replace("?", "")  # Remove question marks
    name = name.replace("!", "")  # Remove exclamation marks
    name = name.replace(""", "")  # Remove curly quotes
    name = name.replace(""", "")
    name = name.replace("\"", "")  # Remove straight quotes

    # Replace spaces with underscores
    name = name.replace(" ", "_")

    # Replace multiple underscores with single
    name = re.sub(r'_+', '_', name)

    # Remove leading/trailing underscores
    name = name.strip('_')

    return name


def to_folder_name(md_filename: str) -> str:
    """
    Convert MD filename to folder name.

    Removes .md extension and normalizes.

    Examples:
        "A_New_Heart.md" -> "A_New_Heart"
        "Jesus' Model.md" -> "Jesus_Model"
    """
    # Remove extension
    if md_filename.endswith('.md'):
        name = md_filename[:-3]
    else:
        name = md_filename

    # Normalize
    return normalize_sermon_name(name)


def from_title(title: str) -> str:
    """
    Convert sermon title to filesystem-safe folder name.

    This is the main function to use when creating new sermon folders
    from titles extracted from metadata or RSS feeds.

    Examples:
        "A New Heart" -> "A_New_Heart"
        "Jesus' Model of Spirituality" -> "Jesus_Model_of_Spirituality"
    """
    return normalize_sermon_name(title)


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize any filename for cross-platform compatibility.

    Removes:
    - Path separators (/, \)
    - Null bytes
    - Control characters

    Limits length to max_length (default 255 for most filesystems).
    """
    # Remove null bytes
    filename = filename.replace('\x00', '')

    # Remove path separators
    filename = filename.replace('/', '_')
    filename = filename.replace('\\', '_')

    # Remove control characters
    filename = ''.join(c for c in filename if ord(c) >= 32 or c == '\n')

    # Normalize unicode (NFC form)
    filename = unicodedata.normalize('NFC', filename)

    # Trim to max length
    if len(filename) > max_length:
        # Try to preserve extension
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
            max_name_length = max_length - len(ext) - 1
            filename = name[:max_name_length] + '.' + ext
        else:
            filename = filename[:max_length]

    return filename


def is_valid_sermon_folder(path: Path) -> bool:
    """
    Check if a folder appears to be a valid sermon folder.

    Valid sermon folder contains at least:
    - metadata.json
    - transcript.md OR audio.mp3
    """
    if not path.is_dir():
        return False

    has_metadata = (path / "metadata.json").exists()
    has_content = (path / "transcript.md").exists() or (path / "audio.mp3").exists()

    return has_metadata and has_content


def find_sermon_folders(base_dir: Path) -> list[Path]:
    """
    Find all valid sermon folders in a directory.

    Returns sorted list of paths.
    """
    if not base_dir.is_dir():
        return []

    folders = []
    for item in base_dir.iterdir():
        if is_valid_sermon_folder(item):
            folders.append(item)

    return sorted(folders)


def get_legacy_md_files(base_dir: Path) -> list[Path]:
    """
    Find all legacy sermon .md files in a directory.

    Returns sorted list of paths, excluding:
    - README.md
    - CHANGELOG.md
    - Other non-sermon MD files (ALL_CAPS.md pattern)
    """
    if not base_dir.is_dir():
        return []

    md_files = []
    for item in base_dir.glob("*.md"):
        # Exclude documentation files
        name = item.stem
        if name.isupper():  # ALL_CAPS files are docs
            continue
        if name in ['README', 'CHANGELOG', 'LICENSE', 'CONTRIBUTING']:
            continue

        md_files.append(item)

    return sorted(md_files)


def main():
    """CLI for testing file normalizer"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python file_normalizer.py <command> [args]")
        print("\nCommands:")
        print("  normalize <name>     - Normalize a sermon name")
        print("  folder <md_file>     - Convert MD filename to folder name")
        print("  title <title>        - Convert title to folder name")
        print("  find-legacy <dir>    - Find legacy MD files")
        print("  find-folders <dir>   - Find sermon folders")
        print("\nExamples:")
        print("  python file_normalizer.py normalize \"Jesus' Model\"")
        print("  python file_normalizer.py folder A_New_Heart.md")
        print("  python file_normalizer.py find-legacy .")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == 'normalize':
            name = sys.argv[2]
            print(normalize_sermon_name(name))

        elif command == 'folder':
            md_file = sys.argv[2]
            print(to_folder_name(md_file))

        elif command == 'title':
            title = sys.argv[2]
            print(from_title(title))

        elif command == 'find-legacy':
            base_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('.')
            files = get_legacy_md_files(base_dir)
            print(f"Found {len(files)} legacy sermon files:")
            for f in files:
                print(f"  {f.name}")

        elif command == 'find-folders':
            base_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('.')
            folders = find_sermon_folders(base_dir)
            print(f"Found {len(folders)} sermon folders:")
            for f in folders:
                print(f"  {f.name}")

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
