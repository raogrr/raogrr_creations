#!/usr/bin/env python3
"""
Binary File Comparator - CLI Tool
Support Contact: Gururaj Rao <grao1@visteon.com>

Usage: python binary_compare.py [OPTIONS] <file1> <file2>

# Basic compare
python binary_compare.py /home/user/file1.bin /tmp/backup/file2.bin

# Verbose mode (shows MD5 hashes)
python binary_compare.py image1.png image2.png --verbose

# Limit to 20 differences shown
python binary_compare.py data1.dat data2.dat --max-diffs 20

# Custom chunk size (faster for large files)
python binary_compare.py archive1.zip archive2.zip --chunk-size 8192

# Quiet mode (just prints IDENTICAL or DIFFERENT — great for scripts)
python binary_compare.py build1.exe build2.exe --quiet

# Short flags
python binary_compare.py f1.bin f2.bin -v -m 50 -c 8192

#Sample Output
=================================================================
  BINARY FILE COMPARATOR
=================================================================
  File 1 : /home/user/file1.bin
           1.00 KB
  File 2 : /tmp/backup/file2.bin
           1.00 KB
=================================================================

  ❌ Files are DIFFERENT
     Differences : 3 byte(s) in first 1.00 KB
     Scan time   : 0.001s

  Offset (Hex)   Offset (Dec)   File1 Hex   File1 Chr   File2 Hex   File2 Chr
  ------------- -------------- ----------  ----------  ----------  ---------
  0x00000004     4              0x48        H           0x4B        K
  0x00000010     16             0x2E        .           0x00        .
  0x000001A3     419            0x3C        <           0x61        a
"""

import os
import sys
import argparse
import hashlib
import time


def format_bytes(size):
    """Human-readable file size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def compute_hash(filepath, algorithm='md5'):
    """Compute file hash for quick equality check."""
    h = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def binary_compare(file1, file2, chunk_size=4096, max_diffs=100, show_context=False, verbose=False):
    """
    Core binary comparison logic.

    Args:
        file1       : Path to first file
        file2       : Path to second file
        chunk_size  : Bytes to read per iteration
        max_diffs   : Max differences to display before stopping
        show_context: Show surrounding bytes around each diff
        verbose     : Print extra info

    Returns:
        (bool: identical, int: diff_count)
    """
    size1 = os.path.getsize(file1)
    size2 = os.path.getsize(file2)
    min_size = min(size1, size2)

    print(f"\n{'='*65}")
    print(f"  BINARY FILE COMPARATOR")
    print(f"{'='*65}")
    print(f"  File 1 : {file1}")
    print(f"           {format_bytes(size1)}")
    print(f"  File 2 : {file2}")
    print(f"           {format_bytes(size2)}")
    print(f"{'='*65}\n")

    # Quick hash check
    if verbose:
        print("  ⏳ Computing MD5 hashes...")
    hash1 = compute_hash(file1)
    hash2 = compute_hash(file2)

    if verbose:
        print(f"  MD5 File 1 : {hash1}")
        print(f"  MD5 File 2 : {hash2}\n")

    if hash1 == hash2:
        print("  ✅ Files are IDENTICAL (MD5 match confirmed)\n")
        return True, 0

    # Files differ — find where
    differences = []
    offset = 0
    start_time = time.time()

    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        while True:
            chunk1 = f1.read(chunk_size)
            chunk2 = f2.read(chunk_size)

            if not chunk1 and not chunk2:
                break

            # Pad the shorter chunk
            max_len = max(len(chunk1), len(chunk2))
            b1 = chunk1.ljust(max_len, b'\x00')
            b2 = chunk2.ljust(max_len, b'\x00')

            for i in range(max_len):
                if b1[i] != b2[i]:
                    differences.append({
                        'offset'    : offset + i,
                        'byte_f1'   : b1[i],
                        'byte_f2'   : b2[i],
                        'char_f1'   : chr(b1[i]) if 32 <= b1[i] < 127 else '.',
                        'char_f2'   : chr(b2[i]) if 32 <= b2[i] < 127 else '.',
                    })

            offset += max_len

            if len(differences) > max_diffs:
                print(f"  ⚠️  Exceeded {max_diffs} differences — stopping early.\n")
                break

    elapsed = time.time() - start_time

    # Size mismatch summary
    if size1 != size2:
        print(f"  ⚠️  Size mismatch  : {format_bytes(size1)} vs {format_bytes(size2)}")
        print(f"     Extra bytes    : {abs(size1 - size2)} bytes in {'File 1' if size1 > size2 else 'File 2'}\n")

    diff_count = len(differences)
    print(f"  ❌ Files are DIFFERENT")
    print(f"     Differences : {diff_count} byte(s) in first {format_bytes(min_size)}")
    print(f"     Scan time   : {elapsed:.3f}s\n")

    # Differences table
    print(f"  {'Offset (Hex)':<14} {'Offset (Dec)':<14} {'File1 Hex':<11} {'File1 Chr':<11} {'File2 Hex':<11} {'File2 Chr'}")
    print(f"  {'-'*13:<14} {'-'*13:<14} {'-'*9:<11} {'-'*9:<11} {'-'*9:<11} {'-'*9}")

    for d in differences[:max_diffs]:
        print(
            f"  0x{d['offset']:08X}    "
            f"{d['offset']:<14} "
            f"0x{d['byte_f1']:02X}       "
            f"{d['char_f1']:<11} "
            f"0x{d['byte_f2']:02X}       "
            f"{d['char_f2']}"
        )

    if diff_count > max_diffs:
        print(f"\n  ... and {diff_count - max_diffs} more differences not shown.")

    print()
    return False, diff_count


def validate_file(path, label):
    """Validate file exists and is readable."""
    if not os.path.exists(path):
        print(f"  ❌ Error: {label} not found: '{path}'")
        sys.exit(1)
    if not os.path.isfile(path):
        print(f"  ❌ Error: {label} is not a file: '{path}'")
        sys.exit(1)
    if not os.access(path, os.R_OK):
        print(f"  ❌ Error: {label} is not readable: '{path}'")
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(
        prog='binary_compare',
        description='Compare two binary files byte-by-byte from the command line.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  python binary_compare.py file1.bin file2.bin
  python binary_compare.py /path/to/a.exe /other/path/b.exe
  python binary_compare.py image1.png image2.png --verbose
  python binary_compare.py data1.bin data2.bin --max-diffs 50
  python binary_compare.py archive1.zip archive2.zip --chunk-size 8192
        """
    )

    parser.add_argument('file1',
        help='Path to the first file')

    parser.add_argument('file2',
        help='Path to the second file')

    parser.add_argument('--max-diffs', '-m',
        type=int, default=100, metavar='N',
        help='Max number of differences to display (default: 100)')

    parser.add_argument('--chunk-size', '-c',
        type=int, default=4096, metavar='BYTES',
        help='Read chunk size in bytes (default: 4096)')

    parser.add_argument('--verbose', '-v',
        action='store_true',
        help='Show MD5 hashes and extra info')

    parser.add_argument('--quiet', '-q',
        action='store_true',
        help='Print only the final result (identical / different)')

    return parser.parse_args()


def main():
    args = parse_args()

    validate_file(args.file1, "File 1")
    validate_file(args.file2, "File 2")

    if args.quiet:
        # Silent mode — just hash compare
        h1 = compute_hash(args.file1)
        h2 = compute_hash(args.file2)
        if h1 == h2:
            print("IDENTICAL")
            sys.exit(0)
        else:
            print("DIFFERENT")
            sys.exit(1)

    identical, diff_count = binary_compare(
        file1       = args.file1,
        file2       = args.file2,
        chunk_size  = args.chunk_size,
        max_diffs   = args.max_diffs,
        verbose     = args.verbose,
    )

    sys.exit(0 if identical else 1)


if __name__ == "__main__":
    main()
