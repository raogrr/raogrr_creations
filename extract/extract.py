#!/usr/bin/env python3
"""
extract.py — Extract a binary file or any file from any compressed archive.
Supports: .tar, .tar.gz, .tgz, .tar.bz2, .tar.xz, .zip, .gz, .bz2, .xz
Suppport contact: Gururaj Rao <grao1@visteon.com>

# Usage
#python3 extract.py openssl-1.0.1t.tar.gz -l

# Extract a specific file
#python3 extract.py images.zip -f qnx6-oem.img -o /tmp/out
#python3 extract.py images.zip -f mahindra.img -o /tmp/out
#python3 extract.py openssl-1.0.1t.tar.gz -f libssl.a -o /tmp/out

# Checksum without extracting
#python3 extract.py openssl-1.0.1t.tar.gz -f Makefile --hash sha256
"""
 
import argparse
import gzip
import bz2
import lzma
import hashlib
import sys
import tarfile
import zipfile
from pathlib import Path
 
 
# ── Format detection ───────────────────────────────────────────────────────────
 
def detect_format(path):
    name = path.name.lower()
    # Check by content first (most reliable)
    try:
        if tarfile.is_tarfile(str(path)):
            return "tar"
    except Exception:
        pass
    if zipfile.is_zipfile(str(path)):
        return "zip"
    # Fall back to extension
    if name.endswith((".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz", ".tar")):
        return "tar"
    if name.endswith(".gz"):
        return "gz"
    if name.endswith(".bz2"):
        return "bz2"
    if name.endswith((".xz", ".lzma")):
        return "xz"
    if name.endswith(".zip"):
        return "zip"
    raise ValueError(f"Unsupported format: {path.name}")
 
 
# ── Member matching ────────────────────────────────────────────────────────────
 
def find_match(name, query):
    """Match by exact path, basename, or suffix."""
    return (
        name == query
        or Path(name).name == query
        or name.endswith(query)
    )
 
 
# ── Stream helper ──────────────────────────────────────────────────────────────
 
def stream_chunks(fileobj, chunk_size):
    while True:
        chunk = fileobj.read(chunk_size)
        if not chunk:
            break
        yield chunk
 
 
# ── Output writer ──────────────────────────────────────────────────────────────
 
def write_output(fileobj, name, size, args):
    # Hash mode — checksum only, no extraction
    if args.hash:
        h = hashlib.new(args.hash)
        for chunk in stream_chunks(fileobj, args.chunk_size):
            h.update(chunk)
        size_label = "  ({:,} bytes)".format(size) if size else ""
        print("{}  {}{}".format(h.hexdigest(), name, size_label))
        return
 
    # Stdout mode — stream raw bytes
    if args.stdout:
        for chunk in stream_chunks(fileobj, args.chunk_size):
            sys.stdout.buffer.write(chunk)
        return
 
    # Disk mode — write to file
    out = (args.output_dir / Path(name).name).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as f:
        for chunk in stream_chunks(fileobj, args.chunk_size):
            f.write(chunk)
    print("extracted: {}  ({:,} bytes)".format(out, out.stat().st_size))
 
 
# ── Format handlers ────────────────────────────────────────────────────────────
 
def handle_tar(archive, args):
    with tarfile.open(str(archive), "r:*") as tar:
        members = [m for m in tar.getmembers() if m.isfile()]
 
        if args.list:
            list_tar(members)
            return
 
        member = next((m for m in members if find_match(m.name, args.filename)), None)
        if member is None:
            raise FileNotFoundError(
                "'{}' not found in archive.\nUse -l to list available files.".format(args.filename)
            )
        write_output(tar.extractfile(member), member.name, member.size, args)
 
 
def handle_zip(archive, args):
    with zipfile.ZipFile(str(archive), "r") as zf:
        members = [m for m in zf.infolist() if not m.filename.endswith("/")]
 
        if args.list:
            list_zip(members)
            return
 
        member = next((m for m in members if find_match(m.filename, args.filename)), None)
        if member is None:
            raise FileNotFoundError(
                "'{}' not found in archive.\nUse -l to list available files.".format(args.filename)
            )
        write_output(zf.open(member), member.filename, member.file_size, args)
 
 
def handle_single(archive, opener, args):
    """Handle .gz / .bz2 / .xz — single file compressed, no listing."""
    if args.list:
        print("(single compressed file: {})".format(archive.name))
        return
    with opener(str(archive), "rb") as f:
        write_output(f, archive.stem, None, args)
 
 
# ── Listing ────────────────────────────────────────────────────────────────────
 
def list_tar(members):
    from datetime import datetime
    print("{:>12}  {:<16}  {}".format("SIZE", "MODIFIED", "NAME"))
    print("-" * 70)
    for m in members:
        ts = datetime.fromtimestamp(m.mtime).strftime("%Y-%m-%d %H:%M")
        print("{:>12,}  {:<16}  {}".format(m.size, ts, m.name))
    print("\n{} file(s)".format(len(members)))
 
 
def list_zip(members):
    from datetime import datetime
    print("{:>12}  {:<16}  {}".format("SIZE", "MODIFIED", "NAME"))
    print("-" * 70)
    for m in members:
        ts = datetime(*m.date_time).strftime("%Y-%m-%d %H:%M")
        print("{:>12,}  {:<16}  {}".format(m.file_size, ts, m.filename))
    print("\n{} file(s)".format(len(members)))
 
 
# ── CLI ────────────────────────────────────────────────────────────────────────
 
def parse_args():
    parser = argparse.ArgumentParser(
        prog="extract",
        description="Extract a binary file from any compressed archive.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
formats supported:
  tarball  .tar  .tar.gz  .tgz  .tar.bz2  .tbz2  .tar.xz  .txz
  zip      .zip
  single   .gz  .bz2  .xz  .lzma
 
match priority (--file):
  1. exact internal path   e.g.  usr/lib/libfoo.so
  2. basename              e.g.  libfoo.so
  3. suffix                e.g.  .so
 
exit codes:
  0  success
  1  file not found in archive
  2  archive not found
  3  corrupt / unsupported format
  4  permission denied
 
examples:
  %(prog)s archive.tar.gz  -l
  %(prog)s archive.tar.gz  -f data.bin
  %(prog)s archive.zip     -f data.bin  -o /tmp/out
  %(prog)s archive.tar.xz  -f data.bin  --stdout | sha256sum
  %(prog)s archive.tar.bz2 -f data.bin  --hash sha256
  %(prog)s data.gz         --stdout > data.bin
        """,
    )
 
    parser.add_argument("archive",
                        type=Path,
                        help="path to compressed archive")
    parser.add_argument("-f", "--file",
                        dest="filename",
                        metavar="FILE",
                        help="file to extract (exact path, basename, or suffix)")
    parser.add_argument("-o", "--output-dir",
                        type=Path,
                        default=Path("."),
                        metavar="DIR",
                        help="output directory (default: cwd)")
    parser.add_argument("-l", "--list",
                        action="store_true",
                        help="list all files in the archive")
    parser.add_argument("--stdout",
                        action="store_true",
                        help="stream binary to stdout instead of disk")
    parser.add_argument("--hash",
                        metavar="ALGO",
                        choices=sorted(hashlib.algorithms_guaranteed),
                        help="print checksum without extracting (e.g. sha256, md5)")
    parser.add_argument("--chunk-size",
                        type=int,
                        default=1024 * 1024,
                        metavar="BYTES",
                        help="read chunk size in bytes (default: 1048576)")
 
    args = parser.parse_args()
 
    if not args.list and not args.filename and not args.stdout:
        parser.error("-f/--file is required unless using -l")
 
    return args
 
 
def main():
    args = parse_args()
 
    # Validate archive exists
    if not args.archive.exists():
        print("error: '{}' not found".format(args.archive), file=sys.stderr)
        sys.exit(2)
 
    try:
        fmt = detect_format(args.archive)
    except ValueError as e:
        print("error: {}".format(e), file=sys.stderr)
        sys.exit(3)
 
    try:
        if fmt == "tar":
            handle_tar(args.archive, args)
        elif fmt == "zip":
            handle_zip(args.archive, args)
        elif fmt == "gz":
            handle_single(args.archive, gzip.open, args)
        elif fmt == "bz2":
            handle_single(args.archive, bz2.open, args)
        elif fmt == "xz":
            handle_single(args.archive, lzma.open, args)
 
    except FileNotFoundError as e:
        print("error: {}".format(e), file=sys.stderr)
        sys.exit(1)
    except (tarfile.TarError, zipfile.BadZipFile) as e:
        print("error: corrupt or unsupported archive — {}".format(e), file=sys.stderr)
        sys.exit(3)
    except PermissionError as e:
        print("error: permission denied — {}".format(e), file=sys.stderr)
        sys.exit(4)
 
 
if __name__ == "__main__":
    main()
