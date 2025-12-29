# Quiz App - Applicazione Streamlit per Quiz Interattivi

Applicazione web per la fruizione di quiz con tre modalità:
1. **Quiz domanda per domanda**
2. **Quiz completo**
3. **Simulazione esame**

I quiz caricati al momento riguardano un corso di laurea di infermieristica.

## Se vuoi usare l'applicazione Streamlit 

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

5. Verifica che la cartella `QUIZ_CLEAN/JSON` contenga i file quiz nel formato corretto:


## 🎮 Utilizzo

Avvia l'applicazione:
```bash
streamlit run streamlit_app.py
```

L'app si aprirà nel browser all'indirizzo `http://localhost:8501`

### 🔐 Primo Accesso

1. L'app si aprirà sulla schermata di login
  
2. Registrati creando un nuovo account:
   - Clicca sulla tab "Registrazione"
   - Inserisci username (min 3 caratteri, solo lettere/numeri/underscore/trattino)
   - Inserisci password (min 6 caratteri)
   - Le credenziali vengono salvate in modo sicuro (bcrypt hash)
   - Il browser può salvare le credenziali per accessi futuri

## 📚 Modalità Quiz

### 1. Quiz Domanda per Domanda

- Seleziona uno o più moduli
- Le domande vengono estratte casualmente senza ripetizioni
- Per ogni domanda puoi:
  - **Inviare** la risposta (con possibilità di riprovare se errata)
  - **Saltare** la domanda
  - **Mostrare** la risposta corretta
  - **Terminare** il quiz anticipatamente

**Statistiche finali:**
- Risposte corrette al 1°, 2°, 3°, 4°, 5+ tentativo
- Domande saltate
- Risposte mostrate

### 2. Quiz Completo

- Seleziona un solo modulo
- Visualizza tutte le domande in sequenza
- Rispondi a tutte le domande
- Clicca "Invia Risposte" per vedere il risultato finale
- Visualizza il dettaglio di ogni risposta (corretta/errata)

### 3. Simulazione Esame

- Seleziona uno o più moduli
- Per ogni modulo: 15 domande random + timer 15 minuti
- Naviga tra le domande con i pulsanti
- Salva le risposte prima di passare alla successiva
- Mappa visuale delle domande risposte
- Risultato per ogni modulo + punteggio complessivo


## 📊 Logging e Statistiche

### TODO: Sistema di Logging

### Statistiche Disponibili

Per ogni utente autenticato:
- Totale domande risposte
- Percentuale di risposte corrette
- Moduli affrontati
- Statistiche dettagliate per modulo

## 🗂️ Struttura File

```
.
├── streamlit_app.py              # App principale
├── quiz_loader.py                # Loader JSON
├── quiz_engine.py                # Engine quiz singolo
├── complete_quiz_engine.py       # Engine quiz completo
├── exam_engine.py                # Engine esame
├── auth.py                       # Autenticazione
├── logger.py                     # Logging
├── requirements.txt              # Dipendenze Python
├── README.md                     # Questo file
├── users.json                    # Utenti (auto-generato)
├── quiz_logs.json                # Log risposte (auto-generato)
└── QUIZ_CLEAN/
    └── JSON/
        ├── farmacologia_final.json
        ├── ptda_final.json
        └── radioprotezione_final.json
```

## 🔧 Personalizzazione

### Aggiungere nuovi quiz

1. Crea un file JSON nella cartella `QUIZ_CLEAN/JSON`
2. Nomina il file con pattern `nomemodulo_final.json`
3. Usa la struttura standard:
```json
[
  {
    "num_domanda": 1,
    "domanda": "Testo domanda",
    "opzioni": ["A", "B", "C", "D"],
    "risposta_corretta": "A"
  }
]
```

### Modificare timer esame

In [exam_engine.py](exam_engine.py#L21), modifica:
```python
TIME_LIMIT_SECONDS = 15 * 60  # Cambia 15 con i minuti desiderati
```

### Modificare numero domande per esame

In [exam_engine.py](exam_engine.py#L20), modifica:
```python
QUESTIONS_PER_MODULE = 15  # Cambia con il numero desiderato
```

## 🚀 Migrazione Futura

Il codice è predisposto per una migrazione a:
- **Backend separato** (FastAPI/Flask)
- **Database** (SQLite, PostgreSQL, Firestore, MongoDB)
- **Cloud deployment** (GCP Cloud Run, AWS, ecc.)

La logica è **completamente indipendente da Streamlit**, rendendo facile:
1. Mantenere gli engine (`quiz_engine.py`, `exam_engine.py`, ecc.)
2. Creare API REST che li utilizzano
3. Sviluppare un frontend React/Vue/Angular

## 🐛 Troubleshooting

**I quiz non vengono caricati:**
- Verifica che i file JSON siano in `QUIZ_CLEAN/JSON`
- Verifica che i file terminino con `_final.json`
- Controlla la struttura JSON

**Il timer dell'esame non funziona:**
- È normale, Streamlit aggiorna la pagina automaticamente
- Non interrompere il flusso dell'esame