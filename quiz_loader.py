"""
Modulo per il caricamento e la normalizzazione dei quiz da file JSON.
Responsabile di:
- Elencare i file JSON disponibili nella cartella
- Caricare e validare la struttura dei quiz
- Normalizzare i dati per l'uso nei diversi engine
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional


class QuizLoader:
    """Gestisce il caricamento dei quiz da file JSON"""
    
    def __init__(self, quiz_folder: Path):
        """
        Inizializza il loader con il percorso della cartella quiz
        
        Args:
            quiz_folder: percorso relativo o assoluto alla cartella contenente i JSON
        """
        # Risolve il path relativo alla posizione di questo file, non alla working directory
        self.quiz_folder = quiz_folder

        # print("QUIZ FOLDER:", self.quiz_folder)
        # print("EXISTS:", self.quiz_folder.exists())
        # print("FILES:", list(self.quiz_folder.glob("*.json")))
        
    def get_available_quizzes(self) -> List[Dict[str, str]]:
        """
        Restituisce la lista dei quiz disponibili
        
        Returns:
            Lista di dizionari con 'name' (nome visualizzato) e 'file' (nome file)
        """
        # print("QUIZ folder in get_available_quizzes:", self.quiz_folder)
        if not self.quiz_folder.exists():
            return []
        
        quizzes = []
        for json_file in self.quiz_folder.glob("*_final.json"):
            # Estrae il nome del modulo dal nome file (es. "farmacologia_final.json" -> "Farmacologia")
            module_name = json_file.stem.replace("_final", "").replace("_", " ").title()
            quizzes.append({
                "name": module_name,
                "file": json_file.name
            })
        
        return sorted(quizzes, key=lambda x: x["name"])
    
    def load_quiz(self, quiz_file: str) -> List[Dict[str, Any]]:
        """
        Carica un singolo quiz da file JSON
        
        Args:
            quiz_file: nome del file JSON da caricare
            
        Returns:
            Lista di domande normalizzate
            
        Raises:
            FileNotFoundError: se il file non esiste
            json.JSONDecodeError: se il file non è un JSON valido
            ValueError: se la struttura non è valida
        """
        file_path = self.quiz_folder / quiz_file

        print("File path in load_quiz: ", file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Quiz file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
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
                question["source_quiz"] = quiz_file
                all_questions.append(question)
        
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


def get_quiz_loader(quiz_folder: Path = None) -> QuizLoader:
    """
    Factory function per ottenere un'istanza del QuizLoader
    Utile per dependency injection e testing
    """
    if quiz_folder is None:
        # Default: path relativo alla posizione di questo file
        quiz_folder = Path(__file__).parent / "QUIZ_CLEAN" / "JSON"
    return QuizLoader(quiz_folder)
