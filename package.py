"""Bundle only intended HW3 source, documentation and result artifacts."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def main():
    root = Path(__file__).resolve().parent
    output = root / "HW3_solution.zip"
    files = [root / name for name in ("main.py", "verify.py", "package.py", "README.md",
                                      "EXECUTION_LOG.md", "HW3.pdf", ".gitignore")]
    for directory in ("hw3", "tests", "results"):
        files.extend(p for p in (root / directory).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    for file in files:
        if not file.is_file():
            raise FileNotFoundError(file)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for file in sorted(files):
            archive.write(file, file.relative_to(root).as_posix())
    with ZipFile(output) as archive:
        corrupt = archive.testzip()
        if corrupt is not None:
            raise RuntimeError(f"Corrupt ZIP entry: {corrupt}")
    print(f"Created {output.name}: {len(files)} files, {output.stat().st_size:,} bytes; integrity OK.")


if __name__ == "__main__":
    main()
