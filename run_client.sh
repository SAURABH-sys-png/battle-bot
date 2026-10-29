#!/usr/bin/env bash
# Launches the Battlecode client (replay viewer).
#
# Why not just run the AppImage? It bundles its own libwayland-* libraries, which clash
# with the system's Mesa EGL driver ("Could not create default EGL display:
# EGL_BAD_PARAMETER. Aborting..."). WebKit's renderer process then dies and the window
# stays blank white. So we extract the AppImage once, delete the bundled Wayland libs so
# the system ones are used, and run it from the extracted folder. Extracting also means
# FUSE (libfuse2) is not needed, which WSL usually lacks.
#
# If the window is still white (e.g. on WSL without GPU support), try:
#   WEBKIT_DISABLE_COMPOSITING_MODE=1 ./run_client.sh
#   LIBGL_ALWAYS_SOFTWARE=1 ./run_client.sh
set -euo pipefail
cd "$(dirname "$0")"

appimages=(client/*.AppImage)
appimage="${appimages[0]}"
if [ ! -f "$appimage" ]; then
  echo "No client AppImage found in client/. Run ./gradlew build first." >&2
  exit 1
fi

dir=client/extracted
stamp="$dir/.source"
source_id="$(stat -c '%s %Y' "$appimage")"

# Re-extract only when the AppImage changed (e.g. after a client update)
if [ ! -f "$stamp" ] || [ "$(cat "$stamp")" != "$source_id" ]; then
  echo "Extracting client..."
  rm -rf "$dir" client/squashfs-root
  (cd client && "./$(basename "$appimage")" --appimage-extract > /dev/null)
  mv client/squashfs-root "$dir"
  rm -f "$dir"/usr/lib/libwayland-*.so*
  echo "$source_id" > "$stamp"
fi

# Avoids another common cause of blank WebKitGTK windows (DMA-BUF renderer on WSL/NVIDIA)
export WEBKIT_DISABLE_DMABUF_RENDERER="${WEBKIT_DISABLE_DMABUF_RENDERER:-1}"

exec "$dir/AppRun" "$@"
