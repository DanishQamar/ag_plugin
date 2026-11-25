#!/usr/bin/env bash
# open-unmerged.sh
# Detects unmerged (conflicted) files in Git and opens them in the active IDE.

set -euo pipefail

# ANSI Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

show_help() {
    cat <<EOF
Usage: $(basename "$0") [options]

Detects unmerged (conflicted) files in the current Git repository and opens
them directly in the active IDE positioned at the first conflict marker.

Options:
  -d, --dry-run, --list    List unmerged files and first conflict line numbers without opening the editor
  -e, --editor <command>   Specify editor executable (default: auto-detect agy-ide, antigravity-ide, or code)
  -h, --help               Show this help message
EOF
}

# 1. Ensure we are in a Git repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo -e "${RED}[ERROR]${NC} Not inside a Git repository." >&2
    exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
DRY_RUN=false
CUSTOM_EDITOR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--dry-run|--list)
            DRY_RUN=true
            shift
            ;;
        -e|--editor)
            if [[ $# -lt 2 ]]; then
                echo -e "${RED}[ERROR]${NC} --editor requires an argument." >&2
                exit 1
            fi
            CUSTOM_EDITOR="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}[ERROR]${NC} Unknown option: $1" >&2
            show_help
            exit 1
            ;;
    esac
done

# 2. Determine editor executable
EDITOR_BIN=""
if [[ -n "$CUSTOM_EDITOR" ]]; then
    if command -v "$CUSTOM_EDITOR" >/dev/null 2>&1; then
        EDITOR_BIN="$(command -v "$CUSTOM_EDITOR")"
    else
        echo -e "${RED}[ERROR]${NC} Specified editor '$CUSTOM_EDITOR' not found in PATH." >&2
        exit 1
    fi
else
    for candidate in agy-ide antigravity-ide code; do
        if command -v "$candidate" >/dev/null 2>&1; then
            EDITOR_BIN="$(command -v "$candidate")"
            break
        fi
    done
fi

# 3. Collect unmerged files using porcelain status
declare -a UNMERGED_FILES=()
declare -a STATUS_CODES=()

while IFS= read -r -d '' entry; do
    [[ -z "$entry" ]] && continue
    status="${entry:0:2}"
    filepath="${entry:3}"
    
    case "$status" in
        UU|AA|DD|AU|UA|UD|DU)
            STATUS_CODES+=("$status")
            UNMERGED_FILES+=("$filepath")
            ;;
    esac
done < <(git status --porcelain=v1 -z)

TOTAL_COUNT=${#UNMERGED_FILES[@]}

if [[ $TOTAL_COUNT -eq 0 ]]; then
    echo -e "${GREEN}[OK]${NC} No unmerged files found. Working tree has no active Git conflicts."
    exit 0
fi

echo -e "${BOLD}${CYAN}Found ${TOTAL_COUNT} unmerged path(s):${NC}\n"

declare -a OPEN_ARGS=()
declare -a MISSING_FILES=()
declare -a EXISTING_FILES=()

for i in "${!UNMERGED_FILES[@]}"; do
    rel_path="${UNMERGED_FILES[$i]}"
    status="${STATUS_CODES[$i]}"
    full_path="${REPO_ROOT}/${rel_path}"

    status_desc=""
    case "$status" in
        UU) status_desc="both modified" ;;
        AA) status_desc="both added" ;;
        DD) status_desc="both deleted" ;;
        AU) status_desc="added by us" ;;
        UA) status_desc="added by them" ;;
        UD) status_desc="deleted by them" ;;
        DU) status_desc="deleted by us" ;;
        *)  status_desc="conflict ($status)" ;;
    esac

    if [[ ! -e "$full_path" ]]; then
        MISSING_FILES+=("$rel_path")
        echo -e "  ${RED}✖${NC} ${BOLD}${rel_path}${NC} [${YELLOW}${status_desc}${NC}] (missing from disk - resolve with git add/rm)"
        continue
    fi

    # Find first conflict marker <<<<<<<
    first_conflict_line=$(grep -n -m 1 '^[<]\{7\}' "$full_path" 2>/dev/null | cut -d: -f1 || true)
    conflict_count=$(grep -c '^[<]\{7\}' "$full_path" 2>/dev/null || true)

    if [[ -n "$first_conflict_line" ]]; then
        line_info="line ${first_conflict_line} (${conflict_count} conflict marker(s))"
        target_line="$first_conflict_line"
    else
        line_info="line 1 (no <<<<<<< marker detected)"
        target_line="1"
    fi

    EXISTING_FILES+=("$rel_path")
    echo -e "  ${GREEN}✔${NC} ${BOLD}${rel_path}${NC} [${YELLOW}${status_desc}${NC}] -> ${line_info}"
    OPEN_ARGS+=("-r" "-g" "${full_path}:${target_line}")
done

echo ""

if [[ "$DRY_RUN" == true ]]; then
    echo -e "${BLUE}[DRY RUN]${NC} Editor will not be launched."
    if [[ -n "$EDITOR_BIN" ]]; then
        echo -e "Detected editor: ${CYAN}${EDITOR_BIN}${NC}"
    fi
    exit 0
fi

if [[ ${#EXISTING_FILES[@]} -eq 0 ]]; then
    echo -e "${YELLOW}[NOTE]${NC} All unmerged paths are deleted or missing from disk. None to open in editor."
    exit 0
fi

if [[ -z "$EDITOR_BIN" ]]; then
    echo -e "${RED}[WARNING]${NC} No compatible IDE editor CLI found (checked: agy-ide, antigravity-ide, code)." >&2
    echo -e "Files to resolve:"
    for f in "${EXISTING_FILES[@]}"; do
        echo "  - $f"
    done
    exit 1
fi

echo -e "Opening ${#EXISTING_FILES[@]} file(s) in ${CYAN}${EDITOR_BIN}${NC}..."
"$EDITOR_BIN" "${OPEN_ARGS[@]}"
echo -e "${GREEN}[SUCCESS]${NC} Dispatched ${#EXISTING_FILES[@]} file(s) to ${EDITOR_BIN}."
