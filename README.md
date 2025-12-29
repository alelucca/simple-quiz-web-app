# Quiz App - Applicazione Streamlit per Quiz Interattivi

Applicazione web per la fruizione di quiz con tre modalità:
1. **Quiz domanda per domanda**
2. **Quiz completo**
3. **Simulazione esame**

I quiz caricati al momento riguardano un corso di laurea di infermieristica.

## Se vuoi usare l'applicazione Streamlit con i quiz pre-inseriti

1. Vai al link 
2. Registrati
3. Fai il login
4. Prova una modalità

## Se ti piace l'idea ma vuoi personalizzarla con i tuoi quiz

1. Clona o scarica il repository

2. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

3. Configura le credenziali per il logging delle registrazioni in `.streamlit/secrets.toml`. Puoi seguire [questa guida](https://docs.streamlit.io/develop/tutorials/databases/private-gsheet) per eventuali dubbi.

4. Carica i tuoi quiz nella cartella `QUIZ_CLEAN/JSON`
   Regole per caricare i quiz: 
   - Il file .json deve chiamarsi *_final.json
   - Il file di quiz deve avere questo formato
      ```json
      [
        {
          "num_domanda": 1,
          "domanda": "...",
          "opzioni": ["...", "...", "...", "..."],
          "risposta_corretta": "..."
        }
      ]
      ```
    NB: Puoi usare validate_quiz.py per verificare la correttezza dei quiz inseriti e inserire in automatico anche il codice della domanda

5. Per la modalità esame, specifica il numero di domande in `exam_engine.py` (viene considerato 1 min per domanda)
   ```python
   QUESTIONS_AND_TIMES_PER_MODULE = {
        "Farmacologia Clinica": 30, # come chiave, prima lettera maiuscola e spazio tra parole
        "Il Mio Quiz": 13
    }
    DEFAULT_VALUE = 15 # valore di default: 15 domande in 15 minuti
    ```

6. Test o utilizzo in locale

  Avvia l'applicazione:
  ```bash
  streamlit run streamlit_app.py
  ```

  L'app si aprirà nel browser all'indirizzo `http://localhost:8501`


## 📚 Modalità Quiz

### 1. Quiz Domanda per Domanda

- Seleziona uno o più moduli
- Le domande vengono estratte casualmente senza ripetizioni
- Per ogni domanda puoi:
  - **Inviare** la risposta (con feedback immediato e possibilità di riprovare)
  - **Saltare** la domanda
  - **Mostrare** la risposta corretta
  - **Terminare** il quiz anticipatamente

- Statistiche finali mostrate quando si termina il quiz

### 2. Quiz Completo

- Seleziona un solo modulo
- Visualizza tutte le domande in sequenza
- Rispondi a tutte le domande
- Clicca "Invia Risposte" per vedere il risultato finale
- Visualizza il dettaglio di ogni risposta (corretta/errata)

### 3. Simulazione Esame

- Seleziona uno o più moduli
- Per ogni modulo è definito il numero di domande e il tempo come all'esame
- Naviga tra le domande con i pulsanti
- Salva le risposte prima di passare alla successiva
- Mappa visuale delle domande risposte
- Risultato per ogni modulo + punteggio complessivo

### TODO: Sistema di Logging

## 🗂️ Struttura File

```
.
├── streamlit_app.py              # App principale
├── quiz_loader.py                # Loader JSON
├── quiz_engine.py                # Engine quiz singolo
├── complete_quiz_engine.py       # Engine quiz completo
├── exam_engine.py                # Engine esame
├── auth.py                       # Autenticazione con gsheets
├── logger.py                     # Logging (da integrare)
├── requirements.txt              # Dipendenze Python
├── README.md                     # Questo file
└── QUIZ_CLEAN/
    └── JSON/
        ├── farmacologia_generale_final.json
        ├── farmacologia_clinica_final.json
        ├── aptd_final.json
        └── radioprotezione_final.json
```