"""
Engine per la gestione del quiz in modalità "quiz completo".
Gestisce:
- Presentazione di tutte le domande in sequenza
- Salvataggio risposte in memoria
- Valutazione finale
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class CompleteQuizResult:
    """Risultato della valutazione del quiz completo"""
    total_questions: int
    correct_answers: int
    wrong_answers: int
    score_percentage: float
    question_results: List[Dict[str, Any]]  # Dettaglio per ogni domanda


class CompleteQuizEngine:
    """
    Engine per quiz in modalità completa (tutte le domande insieme).
    Simile a MS Forms.
    """
    
    def __init__(self, questions: List[Dict[str, Any]]):
        """
        Inizializza il quiz completo
        
        Args:
            questions: lista di domande di un singolo quiz (non mischiato)
        """
        if not questions:
            raise ValueError("Cannot initialize quiz with empty questions list")
        
        self.questions = questions.copy()
        self.total_questions = len(questions)
        
        # Dizionario per salvare le risposte dell'utente
        # Key: indice domanda, Value: risposta selezionata
        self.user_answers: Dict[int, str] = {}
        
    def get_all_questions(self) -> List[Dict[str, Any]]:
        """
        Restituisce tutte le domande
        
        Returns:
            Lista di domande
        """
        
        return self.questions
    
    def save_answer(self, cod_domanda: str, answer: str):
        """
        Salva la risposta dell'utente per una domanda
        
        Args:
            cod_domanda: codice della domanda
            answer: risposta selezionata dall'utente
        """        
        
        self.user_answers[cod_domanda] = answer
    
    def get_saved_answer(self, cod_domanda: str) -> Optional[str]:
        """
        Recupera la risposta salvata per una domanda
        
        Args:
            cod_domanda: codice della domanda
            
        Returns:
            Risposta salvata o None se non presente
        """
        return self.user_answers.get(cod_domanda)
    
    def evaluate(self) -> CompleteQuizResult:
        """
        Valuta tutte le risposte e calcola il risultato
        
        Returns:
            Oggetto CompleteQuizResult con i risultati dettagliati
        """
        correct = 0
        wrong = 0
        question_results = []
        
        for idx, question in enumerate(self.questions):
            user_answer = self.user_answers.get(question["cod_domanda"])
            correct_answer = question["risposta_corretta"]
            
            # Confronto case-insensitive con strip (gestisce None)
            if user_answer is None or user_answer == "":
                is_correct = False
            else:
                is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
            
            if is_correct:
                correct += 1
            else:
                wrong += 1
            
            question_results.append({
                "cod_domanda": question["cod_domanda"],
                "domanda": question["domanda"],
                "user_answer": user_answer if user_answer is not None else "(Non hai risposto)",
                "correct_answer": correct_answer,
                "is_correct": is_correct
            })
        
        score_percentage = (correct / self.total_questions * 100) if self.total_questions > 0 else 0
        
        return CompleteQuizResult(
            total_questions=self.total_questions,
            correct_answers=correct,
            wrong_answers=wrong,
            score_percentage=score_percentage,
            question_results=question_results
        )
    
    def is_complete(self) -> bool:
        """
        Verifica se tutte le domande hanno una risposta
        
        Returns:
            True se tutte le domande sono state risposte
        """
        return len(self.user_answers) == self.total_questions
    
    def get_answered_count(self) -> int:
        """
        Numero di domande a cui è stata data una risposta
        
        Returns:
            Numero di risposte salvate
        """
        return len(self.user_answers)
    
    def reset(self):
        """Resetta tutte le risposte"""
        self.user_answers = {}
