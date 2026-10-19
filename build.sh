#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
cd "$root"

py=python
command -v python >/dev/null 2>&1 || py=python3
export SECRET_KEY="${SECRET_KEY:-build-collectstatic}"

"$py" -m pip install -r backend/requirements.txt

if ! command -v node >/dev/null 2>&1; then
  node_version="v22.14.0"
  curl -fsSL "https://nodejs.org/dist/${node_version}/node-${node_version}-linux-x64.tar.xz" \
    | tar -xJ -C /tmp
  export PATH="/tmp/node-${node_version}-linux-x64/bin:${PATH}"
fi

cd frontend
npm ci
npm run build
rm -rf ../backend/frontend_dist
mkdir -p ../backend/frontend_dist
cp -r dist/. ../backend/frontend_dist/

cd ../backend
"$py" manage.py collectstatic --noinput
