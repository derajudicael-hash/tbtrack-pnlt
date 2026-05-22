#!/bin/bash
# Script d'installation automatique TBTrack sur PythonAnywhere
# Lance ce script UNE SEULE FOIS dans la console Bash de PythonAnywhere

set -e
PA_USER=$(whoami)
REPO="https://github.com/derajudicael-hash/tbtrack-pnlt.git"
APP_DIR="/home/$PA_USER/tbtrack-pnlt"

echo ""
echo "=== TBTrack — Installation PythonAnywhere ==="
echo "Utilisateur : $PA_USER"
echo ""

# 1. Cloner le dépôt
echo "[1/5] Clonage du dépôt GitHub..."
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR" && git pull
else
    git clone "$REPO" "$APP_DIR"
fi
cd "$APP_DIR"

# 2. Environnement virtuel Python 3.11
echo "[2/5] Création de l'environnement virtuel..."
python3.11 -m venv .venv
source .venv/bin/activate

# 3. Dépendances
echo "[3/5] Installation des dépendances..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# 4. Fichier .env
echo "[4/5] Génération de la clé secrète..."
SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
cat > .env << ENVEOF
FLASK_ENV=production
SECRET_KEY=$SECRET
ENVEOF
echo "  Clé générée."

# 5. Générer le fichier WSGI
echo "[5/5] Génération du fichier wsgi_pa.py..."
cat > wsgi_pa.py << WSGIEOF
import sys, os
from dotenv import load_dotenv

app_dir = '/home/$PA_USER/tbtrack-pnlt'
sys.path.insert(0, app_dir)
load_dotenv(os.path.join(app_dir, '.env'))

from app import create_app
application = create_app()
WSGIEOF

echo ""
echo "=============================================="
echo "  INSTALLATION TERMINÉE"
echo "=============================================="
echo ""
echo "Prochaine étape — configure l'app web :"
echo ""
echo "  Virtualenv  : $APP_DIR/.venv"
echo "  Fichier WSGI: $APP_DIR/wsgi_pa.py"
echo ""
echo "Dans l'onglet Web de PythonAnywhere :"
echo "  1. Source code  : $APP_DIR"
echo "  2. Virtualenv   : $APP_DIR/.venv"
echo "  3. WSGI file    : colle le contenu de wsgi_pa.py"
echo "  4. Clic Reload"
echo ""
