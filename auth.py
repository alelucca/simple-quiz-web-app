"""
Modulo per l'autenticazione degli utenti.
Gestisce:
- Registrazione con username e password
- Login con credenziali hashate (bcrypt)
- Salvataggio utenti in Google Sheets
- Sessione utente
- Validazione input per prevenire SQL injection
"""

import json
import re
import bcrypt
import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from streamlit_gsheets import GSheetsConnection


@dataclass
class User:
    """Rappresenta un utente autenticato"""
    username: str
    display_name: str

class AuthManager:
    """
    Gestisce l'autenticazione degli utenti.
    Le credenziali sono salvate in Google Sheets con password hashate.
    """
    
    def __init__(self):
        """Inizializza il gestore autenticazione"""
        self.worksheet_name = "users"
    
    @staticmethod
    def _validate_username(username: str) -> Tuple[bool, str]:
        """
        Valida username per prevenire SQL injection e garantire formato corretto
        
        Args:
            username: username da validare
            
        Returns:
            Tupla (valid, error_message)
        """
        if not username:
            return False, "Username non può essere vuoto"
        
        if len(username) < 3:
            return False, "Username deve essere almeno 3 caratteri"
        
        if len(username) > 50:
            return False, "Username troppo lungo (max 50 caratteri)"
        
        # Solo lettere, numeri, underscore, trattino
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Username può contenere solo lettere, numeri, underscore e trattino"
        
        return True, ""
    
    @staticmethod
    def _validate_password(password: str) -> Tuple[bool, str]:
        """
        Valida password
        
        Args:
            password: password da validare
            
        Returns:
            Tupla (valid, error_message)
        """
        if not password:
            return False, "Password non può essere vuota"
        
        if len(password) < 6:
            return False, "Password deve essere almeno 6 caratteri"
        
        if len(password) > 30:
            return False, "Password troppo lunga (max 30 caratteri)"
        
        return True, ""
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """
        Hash della password usando bcrypt
        
        Args:
            password: password in chiaro
            
        Returns:
            Password hashata come stringa
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def _verify_password(password: str, hashed: str) -> bool:
        """
        Verifica password contro hash
        
        Args:
            password: password in chiaro
            hashed: password hashata
            
        Returns:
            True se corrispondono
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def _get_connection(self):
        """
        Ottiene la connessione a Google Sheets
        
        Returns:
            Connessione a Google Sheets
        """
        return st.connection("gsheets", type=GSheetsConnection)
    
    def _get_users_from_sheet(self) -> Dict[str, Dict[str, Any]]:
        """
        Carica utenti da Google Sheets
        
        Returns:
            Dizionario {username: {password_hash, display_name}}
        """
        try:
            conn = self._get_connection()
            df = conn.read(worksheet=self.worksheet_name, ttl=0)
            
            if df.empty:
                return {}
            
            users = {}
            for _, row in df.iterrows():
                username = row.get('username', '')
                if username:
                    users[username] = {
                        'password_hash': row.get('password_hash', ''),
                        'display_name': row.get('display_name', username)
                    }
            return users
        except Exception as e:
            st.error(f"Errore caricamento utenti da Google Sheets: {str(e)}")
            return {}
    
    def get_user(self, username: str) -> Dict[str, Dict[str, Any]] | None:
        """Ottiene un singolo utente dal foglio Google Sheets usando query SQL"""
        # Valida username per prevenire SQL injection
        valid, error = self._validate_username(username)
        if not valid:
            st.error(f"Username non valido: {error}")
            return None
        
        try:
            conn = self._get_connection()
            query = f"""SELECT username, password_hash, display_name FROM {self.worksheet_name} WHERE username='{username}'"""
            df = conn.query(sql=query, worksheet=self.worksheet_name, ttl=0)
            
            if df.empty:
                return None
            
            row = df.iloc[0]
            return {
                username: {
                    'password_hash': row.get('password_hash', ''),
                    'display_name': row.get('display_name', username)
                }
            }
        except Exception as e:
            st.error(f"Errore caricamento utente da Google Sheets: {str(e)}")
            return None
    
    def _save_user_to_sheet(self, username: str, password_hash: str, display_name: str) -> bool:
        """
        Salva un nuovo utente in Google Sheets
        
        Args:
            username: nome utente
            password_hash: password hashata
            display_name: nome visualizzato
            
        Returns:
            True se salvato correttamente
        """
        try:
            conn = self._get_connection()
            registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Crea un dataframe con il nuovo utente e usa update in modalità append
            new_row = pd.DataFrame([{
                'username': username,
                'password_hash': password_hash,
                'display_name': display_name,
                'registration_date': registration_date
            }])
            
            # Leggi i dati esistenti e appendi
            existing_df = conn.read(worksheet=self.worksheet_name, ttl=0)
            if existing_df.empty:
                updated_df = new_row
            else:
                updated_df = pd.concat([existing_df, new_row], ignore_index=True)
            
            conn.update(worksheet=self.worksheet_name, data=updated_df)
            return True
        except Exception as e:
            st.error(f"Errore salvataggio utente: {str(e)}")
            return False
    
    def register_user(self, username: str, password: str, display_name: str = "") -> Tuple[bool, str]:
        """
        Registra un nuovo utente
        
        Args:
            username: nome utente
            password: password in chiaro
            display_name: nome da visualizzare (opzionale)
            
        Returns:
            Tupla (success, message)
        """
        # Valida username
        valid, error = self._validate_username(username)
        if not valid:
            return False, error
        
        # Valida password
        valid, error = self._validate_password(password)
        if not valid:
            return False, error
        
        # Verifica se utente già esistente usando query
        existing_user = self.get_user(username)
        if existing_user is not None:
            return False, "Username già esistente"
        
        # Hash password
        password_hash = self._hash_password(password)
        
        # Usa username come display_name se non fornito
        if not display_name:
            display_name = username
        
        # Salva in Google Sheets
        try:
            if self._save_user_to_sheet(username, password_hash, display_name):
                return True, "Registrazione completata con successo!"
            else:
                return False, "Errore durante il salvataggio"
        except Exception as e:
            return False, f"Errore durante il salvataggio: {str(e)}"
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Autentica un utente
        
        Args:
            username: nome utente
            password: password in chiaro
            
        Returns:
            Oggetto User se autenticazione riuscita, None altrimenti
        """
        user_data = self.get_user(username=username)
        
        if user_data is None or username not in user_data:
            return None
        
        user_info = user_data[username]
        
        # Verifica password hashata
        if not self._verify_password(password, user_info['password_hash']):
            return None
        
        return User(
            username=username,
            display_name=user_info.get('display_name', username)
        )
    
    def get_all_users(self) -> Dict[str, Dict[str, Any]]:
        """
        Restituisce tutti gli utenti (senza password) usando query SQL
        
        Returns:
            Dizionario con info utenti (esclusa password)
        """
        try:
            conn = self._get_connection()
            query = f"""SELECT username, display_name FROM {self.worksheet_name}"""
            df = conn.query(sql=query, worksheet=self.worksheet_name, ttl=0)
            
            users_safe = {}
            for _, row in df.iterrows():
                username = row.get('username', '')
                if username:
                    users_safe[username] = {
                        "display_name": row.get("display_name", username)
                    }
            return users_safe
        except Exception as e:
            st.error(f"Errore caricamento utenti: {str(e)}")
            return {}


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
