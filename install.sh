#!/usr/bin/env bash
# fp-control installer — shows what is installed, what changed, and installs on request.
#
#   bash install.sh status   [--no-fetch] [--short]
#   bash install.sh install  [--platform claude,cursor,windsurf] [--dest DIR] [--force] [--no-hook] [--no-fetch]
#   bash install.sh uninstall [--force]
#
# status     Read-only. Compares the installed copies with this checkout, and this checkout
#            with origin/main (runs `git fetch` unless --no-fetch).
# install    Copies the two skills to each agent platform and the report assets to
#            ~/.fp-control/, records what was installed, and adds git post-merge and
#            post-rewrite hooks that print the status after every `git pull`, merging or
#            rebasing (skip with --no-hook). Installed files edited since the last install
#            are kept unless --force.
# uninstall  Removes the files recorded by the last install, and the hook. Files edited
#            since the install are kept unless --force.
#
# Platforms (default: every one whose config directory exists):
#   claude    ~/.claude/commands/<skill>.md
#   cursor    ~/.cursor/rules/<skill>.mdc
#   windsurf  ~/.codeium/windsurf/memories/<skill>.md
#   --dest    any other directory, as <skill>.md
set -u

repo=$(cd "$(dirname "$0")" && pwd)
assets_dir=$HOME/.fp-control   # the skills look here; keep in sync with fp-control-html.md
record="$assets_dir/INSTALLED"
skills="fp-control fp-control-html"
asset_files="fp-report.html fpa.sh fpa.py LICENSE-js-yaml"
hook_names="post-merge post-rewrite"   # post-rewrite covers `git pull --rebase` with local commits

if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  B=$'\033[1m' G=$'\033[32m' Y=$'\033[33m' R=$'\033[31m' D=$'\033[2m' N=$'\033[0m'
else
  B='' G='' Y='' R='' D='' N=''
fi

die() { printf 'install.sh: %s\n' "$*" >&2; exit 2; }
usage() { awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"; exit "${1:-0}"; }
sum() { [ -f "$1" ] && cksum < "$1" | awk '{print $1 "-" $2}'; }
pretty() { case $1 in "$HOME"/*) printf '~%s' "${1#"$HOME"}";; *) printf '%s' "$1";; esac; }

# ── What goes where ───────────────────────────────────────────────────────
platform_dir() {
  case $1 in
    claude) echo "$HOME/.claude/commands";;
    cursor) echo "$HOME/.cursor/rules";;
    windsurf) echo "$HOME/.codeium/windsurf/memories";;
    *) return 1;;
  esac
}
platform_ext() { [ "$1" = cursor ] && echo mdc || echo md; }
detect_platforms() {
  found=''
  [ -d "$HOME/.claude" ] && found="$found claude"
  [ -d "$HOME/.cursor" ] && found="$found cursor"
  [ -d "$HOME/.codeium/windsurf" ] && found="$found windsurf"
  echo $found
}

# Print "source<TAB>target" lines for every file to install.
plan() {
  for p in $platforms; do
    dir=$(platform_dir "$p") || die "unknown platform '$p' (use claude, cursor, windsurf, or --dest)"
    for s in $skills; do printf '%s\t%s\n' "$repo/$s.md" "$dir/$s.$(platform_ext "$p")"; done
  done
  for d in $dests; do
    for s in $skills; do printf '%s\t%s\n' "$repo/$s.md" "$d/$s.md"; done
  done
  for a in $asset_files; do printf '%s\t%s\n' "$repo/assets/$a" "$assets_dir/$a"; done
}

# Targets from the last install record, or the default plan when nothing is recorded.
recorded_value() { [ -f "$record" ] && sed -n "s/^$1=//p" "$record" | head -n 1; }
recorded_sum() { [ -f "$record" ] && awk -v f="$1" '$1 == "file" && $3 == f { print $2 }' "$record"; }

# State of one target: missing | current | outdated | edited
state_of() {
  src=$1 dst=$2
  [ -f "$dst" ] || { echo missing; return; }
  [ "$(sum "$src")" = "$(sum "$dst")" ] && { echo current; return; }
  was=$(recorded_sum "$dst")
  if [ -n "$was" ] && [ "$was" != "$(sum "$dst")" ]; then echo edited; else echo outdated; fi
}

# ── Git awareness ─────────────────────────────────────────────────────────
# Sets: git_ok head branch sync ('' when unknown) behind ahead dirty fetch_note
git_info() {
  git_ok='' head='' branch='' sync='' behind=0 ahead=0 dirty='' fetch_note=''
  command -v git >/dev/null 2>&1 && git -C "$repo" rev-parse --git-dir >/dev/null 2>&1 || return 0
  git_ok=1
  head=$(git -C "$repo" rev-parse --short HEAD 2>/dev/null)
  branch=$(git -C "$repo" rev-parse --abbrev-ref HEAD 2>/dev/null)
  if [ "$do_fetch" = 1 ]; then
    GIT_TERMINAL_PROMPT=0 git -C "$repo" fetch --quiet origin main >/dev/null 2>&1 \
      || fetch_note='could not reach origin — using the last fetched state'
  fi
  if git -C "$repo" rev-parse --verify --quiet origin/main >/dev/null; then
    counts=$(git -C "$repo" rev-list --left-right --count HEAD...origin/main 2>/dev/null)
    ahead=${counts%%[[:space:]]*}; behind=${counts##*[[:space:]]}
    if [ "$ahead" = 0 ] && [ "$behind" = 0 ]; then sync=in-sync
    elif [ "$ahead" = 0 ]; then sync=behind
    elif [ "$behind" = 0 ]; then sync=ahead
    else sync=diverged; fi
  fi
  dirty=$(git -C "$repo" status --porcelain -- fp-control.md fp-control-html.md assets 2>/dev/null)
}

# ── status ────────────────────────────────────────────────────────────────
cmd_status() {
  git_info
  installed_commit=$(recorded_value commit)
  n_missing=0 n_outdated=0 n_edited=0 n_current=0 lines=''
  while IFS="$(printf '\t')" read -r src dst; do
    st=$(state_of "$src" "$dst")
    case $st in
      current) n_current=$((n_current + 1)); label="${G}up to date${N}";;
      missing) n_missing=$((n_missing + 1)); label="${Y}not installed${N}";;
      outdated) n_outdated=$((n_outdated + 1)); label="${Y}update available${N}";;
      edited) n_edited=$((n_edited + 1)); label="${R}edited since install (kept unless --force)${N}";;
    esac
    lines="$lines$(printf '    %-52s %s' "$(pretty "$dst")" "$label")
"
  done <<EOF
$(plan)
EOF
  pending=$((n_missing + n_outdated + n_edited))

  # Repository line — the sync state with origin/main is the headline.
  if [ -z "$git_ok" ]; then
    repo_line="${D}not a git checkout — cannot compare with origin/main${N}"
  else
    case $sync in
      in-sync) repo_line="${G}${B}✔ in sync with origin/main${N} (${head})";;
      behind) repo_line="${Y}${B}$behind commit(s) behind origin/main${N} (${head}) — run: git pull";;
      ahead) repo_line="${Y}$ahead commit(s) ahead of origin/main${N} (${head}, not pushed)";;
      diverged) repo_line="${R}diverged from origin/main${N} ($ahead ahead, $behind behind)";;
      *) repo_line="${D}no origin/main to compare with${N} (${head})";;
    esac
    [ "$branch" = main ] || repo_line="$repo_line ${Y}[on branch $branch]${N}"
  fi

  if [ "$short" = 1 ]; then
    if [ "$pending" = 0 ]; then
      printf 'fp-control: %s — installed copies up to date\n' "$repo_line"
    else
      printf 'fp-control: %s — %s%d installed file(s) need an update%s: bash %s install\n' \
        "$repo_line" "$Y" "$pending" "$N" "$(pretty "$repo/install.sh")"
    fi
  else
    printf '%sfp-control%s\n' "$B" "$N"
    printf '  repository   %s\n' "$(pretty "$repo")"
    printf '               %s\n' "$repo_line"
    [ -z "$fetch_note" ] || printf '               %s%s%s\n' "$D" "$fetch_note" "$N"
    [ -z "$dirty" ] || printf '               %suncommitted changes in skill files — installing copies work in progress%s\n' "$Y" "$N"
    if [ -n "$installed_commit" ]; then
      when=$(recorded_value installed_at)
      if [ -n "$head" ] && [ "$installed_commit" = "$head" ]; then note="${G}same as this checkout${N}"
      elif [ -n "$head" ]; then note="${Y}this checkout is now at $head${N}"
      else note=''; fi
      printf '  installed    commit %s on %s  %s\n' "$installed_commit" "${when%%T*}" "$note"
    else
      printf '  installed    %sno install record yet%s\n' "$D" "$N"
    fi
    printf '  platforms    %s\n' "$(echo ${platforms:-none detected} ${dests:++ $dests})"
    printf '%s' "$lines"
    if [ "$pending" = 0 ] && [ "$sync" != behind ]; then
      printf '%s✔ Everything up to date.%s\n' "$G" "$N"
    else
      [ "$sync" != behind ] || printf '%s→ Run git pull to get the latest version from GitHub.%s\n' "$Y" "$N"
      [ "$pending" = 0 ] || printf '%s→ %d file(s) to install or update: bash %s install%s\n' "$Y" "$pending" "$(pretty "$repo/install.sh")" "$N"
    fi
  fi
  if [ "$pending" = 0 ] && [ "$sync" != behind ]; then return 0; else return 1; fi
}

# ── install ───────────────────────────────────────────────────────────────
hooks_dir() {
  h=$(git -C "$repo" rev-parse --git-path hooks)
  case $h in /*) echo "$h";; *) echo "$repo/$h";; esac
}
is_our_hook() { grep -q 'fp-control' "$1" 2>/dev/null && grep -q 'added by install.sh' "$1" 2>/dev/null; }

install_hook() {
  [ -n "$git_ok" ] || return 0
  hooks=$(hooks_dir)
  mkdir -p "$hooks"
  for name in $hook_names; do
    hook="$hooks/$name"
    if [ -f "$hook" ] && ! is_our_hook "$hook"; then
      printf '%s! %s already exists and is not ours — left unchanged%s\n' "$Y" "$(pretty "$hook")" "$N"
      continue
    fi
    before=$(sum "$hook")
    {
      printf '#!/bin/sh\n'
      printf '# fp-control %s hook — added by install.sh; remove with: bash install.sh uninstall\n' "$name"
      printf '# After git pull, show whether the installed copies match this checkout.\n'
      # post-rewrite also runs after `git commit --amend`; only a rebase can bring in new commits
      [ "$name" = post-rewrite ] && printf '[ "$1" = rebase ] || exit 0\n'
      printf 'bash "$(git rev-parse --show-toplevel)/install.sh" status --short --no-fetch || true\n'
    } > "$hook"
    chmod +x "$hook"
    [ "$before" = "$(sum "$hook")" ] || printf '  + git hook   %s (status after git pull)\n' "$(pretty "$hook")"
  done
}

cmd_install() {
  [ -n "$platforms$dests" ] || die "no supported agent found (~/.claude, ~/.cursor, ~/.codeium/windsurf) — use --platform or --dest DIR"
  git_info
  [ "$sync" != behind ] || printf '%s! This checkout is %s commit(s) behind origin/main — you are installing an older version. Run git pull first to get the latest.%s\n' "$Y" "$behind" "$N"
  [ -z "$dirty" ] || printf '%s! Uncommitted changes in skill files will be installed as they are.%s\n' "$Y" "$N"

  mkdir -p "$assets_dir" || die "cannot create $(pretty "$assets_dir")"
  new_record=$(mktemp "${TMPDIR:-/tmp}/fp-control-install.XXXXXX") || die "cannot create a temporary file"
  trap 'rm -f "$new_record"' EXIT
  changed=0 kept=0
  while IFS="$(printf '\t')" read -r src dst; do
    st=$(state_of "$src" "$dst")
    if [ "$st" = edited ] && [ "$force" != 1 ]; then
      printf '%s  = kept       %s (edited since install; --force to replace)%s\n' "$Y" "$(pretty "$dst")" "$N"
      kept=$((kept + 1))
      printf 'file %s %s\n' "$(recorded_sum "$dst")" "$dst" >> "$new_record"
      continue
    fi
    if [ "$st" != current ]; then
      mkdir -p "$(dirname "$dst")" && cp "$src" "$dst" || die "cannot write $(pretty "$dst")"
      case $dst in *.sh) chmod +x "$dst";; esac
      printf '  + %-10s %s\n' "$st" "$(pretty "$dst")"
      changed=$((changed + 1))
    fi
    printf 'file %s %s\n' "$(sum "$dst")" "$dst" >> "$new_record"
  done <<EOF
$(plan)
EOF
  {
    printf 'commit=%s\n' "${head:-unknown}"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'source=%s\n' "$repo"
    printf 'platforms=%s\n' "$(echo $platforms)"
    printf 'dests=%s\n' "$(echo $dests)"
    cat "$new_record"
  } > "$record"
  [ "$hook_wanted" = 1 ] && install_hook
  kept_note=''; [ "$kept" = 0 ] || kept_note=", kept $kept edited"
  printf '%sInstalled %d file(s)%s. Restart open agent sessions to load the new skills.%s\n\n' "$G" "$changed" "$kept_note" "$N"
  do_fetch=0
  cmd_status
}

cmd_uninstall() {
  [ -f "$record" ] || die "nothing recorded at $(pretty "$record")"
  awk '$1 == "file" { print $2 "\t" $3 }' "$record" | while IFS="$(printf '\t')" read -r was f; do
    [ -f "$f" ] || continue
    if [ "$was" != "$(sum "$f")" ] && [ "$force" != 1 ]; then
      printf '%s  = kept %s (edited since install; --force to remove)%s\n' "$Y" "$(pretty "$f")" "$N"
    else
      rm -f "$f" && printf '  - %s\n' "$(pretty "$f")"
    fi
  done
  rm -f "$record"
  git_info
  if [ -n "$git_ok" ]; then
    for name in $hook_names; do
      hook="$(hooks_dir)/$name"
      if is_our_hook "$hook"; then rm -f "$hook"; printf '  - %s\n' "$(pretty "$hook")"; fi
    done
  fi
  rmdir "$assets_dir" 2>/dev/null || true
  printf 'fp-control uninstalled.\n'
}

# ── Arguments ─────────────────────────────────────────────────────────────
[ $# -gt 0 ] || usage 1
cmd=$1; shift
platforms='' dests='' force=0 hook_wanted=1 do_fetch=1 short=0 explicit=''
while [ $# -gt 0 ]; do
  case $1 in
    --platform) explicit=1; platforms="$platforms $(printf '%s' "${2:?--platform needs a value}" | tr ',' ' ')"; shift 2;;
    --dest) explicit=1; dests="$dests ${2:?--dest needs a directory}"; shift 2;;
    --force) force=1; shift;;
    --no-hook) hook_wanted=0; shift;;
    --no-fetch) do_fetch=0; shift;;
    --short) short=1; shift;;
    -h|--help) usage;;
    *) die "unknown option $1";;
  esac
done
# Without --platform/--dest: the platforms of the last install, else the detected ones.
if [ -z "$explicit" ]; then
  platforms=$(recorded_value platforms); dests=$(recorded_value dests)
  [ -n "$platforms$dests" ] || platforms=$(detect_platforms)
fi
for p in $platforms; do platform_dir "$p" >/dev/null || die "unknown platform '$p' (use claude, cursor, windsurf, or --dest)"; done

case $cmd in
  status) cmd_status;;
  install) cmd_install;;
  uninstall) cmd_uninstall;;
  -h|--help|help) usage;;
  *) die "unknown command '$cmd' (use status, install, or uninstall)";;
esac
