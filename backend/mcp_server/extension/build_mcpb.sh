#!/usr/bin/env bash
# Empaqueta el manifest de esta carpeta en cfo-financiero.mcpb y lo copia
# al Escritorio de Windows de Bruno (vía /mnt/c, ya que Claude Desktop
# corre en Windows y no ve el filesystem de WSL directamente).
#
# Requiere: npx (Node.js) para invocar @anthropic-ai/mcpb sin instalarlo
# global. No requiere venv de Python — esto es solo empaquetado.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_NAME="cfo-financiero.mcpb"
DESKTOP_DEST="/mnt/c/Users/Brunito/Desktop/${OUTPUT_NAME}"

cd "$SCRIPT_DIR"

echo "== Validando manifest.json =="
npx --yes @anthropic-ai/mcpb validate manifest.json

echo "== Empaquetando =="
rm -f "$OUTPUT_NAME"
npx --yes @anthropic-ai/mcpb pack . "$OUTPUT_NAME"

if [ ! -f "$OUTPUT_NAME" ]; then
  echo "ERROR: no se generó $OUTPUT_NAME" >&2
  exit 1
fi

echo "== Verificando estructura del paquete =="
python3 -m zipfile -l "$OUTPUT_NAME"

python3 - "$OUTPUT_NAME" <<'PY'
import sys, zipfile
path = sys.argv[1]
with zipfile.ZipFile(path) as z:
    names = z.namelist()
    if "manifest.json" not in names:
        print("ERROR: el paquete no contiene manifest.json en la raíz", file=sys.stderr)
        sys.exit(1)
    bad = z.testzip()
    if bad:
        print(f"ERROR: archivo corrupto dentro del zip: {bad}", file=sys.stderr)
        sys.exit(1)
    print(f"OK: manifest.json presente, {len(names)} archivos, zip íntegro")
PY

echo "== Copiando al Escritorio de Windows =="
mkdir -p "$(dirname "$DESKTOP_DEST")"
cp "$OUTPUT_NAME" "$DESKTOP_DEST"

echo "== Listo =="
echo "Paquete local:  $SCRIPT_DIR/$OUTPUT_NAME"
echo "Copiado a:      $DESKTOP_DEST"
ls -la "$DESKTOP_DEST"
