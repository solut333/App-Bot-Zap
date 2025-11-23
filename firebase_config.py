# firebase_config.py
import os

# --- CONFIGURAÇÃO DA API DE AUTENTICAÇÃO DO FIREBASE ---
# Defina esta variável de ambiente com sua "Web API Key" do Firebase.
FIREBASE_WEB_API_KEY = os.environ.get("FIREBASE_WEB_API_KEY")

# --- CONFIGURAÇÃO DO ADMIN SDK ---
# Coloque o caminho para o seu arquivo de credencial JSON que você baixou do Firebase.
# Este arquivo NUNCA deve ser enviado para o GitHub. Adicione-o ao .gitignore.
FIREBASE_CREDENTIALS_PATH = "admin-key.json"

# --- CONFIGURAÇÃO DA CONTA DE ADMINISTRADOR ---
# Defina esta variável de ambiente com o e-mail do administrador.
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")

# --- CONFIGURAÇÃO DE E-MAIL (PARA NOTIFICAÇÕES) ---
# IMPORTANTE: Para Gmail, use uma "Senha de App", não sua senha normal.
# Veja como: https://support.google.com/accounts/answer/185833
# Defina estas variáveis de ambiente com suas credenciais de e-mail.
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# --- CONFIGURAÇÃO DE ÍCONE ---
# Coloque o nome do arquivo do ícone do seu aplicativo aqui.
APP_ICON_PATH = "app_icon.png"
