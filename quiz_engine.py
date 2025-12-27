"""
Engine per la gestione del quiz in modalità "domanda per domanda".
Gestisce:
- Selezione casuale domande senza ripetizioni
- Validazione risposte
- Tracking tentativi per domanda
- Calcolo statistiche finali
"""

import random
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class QuestionStatus(Enum):
    """Stati possibili per una domanda"""
    NOT_ANSWERED = "not_answered"
    CORRECT = "correct"
    SKIPPED = "skipped"
    SHOWN = "shown"  # Risposta mostrata dall'utente


@dataclass
class QuestionAttempt:
    """Rappresenta i tentativi su una singola domanda"""
    question_id: int
    num_attempts: int = 0
    status: QuestionStatus = QuestionStatus.NOT_ANSWERED
    correct_at_attempt: Optional[int] = None  # A quale tentativo è stata risposta correttamente
    
    def is_completed(self) -> bool:
        """Verifica se la domanda è completata (corretta, saltata o risposta mostrata)"""
        return self.status in [QuestionStatus.CORRECT, QuestionStatus.SKIPPED, QuestionStatus.SHOWN]


@dataclass
class QuizStats:
    """Statistiche finali del quiz"""
    total_questions: int
    total_attempted: int = 0    
    correct_first_try: int = 0
    correct_second_try: int = 0
    correct_third_try: int = 0
    correct_fourth_try: int = 0
    correct_more_tries: int = 0
    skipped: int = 0
    shown: int = 0
    
    def get_total_correct(self) -> int:
        """Totale risposte corrette"""
        return (self.correct_first_try + self.correct_second_try + 
                self.correct_third_try + self.correct_fourth_try + 
                self.correct_more_tries)


class SingleQuestionQuizEngine:
    """
    Engine per quiz in modalità domanda-per-domanda.
    Ogni istanza gestisce una sessione di quiz.
    """
    
    def __init__(self, questions: List[Dict[str, Any]]):
        """
        Inizializza il quiz engine
        
        Args:
            questions: lista di domande caricate dal QuizLoader
        """
        if not questions:
            raise ValueError("Cannot initialize quiz with empty questions list")
        
        self.questions = questions.copy()
        self.total_questions = len(questions)
        
        # Pool di domande non ancora mostrate
        self.remaining_questions = list(range(len(questions)))
        random.shuffle(self.remaining_questions)
        
        # Tracking dei tentativi per ogni domanda
        self.attempts: Dict[int, QuestionAttempt] = {}
        
        # Indice della domanda corrente
        self.current_question_idx: Optional[int] = None
        
    def get_next_question(self) -> Optional[Dict[str, Any]]:
        """
        Estrae la prossima domanda casuale dal pool
        
        Returns:
            Dizionario con la domanda e un ID unico, oppure None se non ci sono più domande
        """
        if not self.remaining_questions:
            return None
        
        # Prende la prossima domanda dalla lista shuffled
        self.current_question_idx = self.remaining_questions.pop(0)
        
        # Inizializza il tracking se non esiste
        if self.current_question_idx not in self.attempts:
            self.attempts[self.current_question_idx] = QuestionAttempt(
                question_id=self.current_question_idx
            )
        
        question_data = self.questions[self.current_question_idx].copy()
        # Usa cod_domanda esistente nel JSON, se non presente usa l'indice come fallback
        if "cod_domanda" not in question_data:
            question_data["cod_domanda"] = self.current_question_idx
        
        return question_data
    
    def check_answer(self, answer: str) -> Tuple[bool, str]:
        """
        Verifica se la risposta è corretta
        
        Args:
            answer: risposta fornita dall'utente
            
        Returns:
            Tupla (is_correct, correct_answer)
        """
        if self.current_question_idx is None:
            raise ValueError("No active question")
        
        question = self.questions[self.current_question_idx]
        attempt = self.attempts[self.current_question_idx]
        
        # Incrementa tentativi
        attempt.num_attempts += 1
        
        # Verifica correttezza (case-insensitive, strip whitespace)
        is_correct = answer.strip().lower() == question["risposta_corretta"].strip().lower()
        
        if is_correct:
            attempt.status = QuestionStatus.CORRECT
            attempt.correct_at_attempt = attempt.num_attempts
        
        return is_correct, question["risposta_corretta"]
    
    def skip_question(self):
        """Marca la domanda corrente come saltata"""
        if self.current_question_idx is None:
            raise ValueError("No active question")
        
        attempt = self.attempts[self.current_question_idx]
        attempt.status = QuestionStatus.SKIPPED
    
    def show_answer(self) -> str:
        """
        Mostra la risposta corretta senza incrementare i tentativi
        
        Returns:
            La risposta corretta
        """
        if self.current_question_idx is None:
            raise ValueError("No active question")
        
        attempt = self.attempts[self.current_question_idx]
        attempt.status = QuestionStatus.SHOWN
        
        return self.questions[self.current_question_idx]["risposta_corretta"]
    
    def is_current_question_completed(self) -> bool:
        """Verifica se la domanda corrente è stata completata"""
        if self.current_question_idx is None:
            return False
        
        return self.attempts[self.current_question_idx].is_completed()
    
    def get_remaining_count(self) -> int:
        """Numero di domande rimanenti non ancora mostrate"""
        return len(self.remaining_questions)
    
    def get_stats(self) -> QuizStats:
        """
        Calcola le statistiche finali del quiz
        
        Returns:
            Oggetto QuizStats con le statistiche
        """
        stats = QuizStats(total_questions=self.total_questions)
        
        for attempt in self.attempts.values():
            if attempt.status == QuestionStatus.CORRECT:
                if attempt.correct_at_attempt == 1:
                    stats.correct_first_try += 1
                elif attempt.correct_at_attempt == 2:
                    stats.correct_second_try += 1
                elif attempt.correct_at_attempt == 3:
                    stats.correct_third_try += 1
                elif attempt.correct_at_attempt == 4:
                    stats.correct_fourth_try += 1
                else:
                    stats.correct_more_tries += 1
                stats.total_attempted+=1
            elif attempt.status == QuestionStatus.SKIPPED:
                stats.skipped += 1
                stats.total_attempted+=1
            elif attempt.status == QuestionStatus.SHOWN:
                stats.shown += 1
                stats.total_attempted+=1
        
        return stats
    
    def reset(self):
        """Resetta il quiz per ricominciare da capo"""
        self.remaining_questions = list(range(len(self.questions)))
        random.shuffle(self.remaining_questions)
        self.attempts = {}
        self.current_question_idx = None
