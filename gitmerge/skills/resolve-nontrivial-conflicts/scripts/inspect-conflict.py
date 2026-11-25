#!/usr/bin/env python3
# Author: Danish Qamar <danqam@gmail.com>
"""
inspect-conflict.py

Inspects non-trivial Git merge conflicts in a specific file.
Extracts conflict hunks, analyzes line numbers, and surfaces Git context
(HEAD commit, MERGE_HEAD / incoming commit, common ancestor diffs)
to assist in deciding the optimal resolution strategy.
"""

import os
import re
import sys
import json
import argparse
import subprocess
from pathlib import Path

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


def parse_hunks(filepath: Path):
    if not filepath.exists():
        print(f"Error: File '{filepath}' does not exist.", file=sys.stderr)
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    hunks = []
    state = 'NORMAL'
    hunk_start = 0
    curr_lines = []
    base_lines = []
    in_lines = []
    head_label = ""
    incoming_label = ""

    for idx, line in enumerate(lines, 1):
        if state == 'NORMAL':
            m = MARKER_START.match(line)
            if m:
                state = 'CURRENT'
                hunk_start = idx
                head_label = m.group(1) or "HEAD"
                curr_lines = []
                base_lines = []
                in_lines = []
        elif state == 'CURRENT':
            if MARKER_DIFF3.match(line):
                state = 'BASE'
            elif MARKER_SEP.match(line):
                state = 'INCOMING'
            else:
                curr_lines.append(line)
        elif state == 'BASE':
            if MARKER_SEP.match(line):
                state = 'INCOMING'
            else:
                base_lines.append(line)
        elif state == 'INCOMING':
            m = MARKER_END.match(line)
            if m:
                incoming_label = m.group(1) or "INCOMING"
                hunks.append({
                    'index': len(hunks) + 1,
                    'start_line': hunk_start,
                    'end_line': idx,
                    'head_label': head_label,
                    'incoming_label': incoming_label,
                    'current_lines': curr_lines,
                    'incoming_lines': in_lines,
                    'base_lines': base_lines,
                    'current_text': "".join(curr_lines),
                    'incoming_text': "".join(in_lines)
                })
                state = 'NORMAL'
            else:
                in_lines.append(line)

    return hunks


def main():
    parser = argparse.ArgumentParser(
        description="Inspect non-trivial merge conflicts in a file with Git branch context."
    )
    parser.add_argument('file', help="Path to conflicted file")
    parser.add_argument('--hunk', type=int, help="Inspect only a specific hunk number (1-based)")
    parser.add_argument('--json', action='store_true', help="Output in JSON format")

    args = parser.parse_args()
    filepath = Path(args.file)

    hunks = parse_hunks(filepath)
    git_info = get_git_info()

    if args.hunk:
        target_hunks = [h for h in hunks if h['index'] == args.hunk]
        if not target_hunks:
            print(f"Error: Hunk #{args.hunk} not found in {filepath} (total: {len(hunks)})", file=sys.stderr)
            sys.exit(1)
    else:
        target_hunks = hunks

    if args.json:
        output = {
            'file': str(filepath),
            'git_info': git_info,
            'total_hunks': len(hunks),
            'hunks': target_hunks
        }
        print(json.dumps(output, indent=2))
        return

    abs_path = filepath.resolve()
    print("=" * 80)
    print(f"Conflict Inspector: {filepath} ({len(hunks)} conflicts total)")
    print(f"Current Branch  (HEAD)   : {git_info['head_msg']}")
    print(f"Incoming Branch (MERGE)  : {git_info['incoming_msg']}")
    print("=" * 80)

    for h in target_hunks:
        link = f"{abs_path}#L{h['start_line']}-L{h['end_line']}"
        print(f"\n>>> Hunk #{h['index']} | Lines: L{h['start_line']}-L{h['end_line']}")
        print(f"    Link: {link}")
        print(f"    --- Current Change ({h['head_label']}) [{len(h['current_lines'])} lines]:")
        for line in h['current_lines'][:15]:
            print(f"      + {line.rstrip()}")
        if len(h['current_lines']) > 15:
            print(f"      ... [{len(h['current_lines']) - 15} more lines]")

        print(f"    --- Incoming Change ({h['incoming_label']}) [{len(h['incoming_lines'])} lines]:")
        for line in h['incoming_lines'][:15]:
            print(f"      - {line.rstrip()}")
        if len(h['incoming_lines']) > 15:
            print(f"      ... [{len(h['incoming_lines']) - 15} more lines]")


if __name__ == '__main__':
    main()
