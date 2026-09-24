#!/usr/bin/env bash
# fp-control helper — build HTML reports from .fpa.yaml files.
#
#   bash fpa.sh report <file.fpa.yaml> [--lang pt-BR] [--labels labels.json]
#                      [--accent '#4F46E5'] [--accent-dark '#818CF8'] [--theme light|dark|auto]
#                      [-o <output.html>]
#   bash fpa.sh check  <file.fpa.yaml> [--strict]
#
# `report` needs only bash and standard Unix tools (cp, cat, sed, awk). It copies the report
# template and appends the YAML files unchanged — the template parses them in the browser
# and runs every consistency check, so the data is never converted or re-typed.
#
# `check` prints the same checks in the terminal. It is optional and runs fpa.py, which
# needs python3 + PyYAML; without them, open the report instead.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
template="$here/fp-report.html"

die() { printf 'fpa.sh: %s\n' "$*" >&2; exit 1; }
usage() { awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"; exit "${1:-0}"; }

# Inside a <script> block only "</script" and "<!--" are special; the template undoes this.
# Bracket expressions keep the match case-insensitive on both GNU and BSD sed.
escape_block() { sed -e 's#</\([Ss][Cc][Rr][Ii][Pp][Tt]\)#<\\/\1#g' -e 's#<!--#<\\!--#g' "$1"; }
escape_attr() { printf '%s' "$1" | sed -e 's/&/\&amp;/g' -e 's/"/\&quot;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g'; }

# Print the file names listed under detail_files (block or flow style), one per line.
detail_files() {
  # q holds a single quote: portable across gawk, mawk, BSD awk and busybox (no octal escapes)
  awk -v q="'" '
    function emit(v) {
      sub(/^[^:]*:[ \t]*/, "", v); sub(/[ \t]+#.*$/, "", v)
      gsub("^[ \t\"" q "]+|[ \t\"" q "]+$", "", v)
      if (v != "") print v
    }
    /^detail_files:[ \t]*\{/ {
      line = $0; sub(/^detail_files:[ \t]*\{/, "", line); sub(/\}.*$/, "", line)
      n = split(line, parts, ","); for (i = 1; i <= n; i++) emit(parts[i]); next
    }
    /^detail_files:[ \t]*(#.*)?$/ { inblock = 1; next }
    inblock && /^[^ \t#]/ { inblock = 0 }
    inblock && /^[ \t]+[A-Za-z_]+[ \t]*:/ { emit($0) }
  ' "$1"
}

check_lang()  { case $1 in ''|*[!A-Za-z0-9-]*) die "invalid --lang '$1' (use a tag like en or pt-BR)";; esac; }
check_color() { case $1 in '#'*) case ${1#\#} in ''|*[!0-9A-Fa-f]*) die "invalid color '$1' (use #RRGGBB)";; esac;; *) die "invalid color '$1' (use #RRGGBB)";; esac; }

cmd_report() {
  input='' out='' lang='' labels='' accent='' accent_dark='' theme=''
  while [ $# -gt 0 ]; do
    case $1 in
      --lang) lang=${2:?--lang needs a value}; check_lang "$lang"; shift 2;;
      --labels) labels=${2:?--labels needs a file}; shift 2;;
      --accent) accent=${2:?--accent needs a value}; check_color "$accent"; shift 2;;
      --accent-dark) accent_dark=${2:?--accent-dark needs a value}; check_color "$accent_dark"; shift 2;;
      --theme) theme=${2:?--theme needs a value}; case $theme in light|dark|auto) ;; *) die "invalid --theme '$theme'";; esac; shift 2;;
      -o|--output) out=${2:?-o needs a path}; shift 2;;
      -h|--help) usage;;
      -*) die "unknown option $1";;
      *) [ -z "$input" ] || die "only one input file"; input=$1; shift;;
    esac
  done
  [ -n "$input" ] || usage 1
  [ -f "$input" ] || die "file not found: $input"
  [ -f "$template" ] || die "template not found: $template"
  [ -z "$labels" ] || [ -f "$labels" ] || die "labels file not found: $labels"

  dir=$(dirname "$input") name=$(basename "$input")
  if [ -z "$out" ]; then
    case $name in
      *.fpa.yaml) stem=${name%.fpa.yaml};;
      *.yaml) stem=${name%.yaml};;
      *.yml) stem=${name%.yml};;
      *) stem=$name;;
    esac
    out="$dir/$stem.html"
  fi

  # Options are optional: the report falls back to the file's report_style, then to defaults.
  style=''
  [ -z "$theme" ] || style="$style,\"theme\":\"$theme\""
  [ -z "$accent" ] || style="$style,\"accent\":\"$accent\""
  [ -z "$accent_dark" ] || style="$style,\"accent_dark\":\"$accent_dark\""
  options="{\"lang\":\"${lang:-en}\""
  [ -z "$style" ] || options="$options,\"style\":{${style#,}}"
  options="$options}"

  tmp="$out.tmp.$$"
  trap 'rm -f "$tmp"' EXIT
  {
    cat "$template"
    printf '<script type="application/json" id="fpa-options">%s</script>\n' "$options"
    if [ -n "$labels" ]; then
      printf '<script type="application/json" id="fpa-labels">'; escape_block "$labels"; printf '</script>\n'
    fi
    printf '<script type="text/yaml" data-role="index" data-name="%s">\n' "$(escape_attr "$name")"
    escape_block "$input"
    printf '</script>\n'
    detail_files "$input" | while IFS= read -r f; do
      if [ -f "$dir/$f" ]; then
        printf '<script type="text/yaml" data-role="detail" data-name="%s">\n' "$(escape_attr "$f")"
        escape_block "$dir/$f"
        printf '</script>\n'
      else
        printf 'fpa.sh: warning: detail file not found: %s\n' "$f" >&2
      fi
    done
  } > "$tmp"
  mv "$tmp" "$out"
  trap - EXIT
  printf '%s\n' "$out"
}

cmd_check() {
  if command -v python3 >/dev/null 2>&1 && python3 -c 'import yaml' >/dev/null 2>&1; then
    exec python3 "$here/fpa.py" check "$@"
  fi
  printf '%s\n' \
    'fpa.sh check needs python3 with PyYAML (optional tools, not required by the skills).' \
    'Without them, build the report (bash fpa.sh report <file>) and open it: it runs the same' \
    'checks and lists any problem in its "Consistency checks" box.' >&2
  exit 2
}

[ $# -gt 0 ] || usage 1
sub=$1; shift
case $sub in
  report) cmd_report "$@";;
  check) cmd_check "$@";;
  -h|--help|help) usage;;
  *) die "unknown command '$sub' (use report or check)";;
esac
