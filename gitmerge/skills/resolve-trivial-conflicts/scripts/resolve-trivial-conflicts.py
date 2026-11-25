#!/usr/bin/env python3
# Author: Danish Qamar <danqam@gmail.com>
"""
resolve-trivial-conflicts.py

Detects Git merge conflicts in PHP and JS/TS files where the difference between
current (HEAD) and incoming branches is purely trivial:
  - PHP: Differences in whitespace, tabs, and newlines only.
  - JS/TS: Differences in semicolons (;), spaces, tabs, and newlines only.

Can list identified trivial vs non-trivial conflicts, and automatically merge
trivial conflicts by keeping the current (HEAD) side while leaving non-trivial
conflicts untouched.
"""

import os
import re
import sys
import argparse
import subprocess
from pathlib import Path

# Supported file extensions
PHP_EXTENSIONS = {'.php', '.phtml'}
JS_EXTENSIONS = {'.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx', '.vue'}

# Regex patterns for conflict markers
MARKER_START = re.compile(r'^<{7}(?: .+)?$')
MARKER_DIFF3 = re.compile(r'^\|{7}(?: .+)?$')
MARKER_SEP   = re.compile(r'^={7}$')
MARKER_END   = re.compile(r'^>{7}(?: .+)?$')


def get_unmerged_files():
    """Retrieve list of unmerged files from git diff or porcelain status."""
    try:
        res = subprocess.run(
            ['git', 'diff', '--name-only', '--diff-filter=U'],
            capture_output=True,
            text=True,
            check=True
        )
        files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
        return files
    except subprocess.CalledProcessError:
        return []


def normalize_php(text: str) -> str:
    """Strip all whitespace and newlines for PHP comparison."""
    return re.sub(r'\s+', '', text)


def normalize_js(text: str) -> str:
    """Strip all whitespace, newlines, and semicolons for JS comparison."""
    return re.sub(r'[\s;]+', '', text)


class ConflictHunk:
    def __init__(self, start_line: int, end_line: int, current_lines: list, incoming_lines: list, raw_lines: list):
        self.start_line = start_line
        self.end_line = end_line
        self.current_lines = current_lines
        self.incoming_lines = incoming_lines
        self.raw_lines = raw_lines

        self.current_text = "".join(current_lines)
        self.incoming_text = "".join(incoming_lines)
        self.is_trivial = False
        self.reason = ""

    def evaluate(self, ext: str):
        if ext in PHP_EXTENSIONS:
            norm_curr = normalize_php(self.current_text)
            norm_in   = normalize_php(self.incoming_text)
            if norm_curr == norm_in:
                self.is_trivial = True
                self.reason = "PHP: whitespace/newlines only"
            else:
                self.is_trivial = False
                self.reason = "PHP: code difference"
        elif ext in JS_EXTENSIONS:
            norm_curr = normalize_js(self.current_text)
            norm_in   = normalize_js(self.incoming_text)
            if norm_curr == norm_in:
                self.is_trivial = True
                self.reason = "JS: semicolon/whitespace only"
            else:
                self.is_trivial = False
                self.reason = "JS: code difference"
        else:
            self.is_trivial = False
            self.reason = f"Unsupported extension ({ext})"


def parse_conflicts(filepath: Path):
    """
    Parses a conflicted file into chunks of lines and ConflictHunks.
    Returns (chunks, hunks, ext), where chunks is a list of (type, data)
    type: 'text' (data=lines) or 'hunk' (data=ConflictHunk)
    """
    ext = filepath.suffix.lower()
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return None, [], ext

    chunks = []
    hunks = []
    current_chunk = []

    state = 'NORMAL'  # NORMAL, CURRENT, BASE (diff3), INCOMING
    hunk_start = 0
    curr_lines = []
    base_lines = []
    in_lines = []
    raw_lines = []

    for idx, line in enumerate(lines, 1):
        if state == 'NORMAL':
            if MARKER_START.match(line):
                if current_chunk:
                    chunks.append(('text', current_chunk))
                    current_chunk = []
                state = 'CURRENT'
                hunk_start = idx
                curr_lines = []
                base_lines = []
                in_lines = []
                raw_lines = [line]
            else:
                current_chunk.append(line)

        elif state == 'CURRENT':
            raw_lines.append(line)
            if MARKER_DIFF3.match(line):
                state = 'BASE'
            elif MARKER_SEP.match(line):
                state = 'INCOMING'
            else:
                curr_lines.append(line)

        elif state == 'BASE':
            raw_lines.append(line)
            if MARKER_SEP.match(line):
                state = 'INCOMING'
            else:
                base_lines.append(line)

        elif state == 'INCOMING':
            raw_lines.append(line)
            if MARKER_END.match(line):
                hunk = ConflictHunk(
                    start_line=hunk_start,
                    end_line=idx,
                    current_lines=curr_lines,
                    incoming_lines=in_lines,
                    raw_lines=raw_lines
                )
                hunk.evaluate(ext)
                hunks.append(hunk)
                chunks.append(('hunk', hunk))
                state = 'NORMAL'
            else:
                in_lines.append(line)

    if current_chunk:
        chunks.append(('text', current_chunk))

    return chunks, hunks, ext


def main():
    parser = argparse.ArgumentParser(
        description="Search and resolve trivial merge conflicts (whitespace/newline in PHP, semicolon/space in JS) by keeping current (HEAD)."
    )
    parser.add_argument('-l', '--list', action='store_true', help="List conflicts without modifying files (dry run)")
    parser.add_argument('-a', '--apply', '--merge', dest='apply', action='store_true', help="Merge trivial conflicts by keeping current (HEAD)")
    parser.add_argument('-f', '--file', type=str, help="Target a specific file")
    parser.add_argument('-v', '--verbose', action='store_true', help="Show conflict previews")
    parser.add_argument('--stage', action='store_true', help="Run 'git add' on files where all conflicts were resolved")

    args = parser.parse_args()

    # Default to list mode if apply not explicitly requested
    if not args.apply:
        args.list = True

    if args.file:
        target_files = [args.file]
    else:
        target_files = get_unmerged_files()

    if not target_files:
        print("No unmerged files found.")
        sys.exit(0)

    # Filter to PHP and JS/TS files
    target_files = [
        f for f in target_files
        if Path(f).suffix.lower() in PHP_EXTENSIONS or Path(f).suffix.lower() in JS_EXTENSIONS
    ]

    if not target_files:
        print("No unmerged PHP or JS/TS files found.")
        sys.exit(0)

    total_files = len(target_files)
    total_hunks = 0
    total_trivial = 0
    total_nontrivial = 0
    resolved_files = []

    print(f"{'='*80}")
    action_str = "APPLYING (Keep Current)" if args.apply else "LISTING (Dry Run)"
    print(f"Resolve Trivial Conflicts - Mode: {action_str}")
    print(f"{'='*80}\n")

    for file_str in target_files:
        filepath = Path(file_str)
        if not filepath.exists():
            continue

        chunks, hunks, ext = parse_conflicts(filepath)
        if not hunks:
            continue

        file_trivial = sum(1 for h in hunks if h.is_trivial)
        file_nontrivial = len(hunks) - file_trivial
        total_hunks += len(hunks)
        total_trivial += file_trivial
        total_nontrivial += file_nontrivial

        print(f"File: {file_str} ({len(hunks)} conflicts | {file_trivial} trivial, {file_nontrivial} non-trivial)")

        for i, hunk in enumerate(hunks, 1):
            tag = "[TRIVIAL]" if hunk.is_trivial else "[NON-TRIVIAL]"
            print(f"  Hunk #{i} L{hunk.start_line}-L{hunk.end_line}: {tag} {hunk.reason}")
            if args.verbose:
                curr_sample = hunk.current_text.strip()[:100].replace('\n', '\\n')
                in_sample = hunk.incoming_text.strip()[:100].replace('\n', '\\n')
                print(f"    Current : {curr_sample}")
                print(f"    Incoming: {in_sample}")

        # If applying changes and there are trivial hunks to resolve
        if args.apply and file_trivial > 0:
            output_lines = []
            for chunk_type, data in chunks:
                if chunk_type == 'text':
                    output_lines.extend(data)
                elif chunk_type == 'hunk':
                    hunk = data
                    if hunk.is_trivial:
                        # Keep current (HEAD) side
                        output_lines.extend(hunk.current_lines)
                    else:
                        # Leave non-trivial conflict intact
                        output_lines.extend(hunk.raw_lines)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(output_lines)

            # Check if file has any remaining conflict markers
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            rem = len(re.findall(r'^<{7}', content, re.MULTILINE))

            if rem == 0:
                print(f"  --> RESOLVED: All conflicts resolved in {file_str}.")
                resolved_files.append(file_str)
                if args.stage:
                    subprocess.run(['git', 'add', file_str], check=True)
                    print(f"  --> STAGED: git add {file_str}")
            else:
                print(f"  --> PARTIAL: Resolved {file_trivial} trivial hunks. {rem} non-trivial conflicts remain.")

        print()

    print(f"{'='*80}")
    print(f"Summary: Scanned {total_files} file(s), {total_hunks} conflict hunk(s).")
    print(f"  - Trivial (resolvable by keeping current): {total_trivial}")
    print(f"  - Non-trivial (requires manual review)   : {total_nontrivial}")
    if args.apply:
        print(f"  - Fully resolved files: {len(resolved_files)}")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
