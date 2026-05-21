"""
Modulo per l'autenticazione degli utenti.
Gestisce:
- Accesso con password di sistema configurata nei secrets
- Sessione utente
- Persistenza dei login riusciti su Google Sheets
"""

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection


@st.cache_resource
def get_gsheets_connection() -> GSheetsConnection:
    """Restituisce la connessione Google Sheets cached."""
    return st.connection("gsheets", type=GSheetsConnection)


@dataclass
class User:
    """Rappresenta un utente autenticato"""
    username: str
    display_name: str

class AuthManager:
    """
    Gestisce l'autenticazione degli utenti.
    L'accesso avviene con una password di sistema letta dai secrets.
    """
    
    def __init__(self):
        """Inizializza il gestore autenticazione"""
        self.worksheet_name = self._get_login_worksheet_name()

    @staticmethod
    def _get_auth_settings() -> Dict[str, Any]:
        """Recupera la configurazione auth dai secrets con fallback compatibili."""
        settings = st.secrets.get("auth", {})
        if not isinstance(settings, dict):
            settings = {}
        return settings

    def _get_login_worksheet_name(self) -> str:
        settings = self._get_auth_settings()
        return settings.get("login_worksheet_name", "users_pswd")

    def _get_system_password(self) -> Optional[str]:
        settings = self._get_auth_settings()
        system_password = settings.get("system_password") or st.secrets.get("system_password")
        if not system_password:
            return None
        return str(system_password)
    
    @staticmethod
    def _validate_username(username: str) -> Tuple[bool, str]:
        """
        Valida username con la sola regola richiesta: lunghezza maggiore di 2.
        
        Args:
            username: username da validare
            
        Returns:
            Tupla (valid, error_message)
        """
        if not username:
            return False, "Lo username deve avere lunghezza maggiore"
        
        if len(username.strip()) <= 2:
            return False, "Lo username deve avere lunghezza maggiore"
        
        return True, ""
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Restituisce un hash stabile della password per il log."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()
    
    @staticmethod
    def _password_matches(password: str, system_password: str) -> bool:
        """Confronta la password usando un confronto costante."""
        return hmac.compare_digest(password, system_password)
    
    def _get_connection(self):
        """
        Ottiene la connessione a Google Sheets
        
        Returns:
            Connessione a Google Sheets
        """
        return get_gsheets_connection()
    
    def _read_login_sheet(self) -> pd.DataFrame:
        """Legge il foglio dei login senza mutarlo."""
        conn = self._get_connection()
        try:
            df = conn.read(worksheet=self.worksheet_name, ttl=0)
        except Exception:
            df = pd.DataFrame()

        if df is None or df.empty:
            return pd.DataFrame(columns=["username", "password_hash", "last_login_at"])

        normalized = df.copy()
        for column in ["username", "password_hash", "last_login_at"]:
            if column not in normalized.columns:
                normalized[column] = ""
        return normalized

    def _save_login_to_sheet(self, username: str, password_hash: str) -> bool:
        """
        Salva o aggiorna un login riuscito in Google Sheets.

        Assunzione: non possono esistere utenti distinti con lo stesso username.
        
        Args:
            username: nome utente
            password_hash: password hashata
            
        Returns:
            True se salvato correttamente
        """
        try:
            conn = self._get_connection()
            existing_df = self._read_login_sheet()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if not existing_df.empty and "username" in existing_df.columns:
                username_matches = existing_df[existing_df["username"].astype(str) == username]
            else:
                username_matches = pd.DataFrame()

            if username_matches.empty:
                # Assunzione: usernames unici, quindi una sola riga per username.
                updated_df = pd.concat(
                    [
                        existing_df,
                        pd.DataFrame(
                            [{
                                "username": username,
                                "password_hash": password_hash,
                                "last_login_at": timestamp,
                            }]
                        ),
                    ],
                    ignore_index=True,
                )
            else:
                updated_df = existing_df.copy()
                updated_df.loc[updated_df["username"].astype(str) == username, "last_login_at"] = timestamp

            try:
                conn.update(worksheet=self.worksheet_name, data=updated_df)
            except Exception as update_err:
                import gspread
                if isinstance(update_err, gspread.exceptions.WorksheetNotFound) or "WorksheetNotFound" in str(type(update_err)):
                    conn.create(worksheet=self.worksheet_name, data=updated_df)
                else:
                    raise
            return True
        except Exception as e:
            st.error(f"Errore salvataggio login su Google Sheets: {str(e)}")
            return False
    
    def authenticate(self, username: str, password: str) -> Tuple[Optional[User], str]:
        """
        Autentica un utente tramite password di sistema.
        
        Args:
            username: nome utente
            password: password inserita dall'utente
            
        Returns:
            Tupla (user, error_message). Se l'accesso fallisce, user è None.
        """
        valid, error = self._validate_username(username)
        if not valid:
            return None, error

        system_password = self._get_system_password()
        if not system_password:
            return None, "Password di sistema non configurata. Contatta l'amministratore."

        if not self._password_matches(password, system_password):
            return None, "Password del sistema errata"

        password_hash = self._hash_password(system_password)
        if not self._save_login_to_sheet(username.strip(), password_hash):
            st.warning("Accesso consentito, ma il salvataggio su Google Sheets non è riuscito.")

        return User(username=username.strip(), display_name=username.strip()), ""

    # ------------------------------------------------------------------
    # Funzionalità precedentemente presenti ma ora disattivate.
    # - registrazione utenti
    # - creazione credenziali personalizzate
    # - validazione credenziali tramite Google Sheets
    # - qualsiasi logica legata a signup/account management
    # ------------------------------------------------------------------


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
