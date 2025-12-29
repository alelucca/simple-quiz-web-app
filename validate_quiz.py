import json
import secrets
import string
import os
from pathlib import Path

def normalize_question(question, source_file):
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
        required_fields = ["num_domanda", "domanda", "opzioni", "risposta_corretta"]
        
        for field in required_fields:
            if field not in question:
                raise ValueError(f"Missing required field: {field}")
        
        # Valida opzioni
        if not isinstance(question["opzioni"], list) or len(question["opzioni"]) != 4:
            raise ValueError("'opzioni' must be a list with 4 options")
        
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

def validate_quiz(quiz_file: str) -> None:
    """
    Stampa domande con struttura non valida nei quiz
    
    Args:
        quiz_file: nome del file JSON da caricare
        
    Returns:
        None

    """
    file_path = f"QUIZ_CLEAN/JSON/{quiz_file}"    
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Valida la struttura
    if not isinstance(data, list):
        raise ValueError(f"Invalid quiz structure in {quiz_file}: expected a list")
    
    # Normalizza e valida ogni domanda
    normalized_questions = []
    for idx, question in enumerate(data):
        try:
            normalized = normalize_question(question, quiz_file)
            normalized_questions.append(normalized)
        except Exception as e:
            print(f"Error in question {idx + 1} of {quiz_file}: {str(e)}")
    
    # return normalized_questions

def assign_unique_question_id(quiz_file: str):
    """
    Assegna un codice univoco a ogni domanda nel quiz che non ha già cod_domanda
    
    Args:
        quiz_file: nome del file JSON da caricare
        
    Returns:
        Tupla (Lista di domande con campo 'cod_domanda', bool indicante se ci sono stati aggiornamenti)
    """
    file_path = f"QUIZ_CLEAN/JSON/{quiz_file}"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Genera codici univoci per ogni domanda che non ha già cod_domanda
    used_codes = set()
    updated = False
    
    # Prima raccoglie tutti i cod_domanda esistenti
    for question in data:
        if "cod_domanda" in question:
            used_codes.add(question["cod_domanda"])
    
    # Poi genera i codici mancanti
    for question in data:
        if "cod_domanda" not in question:
            # Genera un codice univoco di 8 caratteri alfanumerici
            while True:
                cod_domanda = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
                if cod_domanda not in used_codes:
                    used_codes.add(cod_domanda)
                    break
            
            question["cod_domanda"] = cod_domanda
            updated = True
    
    return data, updated

def main():
    """
    Processa tutti i file JSON nella cartella QUIZ_CLEAN/JSON:
    - Valida che terminino con _final.json
    - Valida la struttura delle domande
    - Aggiunge cod_domanda se mancante
    - Risalva il file aggiornato
    """
    json_dir = Path("QUIZ_CLEAN/JSON")
    
    # Verifica che la directory esista
    if not json_dir.exists():
        raise FileNotFoundError(f"Directory {json_dir} not found")
    
    # Trova tutti i file nella directory
    all_files = [f for f in os.listdir(json_dir) if os.path.isfile(json_dir / f)]
    
    # Filtra per file che terminano con _final.json
    json_files = [f for f in all_files if f.endswith("_final.json")]
    
    if not json_files:
        print("No files ending with _final.json found in QUIZ_CLEAN/JSON")
        return
    
    print(f"Found {len(json_files)} file(s) to process:\n")
    
    for filename in json_files:
        print(f"Processing {filename}...")
        
        # Verifica che sia un JSON valido
        try:
            with open(json_dir / filename, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file {filename}: {str(e)}")
        
        # Valida la struttura del quiz
        print(f"  Validating structure...")
        validate_quiz(filename)
        
        # Assegna cod_domanda se mancante
        print(f"  Checking for missing cod_domanda...")
        updated_questions, was_updated = assign_unique_question_id(filename)
        
        if was_updated:
            # Salva il file aggiornato
            file_path = json_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(updated_questions, f, ensure_ascii=False, indent=2)
            print(f"  ✓ {filename} updated with unique question IDs")
        else:
            print(f"  ✓ {filename} already has all cod_domanda assigned")
        
        print()

if __name__=="__main__":
    main()
