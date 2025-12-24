import json
import secrets
import string

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
    Assegna un codice univoco a ogni domanda nel quiz
    
    Args:
        quiz_file: nome del file JSON da caricare
        
    Returns:
        Lista di domande con campo 'cod_domanda' aggiunto
    """
    file_path = f"QUIZ_CLEAN/JSON/{quiz_file}"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Genera codici univoci per ogni domanda
    used_codes = set()
    
    for question in data:
        # Genera un codice univoco di 8 caratteri alfanumerici
        while True:
            cod_domanda = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            if cod_domanda not in used_codes:
                used_codes.add(cod_domanda)
                break
        
        question["cod_domanda"] = cod_domanda
    
    return data


def main():
    files = ["farmacologia_final.json", "ptda_final.json", "radioprotezione_final.json"]

    for f in files:
        print(f"\nProcessing {f}...")
        validate_quiz(f)
        # updated_questions = assign_unique_question_id(f)
        
        # # Sovrascrivi il file con le domande aggiornate
        # file_path = f"QUIZ_CLEAN/JSON/{f}"
        # with open(file_path, 'w', encoding='utf-8') as file:
        #     json.dump(updated_questions, file, ensure_ascii=False, indent=2)
        
        # print(f"✓ {f} updated with unique question IDs") 



if __name__=="__main__":
    main()
