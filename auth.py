"""
Modulo per l'autenticazione semplice degli utenti.
Gestisce:
- Login con username e password
- Verifica credenziali da JSON/DB
- Sessione utente

NOTA: Questo è un sistema di autenticazione minimale per sviluppo.
Per produzione, considerare soluzioni più robuste (OAuth, hash password, ecc.)
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class User:
    """Rappresenta un utente autenticato"""
    username: str
    display_name: str
    role: str = "student"  # Possibili ruoli: student, admin


class AuthManager:
    """
    Gestisce l'autenticazione degli utenti.
    Gli utenti sono memorizzati in un file JSON.
    """
    
    def __init__(self, users_file: str = "users.json"):
        """
        Inizializza il gestore autenticazione
        
        Args:
            users_file: percorso al file JSON con le credenziali
        """
        self.users_file = Path(users_file)
        self.users_data = self._load_users()
    
    def _load_users(self) -> Dict[str, Dict[str, Any]]:
        """
        Carica gli utenti dal file JSON
        
        Returns:
            Dizionario {username: {password, display_name, role}}
        """
        if not self.users_file.exists():
            # Crea un file di default se non esiste
            default_users = {
                "demo": {
                    "password": "demo123",
                    "display_name": "Utente Demo",
                    "role": "student"
                },
                "admin": {
                    "password": "admin123",
                    "display_name": "Amministratore",
                    "role": "admin"
                }
            }
            self._save_users(default_users)
            return default_users
        
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _save_users(self, users_data: Dict[str, Dict[str, Any]]):
        """Salva gli utenti nel file JSON"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Autentica un utente
        
        Args:
            username: nome utente
            password: password in chiaro
            
        Returns:
            Oggetto User se autenticazione riuscita, None altrimenti
        """
        if username not in self.users_data:
            return None
        
        user_info = self.users_data[username]
        
        # Confronto password in chiaro (NON SICURO - solo per sviluppo)
        if user_info.get("password") != password:
            return None
        
        return User(
            username=username,
            display_name=user_info.get("display_name", username),
            role=user_info.get("role", "student")
        )
    
    def add_user(self, username: str, password: str, display_name: str, role: str = "student") -> bool:
        """
        Aggiunge un nuovo utente (solo per admin)
        
        Args:
            username: nome utente (univoco)
            password: password in chiaro
            display_name: nome da visualizzare
            role: ruolo dell'utente
            
        Returns:
            True se l'utente è stato aggiunto, False se già esistente
        """
        if username in self.users_data:
            return False
        
        self.users_data[username] = {
            "password": password,
            "display_name": display_name,
            "role": role
        }
        self._save_users(self.users_data)
        return True
    
    def get_all_users(self) -> Dict[str, Dict[str, Any]]:
        """
        Restituisce tutti gli utenti (senza password)
        
        Returns:
            Dizionario con info utenti (esclusa password)
        """
        users_safe = {}
        for username, info in self.users_data.items():
            users_safe[username] = {
                "display_name": info.get("display_name", username),
                "role": info.get("role", "student")
            }
        return users_safe


def get_auth_manager() -> AuthManager:
    """
    Factory function per ottenere un'istanza di AuthManager
    Utile per dependency injection
    """
    return AuthManager()


# Helper per gestire la sessione in Streamlit
def init_session_auth(st_session_state):
    """
    Inizializza le variabili di sessione per l'autenticazione
    
    Args:
        st_session_state: oggetto session_state di Streamlit
    """
    if "authenticated" not in st_session_state:
        st_session_state.authenticated = False
    if "user" not in st_session_state:
        st_session_state.user = None


def login_user(st_session_state, user: User):
    """
    Imposta l'utente come autenticato nella sessione
    
    Args:
        st_session_state: oggetto session_state di Streamlit
        user: oggetto User autenticato
    """
    st_session_state.authenticated = True
    st_session_state.user = user


def logout_user(st_session_state):
    """
    Effettua il logout dell'utente
    
    Args:
        st_session_state: oggetto session_state di Streamlit
    """
    st_session_state.authenticated = False
    st_session_state.user = None


def get_current_user(st_session_state) -> Optional[User]:
    """
    Restituisce l'utente corrente dalla sessione
    
    Args:
        st_session_state: oggetto session_state di Streamlit
        
    Returns:
        Oggetto User o None se non autenticato
    """
    return st_session_state.get("user")


def is_authenticated(st_session_state) -> bool:
    """
    Verifica se c'è un utente autenticato
    
    Args:
        st_session_state: oggetto session_state di Streamlit
        
    Returns:
        True se autenticato
    """
    return st_session_state.get("authenticated", False)
