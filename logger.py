"""
Modulo per il logging delle risposte degli utenti.
Gestisce:
- Salvataggio di ogni interazione utente-quiz
- Persistenza su file JSON (predisposto per DB)
- Query sui dati storici

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
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


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
    Salva in formato JSON, facilmente migrabile a database.
    """
    
    def __init__(self, log_file: str = "quiz_logs.json"):
        """
        Inizializza il logger
        
        Args:
            log_file: percorso al file JSON per i log
        """
        self.log_file = Path(log_file)
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Crea il file di log se non esiste"""
        if not self.log_file.exists():
            self._save_logs([])
    
    def _load_logs(self) -> List[Dict[str, Any]]:
        """
        Carica tutti i log dal file
        
        Returns:
            Lista di log entries
        """
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def _save_logs(self, logs: List[Dict[str, Any]]):
        """
        Salva i log nel file
        
        Args:
            logs: lista di log entries
        """
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    
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
        
        logs = self._load_logs()
        logs.append(asdict(entry))
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
