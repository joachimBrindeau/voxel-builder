#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/lib.sh"

fail() {
  printf 'lib helper test failed: %s\n' "$1" >&2
  exit 1
}

fixture=$(mktemp -d)
trap 'rm -rf "$fixture"' EXIT HUP INT TERM

mkdir -p "$fixture/cli/src"
: > "$fixture/cli/src/index.ts"
printf '#!/bin/sh\nexit 0\n' > "$fixture/wpdev"
chmod +x "$fixture/wpdev"

actual=$(WPDEV_ROOT="$fixture" find_wpdev_root)
[ "$actual" = "$fixture" ] || fail "WPDEV_ROOT did not resolve to the explicit executable checkout"

actual=$(WPDEV_ROOT= WPDEV_SOURCE_ROOT="$fixture" find_wpdev_root)
[ "$actual" = "$fixture" ] || fail "WPDEV_SOURCE_ROOT did not resolve to the explicit source checkout"

printf 'lib helper tests OK (WPDEV_ROOT and WPDEV_SOURCE_ROOT overrides)\n'
