#!/usr/bin/env python3
"""Regenerates chunks/ from a working tree of the WEB proxy kit.

The kit ships as base64 chunks of a gzipped self-extracting script so the whole
patch, including the Java transport, is one reviewable, reproducible artifact.
Edit the real files, then:

    python3 tools/pack.py <source-directory>

where <source-directory> holds WebProxyTransport.java, apply_web_proxy_patch.py,
protocol_vectors_test.py and selftest/. Reconstruct with:

    cat chunks/*.txt | base64 --decode | gzip --decompress > ci_bundle.py && python3 ci_bundle.py
"""
from __future__ import annotations

import argparse
import base64
import gzip
import pathlib
import zlib

CHUNK_SIZE = 3531


def build_bundle(source: pathlib.Path) -> str:
    files = sorted(p for p in source.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    if not files:
        raise SystemExit(f"ERROR: no files under {source}")
    lines = [
        "#!/usr/bin/env python3",
        '"""Reconstructs the Android WEB proxy kit from chunks/.',
        "",
        "Generated file: edit the sources, then regenerate chunks/ with tools/pack.py.",
        '"""',
        "from pathlib import Path",
        "import base64, zlib",
        "FILES = {",
    ]
    for path in files:
        name = path.relative_to(source).as_posix()
        blob = base64.b64encode(zlib.compress(path.read_bytes(), 9)).decode()
        lines.append(f"{name!r}: {blob!r},")
    lines += [
        "}",
        "for name, data in FILES.items():",
        "    target = Path(name)",
        "    target.parent.mkdir(parents=True, exist_ok=True)",
        "    target.write_bytes(zlib.decompress(base64.b64decode(data)))",
        "print(f'restored {len(FILES)} files')",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="directory holding the kit sources")
    parser.add_argument("--out", default="chunks", help="chunk directory to rewrite")
    args = parser.parse_args()

    bundle = build_bundle(pathlib.Path(args.source).resolve())
    # mtime=0 keeps the output byte-identical for identical input.
    encoded = base64.b64encode(gzip.compress(bundle.encode(), 9, mtime=0)).decode()

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob("*.txt"):
        stale.unlink()
    chunks = [encoded[i:i + CHUNK_SIZE] for i in range(0, len(encoded), CHUNK_SIZE)]
    for index, chunk in enumerate(chunks):
        (out / f"{index:02d}.txt").write_text(chunk)
    print(f"wrote {len(chunks)} chunks ({len(bundle)} bytes of bundle) to {out}")


if __name__ == "__main__":
    main()
