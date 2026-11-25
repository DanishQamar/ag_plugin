#!/usr/bin/env python3
# Author: Danish Qamar <danqam@gmail.com>
"""
resolve-conflicts.py

Unified Git merge conflict resolution tool combining:
1. Automated detection & resolution of trivial formatting conflicts:
   - PHP: Differences in whitespace, tabs, and newlines only.
   - JS/TS: Differences in semicolons (;), spaces, tabs, and newlines only.
2. Structured inspection and decision support for non-trivial conflicts
   using Git branch context (HEAD vs MERGE_HEAD commit logs and ancestor diffs).
"""

import os
import re
import sys
import json
import argparse
import subprocess
from pathlib import Path

PHP_EXTENSIONS = {'.php', '.phtml'}
JS_EXTENSIONS  = {'.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx', '.vue'}

MARKER_START = re.compile(r'^<{7}(?: (.+))?$')
MARKER_DIFF3 = re.compile(r'^\|{7}(?: (.+))?$')
MARKER_SEP   = re.compile(r'^={7}$')
MARKER_END   = re.compile(r'^>{7}(?: (.+))?$')


def run_git(cmd):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return None


def get_git_info():
    head_rev = run_git(['git', 'rev-parse', '--short', 'HEAD'])
    head_msg = run_git(['git', 'log', '-1', '--oneline', 'HEAD'])
    merge_head = run_git(['git', 'rev-parse', '-q', '--verify', 'MERGE_HEAD'])
    merge_msg = run_git(['git', 'log', '-1', '--oneline', 'MERGE_HEAD']) if merge_head else "No active MERGE_HEAD"

    return {
        'head_rev': head_rev,
        'head_msg': head_msg,
        'incoming_rev': merge_head[:7] if merge_head else None,
        'incoming_msg': merge_msg
    }


def get_unmerged_files():
    try:
        res = subprocess.run(
            ['git', 'diff', '--name-only', '--diff-filter=U'],
            capture_output=True,
            text=True,
            check=True
        )
        return [f.strip() for f in res.stdout.splitlines() if f.strip()]
    except Exception:
        return []


def normalize_php(text: str) -> str:
    return re.sub(r'\s+', '', text)


def normalize_js(text: str) -> str:
    return re.sub(r'[\s;]+', '', text)


class ConflictHunk:
    def __init__(self, index: int, start_line: int, end_line: int, head_label: str, incoming_label: str,
                 current_lines: list, incoming_lines: list, base_lines: list, raw_lines: list):
        self.index = index
        self.start_line = start_line
        self.end_line = end_line
        self.head_label = head_label
        self.incoming_label = incoming_label
        self.current_lines = current_lines
        self.incoming_lines = incoming_lines
        self.base_lines = base_lines
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
            self.reason = f"File type {ext}: manual review required"


def parse_conflicts(filepath: Path):
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

    state = 'NORMAL'
    hunk_start = 0
    curr_lines = []
    base_lines = []
    in_lines = []
    raw_lines = []
    head_label = ""
    incoming_label = ""

    for idx, line in enumerate(lines, 1):
        if state == 'NORMAL':
            m = MARKER_START.match(line)
            if m:
                if current_chunk:
                    chunks.append(('text', current_chunk))
                    current_chunk = []
                state = 'CURRENT'
                hunk_start = idx
                head_label = m.group(1) or "HEAD"
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
            m = MARKER_END.match(line)
            if m:
                incoming_label = m.group(1) or "INCOMING"
                hunk = ConflictHunk(
                    index=len(hunks) + 1,
                    start_line=hunk_start,
                    end_line=idx,
                    head_label=head_label,
                    incoming_label=incoming_label,
                    current_lines=curr_lines,
                    incoming_lines=in_lines,
                    base_lines=base_lines,
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
        description="Unified conflict resolution tool: auto-merges trivial formatting conflicts (keep current) and inspects non-trivial conflicts with Git context."
    )
    parser.add_argument('-l', '--list', action='store_true', help="List conflicts with line numbers and classifications (dry run)")
    parser.add_argument('-a', '--apply-trivial', action='store_true', help="Automatically merge trivial conflicts by keeping current (HEAD)")
    parser.add_argument('-i', '--inspect', action='store_true', help="Inspect non-trivial conflicts with Git branch context")
    parser.add_argument('-f', '--file', type=str, help="Target a specific file")
    parser.add_argument('-v', '--verbose', action='store_true', help="Show conflict previews")
    parser.add_argument('--stage', action='store_true', help="Run 'git add' on files where all conflicts are resolved")
    parser.add_argument('--json', action='store_true', help="Output in JSON format")

    args = parser.parse_args()

    if not args.apply_trivial and not args.inspect:
        args.list = True

    if args.file:
        target_files = [args.file]
    else:
        target_files = get_unmerged_files()

    if not target_files:
        if args.json:
            print(json.dumps({'unmerged': []}))
        else:
            print("No unmerged files found.")
        sys.exit(0)

    git_info = get_git_info()
    total_files = len(target_files)
    total_hunks = 0
    total_trivial = 0
    total_nontrivial = 0
    resolved_files = []

    if not args.json:
        print("=" * 80)
        mode_str = "APPLY TRIVIAL" if args.apply_trivial else ("INSPECT NON-TRIVIAL" if args.inspect else "LISTING (Dry Run)")
        print(f"Unified Conflict Resolver - Mode: {mode_str}")
        print(f"Current Branch  (HEAD)   : {git_info['head_msg']}")
        print(f"Incoming Branch (MERGE)  : {git_info['incoming_msg']}")
        print("=" * 80 + "\n")

    json_output = {'git_info': git_info, 'files': []}

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

        abs_path = filepath.resolve()

        if args.json:
            json_output['files'].append({
                'file': str(filepath),
                'total_hunks': len(hunks),
                'trivial': file_trivial,
                'nontrivial': file_nontrivial,
                'hunks': [{
                    'index': h.index,
                    'start_line': h.start_line,
                    'end_line': h.end_line,
                    'is_trivial': h.is_trivial,
                    'reason': h.reason,
                    'head_label': h.head_label,
                    'incoming_label': h.incoming_label,
                    'current_text': h.current_text,
                    'incoming_text': h.incoming_text
                } for h in hunks]
            })
            continue

        print(f"File: {file_str} ({len(hunks)} conflicts | {file_trivial} trivial, {file_nontrivial} non-trivial)")

        for hunk in hunks:
            tag = "[TRIVIAL]" if hunk.is_trivial else "[NON-TRIVIAL]"
            link = f"file://{abs_path}#L{hunk.start_line}-L{hunk.end_line}"
            print(f"  Hunk #{hunk.index} L{hunk.start_line}-L{hunk.end_line}: {tag} {hunk.reason}")
            print(f"    Link: {link}")

            if args.verbose or (args.inspect and not hunk.is_trivial):
                print(f"    --- HEAD ({hunk.head_label}):")
                for line in hunk.current_lines[:10]:
                    print(f"      + {line.rstrip()}")
                if len(hunk.current_lines) > 10:
                    print(f"      ... [{len(hunk.current_lines) - 10} more lines]")
                print(f"    --- INCOMING ({hunk.incoming_label}):")
                for line in hunk.incoming_lines[:10]:
                    print(f"      - {line.rstrip()}")
                if len(hunk.incoming_lines) > 10:
                    print(f"      ... [{len(hunk.incoming_lines) - 10} more lines]")

        # Apply trivial resolution if requested
        if args.apply_trivial and file_trivial > 0:
            output_lines = []
            for chunk_type, data in chunks:
                if chunk_type == 'text':
                    output_lines.extend(data)
                elif chunk_type == 'hunk':
                    hunk = data
                    if hunk.is_trivial:
                        output_lines.extend(hunk.current_lines)
                    else:
                        output_lines.extend(hunk.raw_lines)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(output_lines)

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

    if args.json:
        print(json.dumps(json_output, indent=2))
        return

    print("=" * 80)
    print(f"Summary: Scanned {total_files} file(s), {total_hunks} conflict hunk(s).")
    print(f"  - Trivial (resolvable by keeping current): {total_trivial}")
    print(f"  - Non-trivial (requires manual review)   : {total_nontrivial}")
    if args.apply_trivial:
        print(f"  - Fully resolved files: {len(resolved_files)}")
    print("=" * 80)


if __name__ == '__main__':
    main()
