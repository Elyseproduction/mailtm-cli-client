# mailtm_cli.py 
import json
import os
import requests
import random
import string
import re
import html2text
import time
import sys
import uuid 
import platform 
from requests.exceptions import ConnectionError, ReadTimeout

# --- CONSTANTES GLOBALES ---
API_BASE = "https://api.mail.tm"
ACCOUNT_FILE = "mailtm_account.json"
DEVICE_ID_FILE = "mailtm_device_id.txt"
LAST_ACCESS_CODE_FILE = "last_access_code.txt" 
MAX_DISPLAY_MESSAGES = 50 

# !!!!!!! REMPLACEZ CETTE VALEUR !!!!!!!
# Ceci est l'adresse IP/Domaine de votre serveur qui exécute api_server.py
# Exemple: "http://192.168.1.100:5000" ou "http://mon-serveur.com:5000"
ACCESS_API_URL = "http://VOTRE_IP_PUBLIQUE:5000" 
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# --- COULEURS ANSI ---
R = '\033[0m'
NOIR = '\033[30m'
ROUGE = '\033[31m'
VERT = '\033[32m'
JAUNE = '\033[33m'
BLEU = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m' 
BLANC = '\033[37m'
GRAS = '\033[1m'

# --- FONCTIONS SYSTÈME ET ANIMATIONS ---

def clear_screen():
    """Efface le contenu de la console/terminal de manière robuste."""
    system_name = platform.system()
    if system_name == "Windows":
        os.system('cls') 
        os.system('clear') 
    else:
        os.system('clear')

def loading_spinner(text: str, duration: float = 2.0):
    """Affiche un spinner de chargement professionnel non bloquant (visuel)."""
    spinner = ['|', '/', '-', '\\']
    start_time = time.time()
    i = 0
    full_text = f"{CYAN}{GRAS}{text}{R} "
    
    while time.time() - start_time < duration:
        sys.stdout.write(f"\r{full_text} {CYAN}{spinner[i % len(spinner)]}{R}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    
    sys.stdout.write(f"\r{' ' * (len(full_text) + 5)}\r")
    sys.stdout.flush()

# --- FONCTIONS DE BASE ---

MOBILE_USER_AGENTS = [
    'Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Android 11; Mobile; rv:88.0) Gecko/88.0 Firefox/88.0',
    'Mozilla/5.0 (Linux; Android 9; Pixel 3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Mobile Safari/537.36',
]

def get_random_user_agent() -> str:
    return random.choice(MOBILE_USER_AGENTS)

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def get_or_create_device_id() -> str:
    """Récupère l'ID unique de cet appareil ou le crée s'il n'existe pas."""
    # ... (Code inchangé pour device_id)
    if os.path.exists(DEVICE_ID_FILE):
        try:
            with open(DEVICE_ID_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return content
        except Exception:
            pass
    
    new_id = str(uuid.uuid4())
    try:
        with open(DEVICE_ID_FILE, 'w') as f:
            f.write(new_id)
        return new_id
    except Exception as e:
        print(f"{ROUGE}ATTENTION: Échec de la sauvegarde de l'ID du périphérique: {e}. L'accès peut être perdu lors des prochaines utilisations.{R}")
        return new_id 

# --- FONCTIONS DE GESTION DU CODE D'ACCÈS PERMANENT ---

def save_last_access_code(code: str):
    """Sauvegarde le dernier code d'accès valide utilisé."""
    try:
        with open(LAST_ACCESS_CODE_FILE, 'w') as f:
            f.write(code.strip())
    except Exception:
        pass

def load_last_access_code() -> str:
    """Charge le dernier code d'accès sauvegardé."""
    if os.path.exists(LAST_ACCESS_CODE_FILE):
        try:
            with open(LAST_ACCESS_CODE_FILE, 'r') as f:
                return f.read().strip()
        except Exception:
            pass
    return ""
    
# --- NOUVELLE FONCTION DE VÉRIFICATION À DISTANCE ---

def check_remote_access(code: str, device_id: str) -> tuple[bool, str]:
    """Appelle le serveur API distant pour valider le code d'accès."""
    try:
        # Le spinner dure plus longtemps ici car il y a un délai réseau
        loading_spinner("Vérification de l'accès via l'API distante...", 3.0) 
        
        url = f"{ACCESS_API_URL}/check_code"
        headers = {'Content-Type': 'application/json'}
        payload = {'code': code, 'device_id': device_id}
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status() # Lève une erreur pour les statuts HTTP 4xx/5xx (ex: 404, 500)

        data = response.json()
        return data.get('valid', False), data.get('message', 'Réponse serveur invalide.')
        
    except requests.exceptions.RequestException as e:
        return (False, f"❌ Erreur de connexion au serveur ({ACCESS_API_URL}). Vérifiez l'adresse ou la connexion internet. Erreur: {e}")
    except Exception as e:
        return (False, f"❌ Erreur de vérification: {e}")


# --- CLASSE MAILTM (Code inchangé) ---

class MailTmCLI:
    def __init__(self):
        self.account = self.load_account()
        
    # ... (Les méthodes load_account, save_account, get_domains, login, create_account, get_messages, get_message, 
    # display_inbox, display_message_content restent inchangées)
    
    def load_account(self) -> dict:
        """Charge le compte (email/password/token) depuis le fichier local."""
        try:
            if os.path.exists(ACCOUNT_FILE):
                with open(ACCOUNT_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            pass 
        return {}

    def save_account(self):
        """Sauvegarde le compte dans le fichier local."""
        try:
            with open(ACCOUNT_FILE, 'w') as f:
                json.dump(self.account, f, indent=4)
        except Exception as e:
            print(f"{ROUGE}Erreur lors de la sauvegarde de {ACCOUNT_FILE}: {e}{R}")

    def get_domains(self):
        """Récupère la liste des domaines disponibles auprès de Mail.tm."""
        try:
            loading_spinner("Contact API Mail.tm...", 2.0) 
            headers = {'User-Agent': get_random_user_agent()}
            response = requests.get(f"{API_BASE}/domains", headers=headers, timeout=10)
            
            if response.status_code == 200:
                domains = response.json()
                if domains and isinstance(domains, list):
                    return [d['domain'] for d in domains]
                if domains and 'hydra:member' in domains:
                    return [d['domain'] for d in domains['hydra:member']]
        except Exception as e:
            print(f"{ROUGE}❌ Erreur récupération domaines: {e}{R}")
        return []

    def login(self, email, password):
        """Tente de se connecter et d'obtenir un jeton JWT."""
        try:
            loading_spinner("Authentification en cours...", 1.5) 
            headers = {'User-Agent': get_random_user_agent()}
            data = {"address": email, "password": password}
            response = requests.post(f"{API_BASE}/token", json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json().get('token')
        except Exception as e:
            print(f"{ROUGE}Erreur login: {e}{R}")
        return None

    def create_account(self):
        """Crée un nouveau compte Mail.tm et le sauvegarde localement."""
        print(f"{JAUNE}🔍 Préparation de la création de compte...{R}")
        domains = self.get_domains()
        if not domains:
            print(f"{ROUGE}❌ Aucun domaine disponible. Vérifiez la connexion API.{R}")
            return

        domain = random.choice(domains)
        username = generate_random_string(8)
        email = f"{username}@{domain}"
        password = generate_random_string(12)
        
        data = {"address": email, "password": password}
        delay = random.uniform(1.5, 4.0)
        
        loading_spinner(f"Création de {email} (Attente {delay:.1f}s)", delay) 
        
        try:
            headers = {'User-Agent': get_random_user_agent()}
            response = requests.post(
                f"{API_BASE}/accounts",
                json=data,
                headers=headers,
                timeout=10
            )

            if response.status_code == 201:
                token = self.login(email, password)
                if token:
                    self.account = {
                        "email": email,
                        "password": password,
                        "token": token
                    }
                    self.save_account()
                    print(f"\n{VERT}{GRAS}✅ Compte créé avec succès !{R}")
                    print(f"📧 Email: {email}")
                    print(f"🔑 Mot de passe: {password}")
                    return
        except Exception as e:
            print(f"{ROUGE}❌ Erreur lors de la création du compte: {e}{R}")
        
        print(f"{ROUGE}❌ Échec de la création du compte.{R}")

    def get_messages(self) -> list:
        """Récupère la liste des messages (résumés) de l'Inbox."""
        if not self.account or 'token' not in self.account:
            print(f"{JAUNE}⚠️ Erreur: Aucun jeton actif. Veuillez créer un compte d'abord.{R}")
            return []
            
        try:
            loading_spinner("Récupération des messages...", 2.0) 
            headers = {"Authorization": f"Bearer {self.account['token']}", 'User-Agent': get_random_user_agent()}
            response = requests.get(f"{API_BASE}/messages", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('hydra:member', [])
            elif response.status_code == 401:
                print(f"{JAUNE}⚠️ Jeton expiré ou invalide. Essayez de recréer un compte.{R}")
                return []
                
        except Exception as e:
            print(f"{ROUGE}❌ Erreur récupération messages: {e}{R}")
            
        return []

    def get_message(self, message_id: str) -> dict or None:
        """Récupère les détails complets d'un message par son ID."""
        if not self.account or 'token' not in self.account:
            return None
            
        try:
            loading_spinner("Téléchargement du message...", 1.5) 
            headers = {"Authorization": f"Bearer {self.account['token']}", 'User-Agent': get_random_user_agent()}
            response = requests.get(
                f"{API_BASE}/messages/{message_id}",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            print(f"{ROUGE}❌ Erreur lecture message: {e}{R}")
            
        return None
    
    def display_inbox(self):
        """Affiche le contenu résumé de l'Inbox."""
        if not self.account:
            print(f"{JAUNE}⚠️ Aucun compte actif. Veuillez créer un compte (option 1).{R}")
            return
            
        print(f"\n{VERT}🔍 Vérification de la boîte de réception pour: {self.account['email']}...{R}")
        messages = self.get_messages()
        
        if not messages:
            print(f"{JAUNE}📭 Aucun email reçu.{R}")
            return

        print(f"\n📬 {len(messages)} message(s) reçu(s) (Affichage des {min(len(messages), MAX_DISPLAY_MESSAGES)} premiers):")
        print(f"{BLEU}=" * 50 + R) 
        
        for i, msg_data in enumerate(messages[:MAX_DISPLAY_MESSAGES], 1):
            sender = msg_data.get('from', {}).get('address', 'Inconnu')
            subject = msg_data.get('subject', 'Sans objet')
            date = msg_data.get('createdAt', '')[:10]
            msg_id = msg_data.get('id', '') 

            print(f"{MAGENTA}{i}. De: {R}{sender}")
            print(f"   Objet: {subject}")
            print(f"   Date: {date}")
            print(f"   {GRAS}{CYAN}ID:{R} {msg_id}") 
            print("-" * 50)
            
    def display_message_content(self, msg_id: str):
        """Affiche le contenu d'un message donné et tente d'extraire un code de confirmation."""
        if not msg_id:
            print(f"{ROUGE}❌ L'ID du message ne peut pas être vide.{R}")
            return
            
        print(f"\n{JAUNE}📖 Préparation de l'affichage du message ID: {msg_id}...{R}")
        message = self.get_message(msg_id)
        
        if not message:
            print(f"{ROUGE}❌ Impossible de charger le message (non trouvé ou erreur réseau).{R}")
            return
            
        sender = message.get('from', {}).get('address', 'Inconnu')
        subject = message.get('subject', 'Sans objet')
        text_content = message.get('text', 'Pas de contenu texte')
        html_content = message.get('html', [''])[0] if message.get('html') and message['html'] else ''

        h = html2text.HTML2Text()
        h.body_width = 0 
        h.inline_links = True 
        h.ignore_images = True 
        content = h.handle(html_content) if html_content else text_content
        
        def extract_confirmation_code(text: str) -> str or None:
            """Recherche les codes PIN/OTP courants dans le texte."""
            pattern_num = r'\b(\d{4,8})\b'
            match_num = re.search(pattern_num, text)
            if match_num:
                return match_num.group(1)
            pattern_alphanum = r'\b([A-Z0-9]{6,8})\b'
            match_alphanum = re.search(pattern_alphanum, text)
            if match_alphanum:
                return match_alphanum.group(1)
            return None

        code = extract_confirmation_code(content)
        
        print("\n" + f"{BLEU}={R}" * 50)
        print(f"De: {MAGENTA}{sender}{R}")
        print(f"Objet: {GRAS}{subject}{R}")
        if code:
            print(f"{VERT}{GRAS}🔥 CODE DE CONFIRMATION DÉTECTÉ: {code} 🔥{R}")
        print(f"{BLEU}={R}" * 50)
        print("\nCONTENU DU MESSAGE:\n")
        print(content)
        print("\n" + f"{BLEU}={R}" * 50)


# --- FONCTION PRINCIPALE MODIFIÉE ---

def main_cli():
    """Fonction principale pour l'interface en ligne de commande avec vérification de l'accès permanent DISTANTE."""
    
    clear_screen()
    print(f"{VERT}{GRAS}🤖 Mail.tm CLI - Gestion d'Email Temporaire (Termux){R}")
    
    # REMOVED: access_manager = AccessManager()
    device_id = get_or_create_device_id()
    cli = MailTmCLI() 

    start_interface = False
    valid_access_code = load_last_access_code()

    # --- ÉTAPE 1: VÉRIFICATION AVEC LE DERNIER CODE SAUVEGARDÉ (DISTANTE) ---
    if valid_access_code:
        print(f"{CYAN}Vérification de l'accès permanent avec le code sauvegardé...{R}")
        is_valid, status_message = check_remote_access(valid_access_code, device_id)
        
        if is_valid:
            print(f"{VERT}✅ Accès permanent validé. {status_message}. Démarrage de l'interface.{R}")
            start_interface = True
        else:
            print(f"{ROUGE}❌ Code permanent invalide/expiré ou erreur serveur: {status_message}{R}")
            valid_access_code = "" 
            
    # --- ÉTAPE 2: DEMANDE D'UN NOUVEAU CODE SI NON DÉMARRÉ ---
    if not start_interface:
        access_code_input = input(f"{GRAS}🔐 Veuillez entrer le code d'accès: {R}").strip()

        if not access_code_input:
            print(f"{ROUGE}❌ Opération annulée. Aucun code entré.{R}")
            return

        # VÉRIFICATION DISTANTE DU NOUVEAU CODE
        is_valid, status_message = check_remote_access(access_code_input, device_id)
        
        if not is_valid:
            print(f"{ROUGE}❌ ACCÈS REFUSÉ: {status_message}{R}")
            return
            
        print(f"{VERT}✅ Code d'accès valide. {status_message}. Démarrage de l'interface.{R}")
        
        save_last_access_code(access_code_input)
        start_interface = True
    
    if not start_interface:
        return
        
    while True:
        clear_screen() 
        print(f"{VERT}{GRAS}🤖 Mail.tm CLI - Menu Principal{R}")
        
        print(f"\n{GRAS}--- Menu Principal ---{R}")
        
        # Affichage du statut du compte et de l'Option 1
        if cli.account:
            print(f"📧 Compte actif: {CYAN}{cli.account['email']}{R}")
            print(f"{CYAN}1. [Désactivé] (Supprimer le compte actif d'abord){R}")
        else:
            print(f"{JAUNE}⚠️ Pas de compte actif. Vous devez en créer un.{R}")
            print(f"{CYAN}1. Créer une nouvelle adresse email{R}")
            
        print(f"\n{GRAS}--- Actions ---{R}") 
        
        print(f"{VERT}2. Voir la boîte de réception (Inbox){R}")
        print(f"{BLEU}3. Lire un message par ID{R}")
        print(f"{ROUGE}4. Supprimer le compte local et quitter{R}")
        print(f"{JAUNE}5. Quitter{R}")
        
        choice = input(f"\n{GRAS}Votre choix (1-5): {R}").strip()
        
        if choice == '1':
            if not cli.account:
                cli.create_account()
            else:
                print(f"{JAUNE}❌ Veuillez d'abord {ROUGE}supprimer votre compte actif (Option 4){JAUNE} avant d'en créer un nouveau.{R}")
                
        elif choice == '2':
            cli.display_inbox()
            
        elif choice == '3':
            msg_id = input("Entrez l'ID du message à lire (ex: 1d9e...c7b): ").strip()
            if msg_id:
                cli.display_message_content(msg_id)
            
        elif choice == '4':
            if os.path.exists(ACCOUNT_FILE):
                email_to_print = cli.account.get('email', 'précédent') 
                os.remove(ACCOUNT_FILE)
                cli.account = {}
                print(f"{VERT}✅ Compte local supprimé. Le mail {email_to_print} restera actif sur Mail.tm jusqu'à sa purge.{R}")
            else:
                print(f"{JAUNE}❌ Aucun fichier de compte à supprimer.{R}")
                
        elif choice == '5':
            print(f"{VERT}👋 Au revoir.{R}")
            break
            
        else:
            print(f"{ROUGE}Choix invalide. Veuillez réessayer.{R}")
            
        if choice not in ['5', '1', '4']: 
            input(f"{JAUNE}{GRAS}Appuyez sur Entrée pour revenir au menu...{R}")


if __name__ == '__main__':
    try:
        import requests, html2text, uuid, platform
        # Vérifiez que la constante critique est définie
        if ACCESS_API_URL == "http://VOTRE_IP_PUBLIQUE:5000":
             print(f"{ROUGE}FATAL: Veuillez modifier la constante ACCESS_API_URL dans le script mailtm_cli.py avant l'exécution!{R}")
             sys.exit(1)
             
        main_cli()
    except ImportError as e:
        print(f"\n{ROUGE}--- ERREUR ---{R}")
        print(f"Dépendance manquante: {e}")
        print(f"Veuillez installer les paquets requis via pip: pip install requests html2text{R}")
        print(f"--------------{R}\n")
