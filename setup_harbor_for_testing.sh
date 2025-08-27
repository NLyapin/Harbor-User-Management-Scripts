#!/usr/bin/env bash
set -euo pipefail

HARBOR_VERSION="2.11.0"
HARBOR_HOST="localhost"
HARBOR_ADMIN_PASSWORD="Harbor12345"

# Проверяем зависимости
for bin in curl tar docker docker-compose; do
  if ! command -v $bin &>/dev/null; then
    echo "[ERROR] $bin не найден, установите его."
    exit 1
  fi
done

# Скачиваем Harbor, если нет
if [ ! -d "harbor" ]; then
  echo "[*] Downloading Harbor ${HARBOR_VERSION}..."
  curl -LO https://github.com/goharbor/harbor/releases/download/v${HARBOR_VERSION}/harbor-online-installer-v${HARBOR_VERSION}.tgz
  tar xvf harbor-online-installer-v${HARBOR_VERSION}.tgz
else
  echo "[*] Harbor already downloaded."
fi

cd harbor

# Генерация конфига
if [ ! -f harbor.yml ]; then
  cp harbor.yml.tmpl harbor.yml
  # Убираем HTTPS, ставим localhost
  sed -i "s/hostname: reg.mydomain.com/hostname: ${HARBOR_HOST}/g" harbor.yml
  sed -i "s/Harbor12345/${HARBOR_ADMIN_PASSWORD}/g" harbor.yml
  # Отключаем https
  sed -i "s/^  https: .*/  https: off/" harbor.yml
fi

echo "[*] Installing Harbor..."
./install.sh --with-trivy

echo "[*] Harbor installed. Check containers:"
docker-compose ps
