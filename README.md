# Quiz App - Applicazione Streamlit per Quiz Interattivi

Applicazione web per la fruizione di quiz con tre modalità:
1. **Quiz domanda per domanda** - con retry e tracking tentativi
2. **Quiz completo** - tutte le domande insieme con feedback finale
3. **Simulazione esame** - 15 domande per modulo con timer 15 minuti

## ✨ Funzionalità Principali

- 🔐 **Autenticazione utenti** con registrazione e login
- 🔒 **Password sicure** hashate con bcrypt
- 📊 **Logging avanzato** su Google Sheets (con fallback locale)
- 💾 **Salvataggio credenziali** nel browser
- 📈 **Statistiche utente** personalizzate
- 🎯 **Tre modalità di quiz** distinte

## 🏗️ Architettura

L'applicazione è progettata con una **separazione netta tra logica e UI**:

- `quiz_loader.py` - Caricamento e normalizzazione JSON
- `quiz_engine.py` - Logica modalità 1 (quiz singolo)
- `complete_quiz_engine.py` - Logica modalità 2 (quiz completo)
- `exam_engine.py` - Logica modalità 3 (simulazione esame)
- `auth.py` - Sistema autenticazione con bcrypt e validazione anti-SQL injection
- `logger.py` - Logging risposte su Google Sheets (con fallback JSON)
- `streamlit_app.py` - UI principale

## 📋 Requisiti

- Python 3.8+
- Streamlit 1.30+
- bcrypt 4.0+
- gspread 5.12+ (opzionale, per Google Sheets)
- oauth2client 4.1+ (opzionale, per Google Sheets)

## 🚀 Installazione

1. Clona o scarica il repository

2. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

3. Inizializza il file secrets con gli utenti demo:
```bash
python init_secrets.py
```
   Questo creerà il file `.streamlit/secrets.toml` con:
   - Utente demo: `demo` / `demo123`
   - Utente admin: `admin` / `admin123`

4. (Opzionale) Configura Google Sheets per il logging:
   - Segui le istruzioni in [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)
   - Aggiungi le credenziali GCP al file `.streamlit/secrets.toml`
   - Se non configuri Google Sheets, l'app userà un file JSON locale

5. Verifica che la cartella `QUIZ_CLEAN/JSON` contenga i file quiz nel formato corretto:
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

## 🎮 Utilizzo

Avvia l'applicazione:
```bash
streamlit run streamlit_app.py
```

L'app si aprirà nel browser all'indirizzo `http://localhost:8501`

### 🔐 Primo Accesso

1. L'app si aprirà sulla schermata di login
2. Puoi usare gli account demo:
   - Username: `demo` / Password: `demo123`
   - Username: `admin` / Password: `admin123`
3. Oppure registrati creando un nuovo account:
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

## 🔒 Sicurezza

### Password
- Le password sono hashate usando **bcrypt** con salt automatico
- Gli hash vengono salvati in `.streamlit/secrets.toml`
- Non è possibile recuperare la password originale dall'hash
- Validazione input per prevenire SQL injection

### Validazione Username
- Minimo 3 caratteri, massimo 50
- Solo caratteri alfanumerici, underscore e trattino
- Case-sensitive (ma previene duplicati case-insensitive)

### File Sensibili
Il file `.streamlit/secrets.toml` contiene:
- Hash delle password utente
- Credenziali Google Cloud (se configurato)
- **NON committare mai questo file su repository pubblici**

## 📊 Logging e Statistiche

### Sistemi di Logging

L'app supporta due modalità di logging:

#### 1. Google Sheets (Consigliato)
- Dati salvati in un foglio Google privato "log_streamlit"
- Due fogli separati:
  - `answers`: log di ogni singola risposta
  - `sessions`: riassunti delle sessioni di quiz
- Accessibile da qualsiasi dispositivo
- Backup automatico by Google
- Configurazione: vedi [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)

#### 2. File JSON Locale (Fallback)
- Se Google Sheets non è configurato, usa `quiz_logs.json`
- Salvato localmente nella directory del progetto

### Statistiche Disponibili

Per ogni utente autenticato:
- Totale domande risposte
- Percentuale di risposte corrette
- Moduli affrontati
- Statistiche dettagliate per modulo

## 🔐 Autenticazione

L'autenticazione è **abilitata di default**.
- Username: `admin` / Password: `admin123`

## 📊 Logging (Opzionale)

Il sistema di logging è **sempre attivo** se l'autenticazione è abilitata.

I log vengono salvati in `quiz_logs.json` e includono:
- Ogni risposta data dall'utente
- Timestamp, tentativo, correttezza
- Riepilogo sessioni

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
- **Database** (SQLite, PostgreSQL, Firestore)
- **Cloud deployment** (GCP Cloud Run, AWS, ecc.)

La logica è **completamente indipendente da Streamlit**, rendendo facile:
1. Mantenere gli engine (`quiz_engine.py`, `exam_engine.py`, ecc.)
2. Creare API REST che li utilizzano
3. Sviluppare un frontend React/Vue/Angular

## 📝 Note

- Tutti i commenti sono in **italiano**
- Tutte le variabili/funzioni sono in **inglese**
- Nessuna dipendenza esterna eccetto Streamlit
- Codice testabile e modulare

## 🐛 Troubleshooting

**I quiz non vengono caricati:**
- Verifica che i file JSON siano in `QUIZ_CLEAN/JSON`
- Verifica che i file terminino con `_final.json`
- Controlla la struttura JSON

**Il timer dell'esame non funziona:**
- È normale, Streamlit aggiorna la pagina automaticamente
- Non interrompere il flusso dell'esame

**Le statistiche utente non si salvano:**
- Abilita l'autenticazione
- Verifica che `quiz_logs.json` sia scrivibile

## 📄 Licenza

Progetto personale - uso interno.
