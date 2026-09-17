#!/bin/sh
# MASK installer for macOS and Linux.
#
#   curl -fsSL https://raw.githubusercontent.com/MikeMarcin/ManageAgentSkills/main/install.sh | sh
#
# It clones ManageAgentSkills (or fast-forwards an existing clone), then runs the program's own
# `self install` to write the `mask` launcher. Nothing runs as root, nothing is added to your shell
# profile, and neither Python nor Git is installed for you. Running it again updates in place.
#
#   MASK_INSTALL_DIR  where the program clone lives   (default: ${XDG_DATA_HOME:-$HOME/.local/share}/mask)
#   MASK_BIN_DIR      where the launcher is written   (default: $HOME/.local/bin)
#   MASK_REPO         Git URL to clone                (default: https://github.com/MikeMarcin/ManageAgentSkills.git)
#   MASK_PYTHON       Python 3.11+ interpreter to use (default: first of python3, python)
#
# The whole script is one function called on the last line, so a download that is cut short runs nothing.
set -eu

main() {
    repo=${MASK_REPO:-https://github.com/MikeMarcin/ManageAgentSkills.git}
    dir=${MASK_INSTALL_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/mask}
    bin=${MASK_BIN_DIR:-$HOME/.local/bin}

    command -v git >/dev/null 2>&1 || fail "Git is required. Install Git, then run this again."
    python=${MASK_PYTHON:-}
    if [ -z "$python" ]; then
        for candidate in python3 python; do
            if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
                python=$candidate
                break
            fi
        done
    fi
    [ -n "$python" ] || fail "Python 3.11 or newer is required (looked for python3 and python). Set MASK_PYTHON to choose one."
    "$python" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null || fail "$python is older than Python 3.11."

    if [ -d "$dir/.git" ]; then
        say "Updating MASK in $dir"
        # Only a clean fast-forward: local work in the clone is never discarded.
        git -C "$dir" pull --quiet --ff-only || fail "Could not fast-forward $dir. Resolve it with Git, or remove the directory and run this again."
    elif [ -e "$dir" ]; then
        fail "$dir exists and is not a MASK clone. Move it away, or set MASK_INSTALL_DIR."
    else
        say "Installing MASK into $dir"
        mkdir -p "$(dirname "$dir")"
        git clone --quiet "$repo" "$dir" || fail "Could not clone $repo. If it needs credentials, sign in to Git first (for GitHub: gh auth login)."
    fi

    mkdir -p "$bin"
    "$python" "$dir/mask.py" self install --bin-dir "$bin" >/dev/null || fail "The launcher could not be written to $bin."
    say "Installed $("$bin/mask" --version) as $bin/mask"

    case ":$PATH:" in
        *":$bin:"*) mask=mask ;;
        *)
            mask=$bin/mask
            say ""
            say "$bin is not on your PATH. Add it in your shell profile:"
            say "  export PATH=\"$bin:\$PATH\""
            ;;
    esac
    say ""
    say "Next:"
    say "  $mask tap add agentskills https://github.com/MikeMarcin/AgentSkills.git   # approve a tap"
    say "  cd your-project && $mask install implement-rfc                            # add a skill"
    say "  $mask update                                                              # later: update MASK and fetch taps"
}

say() { printf '%s\n' "$*"; }
fail() { printf 'mask install: %s\n' "$*" >&2; exit 1; }

main "$@"
