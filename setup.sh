#!/bin/bash

# ─────────────────────────────────────────
#  Theia Guard — Setup Script
# ─────────────────────────────────────────

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "╔══════════════════════════════════════╗"
echo "║        THEIA GUARD — SETUP           ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Python version check
PYTHON=$(command -v python3 || true)
if [ -z "$PYTHON" ]; then
  echo -e "${RED}✗ python3 bulunamadı. Lütfen Python 3.10+ yükleyin.${NC}"
  exit 1
fi

PY_VERSION=$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}✓ Python $PY_VERSION bulundu${NC}"

# Pip dependencies
echo ""
echo "Bağımlılıklar yükleniyor..."
$PYTHON -m pip install -r requirements.txt --break-system-packages -q
echo -e "${GREEN}✓ Bağımlılıklar yüklendi${NC}"

# .env setup
echo ""
if [ -f ".env" ]; then
  echo -e "${YELLOW}⚠ .env dosyası zaten mevcut, atlanıyor.${NC}"
else
  echo ".env dosyası oluşturuluyor..."
  cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
EOF
  echo -e "${GREEN}✓ .env dosyası oluşturuldu${NC}"
  echo -e "${YELLOW}  → .env dosyasını açıp API anahtarlarınızı girin!${NC}"
fi

# Bash aliases
echo ""
echo "Bash alias'ları ekleniyor..."
BASHRC="$HOME/.bashrc"
if ! grep -q "alias t=" "$BASHRC" 2>/dev/null; then
  echo "" >> "$BASHRC"
  echo "# Theia Guard" >> "$BASHRC"
  echo "alias t='cd $(pwd) && python3 api_server.py'" >> "$BASHRC"
  echo "alias tg='cd $(pwd) && python3 gatekeeper.py'" >> "$BASHRC"
  echo -e "${GREEN}✓ Alias'lar .bashrc'ye eklendi${NC}"
else
  echo -e "${YELLOW}⚠ Alias'lar zaten mevcut, atlanıyor.${NC}"
fi

echo ""
echo "╔══════════════════════════════════════╗"
echo "║           KURULUM TAMAM ✓            ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "Sonraki adımlar:"
echo "  1. .env dosyasına API anahtarlarınızı ekleyin"
echo "  2. source ~/.bashrc  (alias'ları aktif et)"
echo "  3. t                 (API sunucusunu başlat)"
echo "  4. Tarayıcıdan: http://YOUR_IP:5000"
echo ""
