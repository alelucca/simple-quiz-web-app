"""
Engine per la gestione della simulazione d'esame.
Gestisce:
- Selezione di X domande random per modulo
- Timer di X minuti per modulo
- Navigazione tra domande
- Calcolo punteggio finale
"""

import random
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ModuleResult:
    """Risultato di un singolo modulo d'esame"""
    module_name: str
    total_questions: int
    correct_answers: int
    score_percentage: float
    time_spent_seconds: int
    completed: bool


@dataclass
class ExamResult:
    """Risultato complessivo dell'esame"""
    module_results: List[ModuleResult]
    total_correct: int
    total_questions: int
    total_time_spent_seconds: int


class ExamModuleEngine:
    """
    Engine per un singolo modulo dell'esame.
    Gestisce QUESTIONS_AND_TIMES_PER_MODULE domande con timer di un minuto per domanda.
    """
    
    QUESTIONS_AND_TIMES_PER_MODULE = {
        "Farmacologia Clinica": 30,
        "Farmacologia Generale": 30,
        "Aptd": 15,
        "Radioprotezione": 15
    }
    
    def __init__(self, module_name: str, questions: List[Dict[str, Any]]):
        """
        Inizializza un modulo d'esame
        
        Args:
            module_name: nome del modulo
            questions: pool completo di domande del modulo
        """        
        if len(questions) < self.QUESTIONS_AND_TIMES_PER_MODULE[module_name]:
            raise ValueError(
                f"Not enough questions for exam module. "
                f"Required: {self.QUESTIONS_AND_TIMES_PER_MODULE[module_name]}, available: {len(questions)}"
            )
        
        self.module_name = module_name
        
        # Seleziona QUESTIONS_AND_TIMES_PER_MODULE domande random
        self.questions = random.sample(questions, self.QUESTIONS_AND_TIMES_PER_MODULE[module_name])
        
        # Risposte dell'utente (key: cod_domanda, value: risposta)
        self.user_answers: Dict[str, str] = {}
        
        # Timer
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
        # Indice domanda corrente
        self.current_question_idx = 0
        
    def start_timer(self):
        """Avvia il timer del modulo"""
        self.start_time = time.time()
        self.end_time = None  # Reset end_time quando si riavvia il timer
         # print(f"[Debug ExamEngine] Timer started for module {self.module_name} at {self.start_time}")
    
    def get_elapsed_seconds(self) -> int:
        """
        Calcola i secondi trascorsi dall'inizio
        
        Returns:
            Secondi trascorsi
        """
        if self.start_time is None:
            return 0
        
        if self.end_time is not None:
            return int(self.end_time - self.start_time)
        
        return int(time.time() - self.start_time)
    
    def get_remaining_seconds(self, module_name) -> int:
        """
        Calcola i secondi rimanenti
        
        Returns:
            Secondi rimanenti (0 se il tempo è scaduto)
        """
        elapsed = self.get_elapsed_seconds()
        remaining = self.QUESTIONS_AND_TIMES_PER_MODULE[module_name]*60 - elapsed
        return max(0, remaining)
    
    def is_time_expired(self, module_name) -> bool:
        """Verifica se il tempo è scaduto"""
        return self.get_remaining_seconds(module_name) == 0
    
    def get_current_question(self) -> Optional[Dict[str, Any]]:
        """
        Restituisce la domanda corrente
        
        Returns:
            Dizionario con la domanda e metadata
        """
        if self.current_question_idx >= len(self.questions):
            return None
        
        question = self.questions[self.current_question_idx].copy()
        # Preserva cod_domanda dal JSON, non sovrascriverlo
        question["question_number"] = self.current_question_idx + 1
        question["total_questions"] = len(self.questions)
        
        return question
    
    def save_current_answer(self, answer: str):
        """
        Salva la risposta per la domanda corrente
        
        Args:
            answer: risposta selezionata dall'utente
        """
        current_question = self.questions[self.current_question_idx]
        cod_domanda = current_question.get("cod_domanda", str(self.current_question_idx))
         # print(f"[Debug ExamEngine] Saving answer for cod_domanda={cod_domanda}, answer={answer}")
        self.user_answers[cod_domanda] = answer
         # print(f"[Debug ExamEngine] Total answers saved: {len(self.user_answers)}")
    
    def next_question(self) -> bool:
        """
        Passa alla domanda successiva
        
        Returns:
            True se c'è una domanda successiva, False se siamo all'ultima
        """
        if self.current_question_idx < len(self.questions) - 1:
            self.current_question_idx += 1
            return True
        return False
    
    def previous_question(self) -> bool:
        """
        Torna alla domanda precedente
        
        Returns:
            True se c'è una domanda precedente, False se siamo alla prima
        """
        if self.current_question_idx > 0:
            self.current_question_idx -= 1
            return True
        return False
    
    def go_to_question(self, question_idx: int):
        """
        Vai a una domanda specifica
        
        Args:
            question_idx: indice della domanda (0-based)
        """
        if 0 <= question_idx < len(self.questions):
            self.current_question_idx = question_idx
    
    def get_saved_answer(self, question_idx: int) -> Optional[str]:
        """Recupera la risposta salvata per una domanda specifica (usa idx per compatibilità UI)"""
        if question_idx < len(self.questions):
            question = self.questions[question_idx]
            cod_domanda = question.get("cod_domanda", str(question_idx))
            return self.user_answers.get(cod_domanda)
        return None
    
    def get_answered_count(self) -> int:
        """Numero di domande a cui è stata data una risposta"""
        return len(self.user_answers)
    
    def finish_module(self) -> ModuleResult:
        """
        Termina il modulo e calcola il risultato
        
        Returns:
            Oggetto ModuleResult con i risultati
        """
        if self.end_time is None:
            self.end_time = time.time()
        
         # print(f"[Debug ExamEngine] finish_module called - Total questions: {len(self.questions)}")
         # print(f"[Debug ExamEngine] Total user answers: {len(self.user_answers)}")
         # print(f"[Debug ExamEngine] User answers: {self.user_answers}")
        
        correct = 0
        for idx, question in enumerate(self.questions):
            cod_domanda = question.get("cod_domanda", str(idx))
            user_answer = self.user_answers.get(cod_domanda)
            correct_answer = question["risposta_corretta"]
            
             # print(f"[Debug ExamEngine] Q{idx+1} cod={cod_domanda}, user={user_answer}, correct={correct_answer}")
            
            # Gestisce None nelle risposte
            if user_answer is None or user_answer == "":
                is_correct = False
            else:
                is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
            
             # print(f"[Debug ExamEngine] Q{idx+1} is_correct={is_correct}")
            
            if is_correct:
                correct += 1
        
        score_percentage = (correct / len(self.questions) * 100) if len(self.questions) > 0 else 0
        time_spent = self.get_elapsed_seconds()
        
        return ModuleResult(
            module_name=self.module_name,
            total_questions=len(self.questions),
            correct_answers=correct,
            score_percentage=score_percentage,
            time_spent_seconds=time_spent,
            completed=True
        )


class ExamEngine:
    """
    Engine principale per la simulazione d'esame completa.
    Gestisce multipli moduli in sequenza.
    """
    
    def __init__(self, modules_data: Dict[str, List[Dict[str, Any]]]):
        """
        Inizializza l'esame con i moduli selezionati
        
        Args:
            modules_data: dizionario {nome_modulo: lista_domande}
        """
        if not modules_data:
            raise ValueError("Cannot initialize exam with no modules")
        
        self.module_names = list(modules_data.keys())
        self.module_engines: List[ExamModuleEngine] = []
        
        # Crea un engine per ogni modulo
        for module_name, questions in modules_data.items():
            try:
                # Estrae un nome leggibile dal filename
                display_name = module_name.replace("_final.json", "").replace("_", " ").title()
                #print(f"This is the display name: {display_name}")
                engine = ExamModuleEngine(display_name, questions)
                self.module_engines.append(engine)
            except ValueError as e:
                raise ValueError(f"Error initializing module {module_name}: {str(e)}")
        
        self.current_module_idx = 0
        self.module_results: List[ModuleResult] = []
        
    def get_current_module(self) -> Optional[ExamModuleEngine]:
        """
        Restituisce l'engine del modulo corrente
        
        Returns:
            ExamModuleEngine o None se l'esame è finito
        """
        if self.current_module_idx >= len(self.module_engines):
            return None
        return self.module_engines[self.current_module_idx]
    
    def start_current_module(self):
        """Avvia il timer del modulo corrente"""
        module = self.get_current_module()
        if module:
            module.start_timer()
    
    def finish_current_module(self) -> ModuleResult:
        """
        Termina il modulo corrente e salva il risultato
        
        Returns:
            Risultato del modulo appena finito
        """
        module = self.get_current_module()
        if module is None:
            raise ValueError("No active module to finish")
        
        result = module.finish_module()
        self.module_results.append(result)
        return result
    
    def next_module(self) -> bool:
        """
        Passa al modulo successivo
        
        Returns:
            True se c'è un modulo successivo, False se l'esame è finito
        """
        if self.current_module_idx < len(self.module_engines) - 1:
            self.current_module_idx += 1
            return True
        return False
    
    def get_exam_progress(self) -> Dict[str, Any]:
        """
        Informazioni sullo stato di avanzamento dell'esame
        
        Returns:
            Dizionario con modulo corrente, totale moduli, ecc.
        """
        return {
            "current_module": self.current_module_idx + 1,
            "total_modules": len(self.module_engines),
            "completed_modules": len(self.module_results),
            "current_module_name": self.get_current_module().module_name if self.get_current_module() else None
        }
    
    def get_final_results(self) -> ExamResult:
        """
        Calcola i risultati finali dell'esame
        
        Returns:
            Oggetto ExamResult con tutti i risultati
        """
        total_correct = sum(r.correct_answers for r in self.module_results)
        total_questions = sum(r.total_questions for r in self.module_results)
        
        total_time = sum(r.time_spent_seconds for r in self.module_results)
        
        return ExamResult(
            module_results=self.module_results,
            total_correct=total_correct,
            total_questions=total_questions,
            total_time_spent_seconds=total_time
        )
