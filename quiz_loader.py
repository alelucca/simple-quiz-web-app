"""
Modulo per il caricamento e la normalizzazione dei quiz da MongoDB (in memoria).
Responsabile di:
- Elencare i quiz disponibili a partire dai documenti Mongo
- Caricare e validare la struttura dei quiz
- Normalizzare i dati per l'uso nei diversi engine
"""

import random
from typing import List, Dict, Any


class QuizLoader:
    """Gestisce il caricamento dei quiz da documenti MongoDB"""
    
    def __init__(self, quiz_documents: List[Dict[str, Any]]):
        """
        Inizializza il loader con i documenti del quiz caricati da MongoDB
        
        Args:
            quiz_documents: lista di documenti Mongo con campi `materia` e
                `lista_domande_risposte`
        """
        self.quiz_documents = list(quiz_documents)
        self._quizzes_by_file: Dict[str, Dict[str, Any]] = {}

        for item in self.quiz_documents:
            materia = item.get("materia")
            if not materia:
                continue
            quiz_file = self._build_quiz_file_name(str(materia))
            self._quizzes_by_file[quiz_file] = item

    @staticmethod
    def _build_quiz_file_name(materia: str) -> str:
        """Costruisce un identificatore compatibile con il vecchio naming a file."""
        return f"{materia}_final.json"
        
    def get_available_quizzes(self) -> List[Dict[str, str]]:
        """
        Restituisce la lista dei quiz disponibili
        
        Returns:
            Lista di dizionari con 'name' (nome visualizzato) e 'file' (nome file)
        """
        quizzes = []
        for item in self.quiz_documents:
            materia = item.get("materia")
            questions = item.get("lista_domande_risposte")
            if not materia or not isinstance(questions, list):
                continue

            module_name = str(materia).replace("_", " ").title()
            quizzes.append({
                "name": module_name,
                "file": self._build_quiz_file_name(str(materia)),
            })
        
        return sorted(quizzes, key=lambda x: x["name"])
    
    def load_quiz(self, quiz_file: str) -> List[Dict[str, Any]]:
        """
        Carica un singolo quiz dai documenti Mongo in memoria
        
        Args:
            quiz_file: nome del file JSON da caricare
            
        Returns:
            Lista di domande normalizzate
            
        Raises:
            FileNotFoundError: se il quiz non esiste nei documenti Mongo
            ValueError: se la struttura non è valida
        """
        quiz_document = self._quizzes_by_file.get(quiz_file)
        if quiz_document is None:
            raise FileNotFoundError(f"Quiz not found: {quiz_file}")

        data = quiz_document.get("lista_domande_risposte")
        
        # Valida la struttura
        if not isinstance(data, list):
            raise ValueError(f"Invalid quiz structure in {quiz_file}: expected a list")
        
        # Normalizza e valida ogni domanda
        normalized_questions = []
        for idx, question in enumerate(data):
            try:
                normalized = self._normalize_question(question, quiz_file)
                normalized_questions.append(normalized)
            except Exception as e:
                raise ValueError(f"Error in question {idx + 1} of {quiz_file}: {str(e)}")
        
        return normalized_questions
    
    def load_multiple_quizzes(self, quiz_files: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Carica più quiz contemporaneamente
        
        Args:
            quiz_files: lista di nomi file da caricare
            
        Returns:
            Dizionario con nome file come chiave e lista domande come valore
        """
        quizzes = {}
        for quiz_file in quiz_files:
            quizzes[quiz_file] = self.load_quiz(quiz_file)
        return quizzes
    
    def merge_quizzes(self, quiz_files: List[str]) -> List[Dict[str, Any]]:
        """
        Carica e unisce più quiz in un unico pool di domande
        
        Args:
            quiz_files: lista di nomi file da caricare e unire
            
        Returns:
            Lista unica di tutte le domande con metadata sul quiz di origine
        """
        all_questions = []
        
        for quiz_file in quiz_files:
            questions = self.load_quiz(quiz_file)
            # Aggiunge metadata sul quiz di origine
            for question in questions:
                question_with_source = question.copy()
                question_with_source["source_quiz"] = quiz_file
                all_questions.append(question_with_source)
        
        # randomize question order also between various modules
        random.shuffle(all_questions)

        return all_questions
    
    def _normalize_question(self, question: Dict[str, Any], source_file: str) -> Dict[str, Any]:
        """
        Normalizza e valida una singola domanda
        
        Args:
            question: dizionario con i dati della domanda
            source_file: nome del file sorgente (per error reporting)
            
        Returns:
            Domanda normalizzata
            
        Raises:
            ValueError: se mancano campi obbligatori o sono invalidi
        """
        required_fields = ["num_domanda", "domanda", "opzioni", "risposta_corretta", "cod_domanda"]
        
        for field in required_fields:
            if field not in question:
                raise ValueError(f"Missing required field: {field}")
        
        # Valida opzioni
        if not isinstance(question["opzioni"], list) or len(question["opzioni"]) < 2:
            raise ValueError("'opzioni' must be a list with at least 2 options")
        
        # Valida che la risposta corretta sia tra le opzioni
        if question["risposta_corretta"] not in question["opzioni"]:
            raise ValueError(f"'risposta_corretta' must be one of the options")
        
        # Normalizza la struttura
        return {
            "num_domanda": question["num_domanda"],
            "domanda": question["domanda"].strip(),
            "opzioni": [opt.strip() for opt in question["opzioni"]],
            "risposta_corretta": question["risposta_corretta"].strip(),
            "source_quiz": source_file,
            "cod_domanda": question["cod_domanda"]
        }


def get_quiz_loader(quiz_documents: List[Dict[str, Any]] = None) -> QuizLoader:
    """
    Factory function per ottenere un'istanza del QuizLoader
    Utile per dependency injection e testing
    """
    if quiz_documents is None:
        quiz_documents = []
    return QuizLoader(quiz_documents)
