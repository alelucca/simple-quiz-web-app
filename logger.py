"""
Modulo per il logging delle risposte degli utenti.
Gestisce:
- Salvataggio di ogni interazione utente-quiz su Google Sheets
- Persistenza su foglio Google (log_streamlit) con due fogli separati
- Query sui dati storici
- Conversione automatica CSV->JSON per compatibilità

Struttura log:
{
    "timestamp": "2025-12-23T10:30:00",
    "username": "demo",
    "quiz_mode": "single_question|complete|exam",
    "module_name": "farmacologia",
    "question_id": 1,
    "user_answer": "...",
    "correct_answer": "...",
    "is_correct": true,
    "attempt_number": 1
}
"""

import json
import csv
import io
import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

# Google Sheets imports (usando connettore ufficiale Streamlit)
try:
    from streamlit_gsheets import GSheetsConnection
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False


@dataclass
class QuizLogEntry:
    """Singola entry nel log delle risposte"""
    timestamp: str
    username: str
    quiz_mode: str  # "single_question", "complete", "exam"
    module_name: str
    question_id: int
    user_answer: str
    correct_answer: str
    is_correct: bool
    attempt_number: int = 1
    session_id: Optional[str] = None  # Per raggruppare risposte della stessa sessione


class QuizLogger:
    """
    Gestisce il logging delle risposte degli utenti.
    Salva su Google Sheets (con fallback a JSON locale).
    """
    
    def __init__(self, spreadsheet_name="log_streamlit", log_file: str = "quiz_logs.json", use_google_sheets: bool = True):
        """
        Inizializza il logger
        
        Args:
            log_file: percorso al file JSON per fallback
            use_google_sheets: se True, usa Google Sheets
        """
        self.log_file = Path(log_file)
        self.use_google_sheets = use_google_sheets and GSHEETS_AVAILABLE
        self.spreadsheet_name=spreadsheet_name
        self.conn = None
        
        if self.use_google_sheets:
            self._init_google_sheets()
        else:
            self._ensure_log_file()
    
    def _init_google_sheets(self):
        """Inizializza la connessione a Google Sheets usando il connettore ufficiale Streamlit"""
        try:
            # Usa il connettore ufficiale Streamlit
            self.conn = st.connection("gsheets", type=GSheetsConnection)
            
            # Verifica che la connessione funzioni leggendo i fogli esistenti
            # try:
            #     # Prova a leggere il foglio answers
            #     df = self.conn.read(worksheet="answers", ttl=0)
            # except Exception:
            #     # Se non esiste, lo creeremo al primo salvataggio
            #     pass
                
        except Exception as e:
            print(f"Errore inizializzazione Google Sheets: {e}")
            self.use_google_sheets = False
            self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Crea il file di log se non esiste"""
        if not self.log_file.exists():
            self._save_logs([])
    
    def _load_logs_from_sheets(self) -> List[Dict[str, Any]]:
        """
        Carica tutti i log da Google Sheets e converte in formato JSON
        
        Returns:
            Lista di log entries
        """
        if not self.use_google_sheets or not self.conn:
            return []
        
        try:
            # Leggi il foglio answers
            df = self.conn.read(worksheet="answers", ttl=0)
            
            if df.empty:
                return []
            
            # Converti DataFrame in lista di dizionari
            logs = df.to_dict('records')
            
            # Converti tipi di dati
            for record in logs:
                # Converti is_correct da stringa a booleano
                if 'is_correct' in record:
                    record['is_correct'] = str(record['is_correct']).lower() == 'true'
                # Converti question_id e attempt_number a int
                if 'question_id' in record:
                    try:
                        record['question_id'] = int(record['question_id'])
                    except (ValueError, TypeError):
                        record['question_id'] = 0
                if 'attempt_number' in record:
                    try:
                        record['attempt_number'] = int(record['attempt_number'])
                    except (ValueError, TypeError):
                        record['attempt_number'] = 1
            
            return logs
        except Exception as e:
            print(f"Errore caricamento da Sheets: {e}")
            return []
    
    def _load_sessions_from_sheets(self) -> List[Dict[str, Any]]:
        """
        Carica i riassunti sessioni da Google Sheets
        
        Returns:
            Lista di session entries
        """
        if not self.use_google_sheets or not self.conn:
            return []
        
        try:
            df = self.conn.read(worksheet="sessions", ttl=0)
            
            if df.empty:
                return []
            
            sessions = df.to_dict('records')
            
            for record in sessions:
                # Deserializza il JSON summary
                if 'summary_json' in record and record['summary_json']:
                    try:
                        record['summary'] = json.loads(record['summary_json'])
                    except json.JSONDecodeError:
                        record['summary'] = {}
            
            return sessions
        except Exception as e:
            print(f"Errore caricamento sessioni da Sheets: {e}")
            return []
    
    def _load_logs(self) -> List[Dict[str, Any]]:
        """
        Carica tutti i log (da Sheets o file)
        
        Returns:
            Lista di log entries
        """
        if self.use_google_sheets:
            # Combina logs da answers e sessions
            answers = self._load_logs_from_sheets()
            sessions = self._load_sessions_from_sheets()
            return answers + sessions
        else:
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
    
    def _save_logs(self, logs: List[Dict[str, Any]]):
        """
        Salva i log nel file (fallback)
        
        Args:
            logs: lista di log entries
        """
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    
    def _save_to_sheets(self, entry: Dict[str, Any], is_session: bool = False):
        """
        Salva una entry su Google Sheets usando il connettore Streamlit
        
        Args:
            entry: dizionario con i dati
            is_session: True se è un session summary, False se è una risposta
        """
        if not self.use_google_sheets or not self.conn:
            return
        
        try:
            worksheet_name = "sessions" if is_session else "answers"
            
            # Crea DataFrame da una singola riga
            if is_session:
                data = {
                    'timestamp': [entry.get('timestamp', '')],
                    'username': [entry.get('username', '')],
                    'quiz_mode': [entry.get('quiz_mode', '')],
                    'session_id': [entry.get('session_id', '')],
                    'type': [entry.get('type', 'session_summary')],
                    'summary_json': [json.dumps(entry.get('summary', {}), ensure_ascii=False)]
                }
            else:
                data = {
                    'timestamp': [entry.get('timestamp', '')],
                    'username': [entry.get('username', '')],
                    'quiz_mode': [entry.get('quiz_mode', '')],
                    'module_name': [entry.get('module_name', '')],
                    'question_id': [entry.get('question_id', 0)],
                    'user_answer': [entry.get('user_answer', '')],
                    'correct_answer': [entry.get('correct_answer', '')],
                    'is_correct': [str(entry.get('is_correct', False))],
                    'attempt_number': [entry.get('attempt_number', 1)],
                    'session_id': [entry.get('session_id', '')]
                }
            
            df_new = pd.DataFrame(data)
            
            # Append diretto senza leggere i dati esistenti (molto più veloce)
            try:                
                # Se arriviamo qui, il foglio esiste - usa append
                print("Saving with append mode")
                self.conn.update(
                    spreadsheet=self.spreadsheet_name,
                    worksheet=worksheet_name,
                    data=df_new,
                    # Append mode - aggiunge alla fine senza leggere tutto
                )
            except Exception as e:
                print(f"Direct append failed: {str(e)}")
            
        except Exception as e:
            print(f"Errore salvataggio su Sheets, fallback a JSON locale: {e}")
            # Fallback a file JSON
            logs = self._load_logs()
            logs.append(entry)
            self._save_logs(logs)
    
    def log_answer(
        self,
        username: str,
        quiz_mode: str,
        module_name: str,
        question_id: int,
        user_answer: str,
        correct_answer: str,
        is_correct: bool,
        attempt_number: int = 1,
        session_id: Optional[str] = None
    ):
        """
        Registra una risposta utente
        
        Args:
            username: nome utente che ha risposto
            quiz_mode: modalità quiz ("single_question", "complete", "exam")
            module_name: nome del modulo
            question_id: ID della domanda
            user_answer: risposta data dall'utente
            correct_answer: risposta corretta
            is_correct: se la risposta è corretta
            attempt_number: numero del tentativo (per modalità single_question)
            session_id: ID univoco della sessione di quiz
        """
        entry = QuizLogEntry(
            timestamp=datetime.now().isoformat(),
            username=username,
            quiz_mode=quiz_mode,
            module_name=module_name,
            question_id=question_id,
            user_answer=user_answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
            attempt_number=attempt_number,
            session_id=session_id
        )
        
        entry_dict = asdict(entry)
        
        if self.use_google_sheets:
            self._save_to_sheets(entry_dict, is_session=False)
        else:
            logs = self._load_logs()
            logs.append(entry_dict)
            self._save_logs(logs)
    
    def log_session_summary(
        self,
        username: str,
        quiz_mode: str,
        session_id: str,
        summary_data: Dict[str, Any]
    ):
        """
        Registra un riassunto di sessione
        
        Args:
            username: nome utente
            quiz_mode: modalità quiz
            session_id: ID della sessione
            summary_data: dati di riepilogo (score, tempo, ecc.)
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "quiz_mode": quiz_mode,
            "session_id": session_id,
            "type": "session_summary",
            "summary": summary_data
        }
        
        if self.use_google_sheets:
            self._save_to_sheets(entry, is_session=True)
        else:
            logs = self._load_logs()
            logs.append(entry)
            self._save_logs(logs)
    
    def get_user_history(self, username: str) -> List[Dict[str, Any]]:
        """
        Recupera lo storico di un utente
        
        Args:
            username: nome utente
            
        Returns:
            Lista di log entries dell'utente
        """
        if self.use_google_sheets and self.conn:
            try:
                # Query diretta sul foglio answers
                query = f'SELECT * WHERE B = "{username}"'  # Colonna B = username
                df_answers = self.conn.query(worksheet="answers", sql=query, ttl=0)
                
                # Query diretta sul foglio sessions
                df_sessions = self.conn.query(worksheet="sessions", sql=query, ttl=0)
                
                # Combina i risultati
                logs = []
                if not df_answers.empty:
                    logs.extend(df_answers.to_dict('records'))
                if not df_sessions.empty:
                    sessions = df_sessions.to_dict('records')
                    # Deserializza summary_json per sessions
                    for record in sessions:
                        if 'summary_json' in record and record['summary_json']:
                            try:
                                record['summary'] = json.loads(record['summary_json'])
                            except json.JSONDecodeError:
                                record['summary'] = {}
                    logs.extend(sessions)
                
                return logs
            except Exception as e:
                print(f"Errore query Google Sheets: {e}")
                # Fallback al metodo tradizionale
                logs = self._load_logs()
                return [log for log in logs if log.get("username") == username]
        else:
            logs = self._load_logs()
            return [log for log in logs if log.get("username") == username]
    
    def get_question_stats(self, module_name: str, question_id: int) -> Dict[str, Any]:
        """
        Calcola statistiche per una domanda specifica
        
        Args:
            module_name: nome del modulo
            question_id: ID della domanda
            
        Returns:
            Dizionario con statistiche (total_attempts, correct_rate, ecc.)
        """
        if self.use_google_sheets and self.conn:
            try:
                # Query diretta: filtra per module_name e question_id
                # Colonna D = module_name, Colonna E = question_id
                query = f'SELECT * WHERE D = "{module_name}" AND E = {question_id}'
                df = self.conn.query(worksheet="answers", sql=query, ttl=0)
                
                if df.empty:
                    return {
                        "total_attempts": 0,
                        "correct_attempts": 0,
                        "correct_rate": 0.0
                    }
                
                question_logs = df.to_dict('records')
                total = len(question_logs)
                correct = sum(1 for log in question_logs if str(log.get("is_correct", "false")).lower() == "true")
                unique_users = df['username'].nunique() if 'username' in df.columns else 0
                
                return {
                    "total_attempts": total,
                    "correct_attempts": correct,
                    "correct_rate": (correct / total * 100) if total > 0 else 0.0,
                    "unique_users": unique_users
                }
            except Exception as e:
                print(f"Errore query Google Sheets: {e}")
                # Fallback
                pass
        
        # Fallback al metodo tradizionale
        logs = self._load_logs()
        
        question_logs = [
            log for log in logs
            if log.get("module_name") == module_name and
               log.get("question_id") == question_id and
               log.get("type") != "session_summary"
        ]
        
        if not question_logs:
            return {
                "total_attempts": 0,
                "correct_attempts": 0,
                "correct_rate": 0.0
            }
        
        total = len(question_logs)
        correct = sum(1 for log in question_logs if log.get("is_correct", False))
        
        return {
            "total_attempts": total,
            "correct_attempts": correct,
            "correct_rate": (correct / total * 100) if total > 0 else 0.0,
            "unique_users": len(set(log.get("username") for log in question_logs))
        }
    
    def get_module_stats(self, module_name: str) -> Dict[str, Any]:
        """
        Calcola statistiche per un intero modulo
        
        Args:
            module_name: nome del modulo
            
        Returns:
            Dizionario con statistiche aggregate
        """
        if self.use_google_sheets and self.conn:
            try:
                # Query diretta: filtra per module_name (Colonna D)
                query = f'SELECT * WHERE D = "{module_name}"'
                df = self.conn.query(worksheet="answers", sql=query, ttl=0)
                
                if df.empty:
                    return {
                        "total_attempts": 0,
                        "correct_rate": 0.0,
                        "unique_users": 0
                    }
                
                module_logs = df.to_dict('records')
                total = len(module_logs)
                correct = sum(1 for log in module_logs if str(log.get("is_correct", "false")).lower() == "true")
                unique_users = df['username'].nunique() if 'username' in df.columns else 0
                
                return {
                    "total_attempts": total,
                    "correct_attempts": correct,
                    "correct_rate": (correct / total * 100) if total > 0 else 0.0,
                    "unique_users": unique_users
                }
            except Exception as e:
                print(f"Errore query Google Sheets: {e}")
                # Fallback
                pass
        
        # Fallback al metodo tradizionale
        logs = self._load_logs()
        
        module_logs = [
            log for log in logs
            if log.get("module_name") == module_name and
               log.get("type") != "session_summary"
        ]
        
        if not module_logs:
            return {
                "total_attempts": 0,
                "correct_rate": 0.0,
                "unique_users": 0
            }
        
        total = len(module_logs)
        correct = sum(1 for log in module_logs if log.get("is_correct", False))
        unique_users = len(set(log.get("username") for log in module_logs))
        
        return {
            "total_attempts": total,
            "correct_attempts": correct,
            "correct_rate": (correct / total * 100) if total > 0 else 0.0,
            "unique_users": unique_users
        }
    
    def get_user_stats(self, username: str) -> Dict[str, Any]:
        """
        Calcola statistiche per un utente
        
        Args:
            username: nome utente
            
        Returns:
            Dizionario con statistiche utente
        """
        logs = self.get_user_history(username)
        
        answer_logs = [log for log in logs if log.get("type") != "session_summary"]
        
        if not answer_logs:
            return {
                "total_questions_answered": 0,
                "correct_rate": 0.0,
                "modules_practiced": [],
                "modules_stats": {}
            }
        
        total = sum(1 for log in answer_logs if log.get("user_answer", "")!="(Non hai risposto)")
        correct = sum(1 for log in answer_logs if log.get("is_correct", False))
        modules = list(set(log.get("module_name") for log in answer_logs if log.get("module_name")))
        
        # Statistiche per modulo
        modules_stats = {}
        for module in modules:
            module_logs = [log for log in answer_logs if log.get("module_name") == module]
            module_total = sum(1 for log in answer_logs if log.get("user_answer", "")!="(Non hai risposto)")
            module_correct = sum(1 for log in module_logs if log.get("is_correct", False))
            
            modules_stats[module] = {
                "total_questions": module_total,
                "correct_answers": module_correct,
                "correct_rate": (module_correct / module_total * 100) if module_total > 0 else 0.0
            }
        
        return {
            "total_questions_answered": total,
            "correct_answers": correct,
            "correct_rate": (correct / total * 100) if total > 0 else 0.0,
            "modules_practiced": modules,
            "modules_stats": modules_stats
        }


def get_quiz_logger() -> QuizLogger:
    """
    Factory function per ottenere un'istanza di QuizLogger
    """
    return QuizLogger()


# Helper per generare session ID univoci
def generate_session_id() -> str:
    """
    Genera un ID univoco per la sessione
    
    Returns:
        Stringa con timestamp e random component
    """
    from datetime import datetime
    import random
    import string
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{timestamp}_{random_str}"
