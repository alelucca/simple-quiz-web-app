# Quiz App - Streamlit Interactive Quiz Application

Web application for interactive quizzes with three modes:
1. **Question by Question Quiz**
2. **Complete Quiz**
3. **Exam Simulation**

## If you want to use the Streamlit application with pre-loaded quizzes

1. Go to the link
2. Register
3. Log in
4. Try a mode

## If you like the idea but want to customize it with your own quizzes

1. Clone or download the repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure credentials for registration logging in `.streamlit/secrets.toml`. You can follow [this guide](https://docs.streamlit.io/develop/tutorials/databases/private-gsheet) for any questions.

4. Upload your quizzes to the `QUIZ_CLEAN/JSON` folder
   Rules for uploading quizzes:
   - The .json file must be named *_final.json
   - The quiz file must have this format:
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
    NB: You can use validate_quiz.py to verify the correctness of inserted quizzes and automatically add question codes

5. For exam mode, specify the number of questions in `exam_engine.py` (1 minute per question is considered)
   ```python
   QUESTIONS_AND_TIMES_PER_MODULE = {
        "Module Name": 30, # as key, first letter capitalized and space between words
        "My Quiz": 13
    }
    DEFAULT_VALUE = 15 # default value: 15 questions in 15 minutes
    ```

6. Testing or local usage

  Launch the application:
  ```bash
  streamlit run streamlit_app.py
  ```

  The app will open in your browser at `http://localhost:8501`


## 📚 Quiz Modes

### 1. Question by Question Quiz

- Select one or more modules
- Questions are randomly extracted without repetition
- For each question you can:
  - **Submit** the answer (with immediate feedback and retry option)
  - **Skip** the question
  - **Show** the correct answer
  - **End** the quiz early

- Final statistics shown when the quiz ends

### 2. Complete Quiz

- Select a single module
- View all questions in sequence
- Answer all questions
- Click "Submit Answers" to see the final result
- View details of each answer (correct/incorrect)

### 3. Exam Simulation

- Select one or more modules
- For each module, the number of questions and time are defined as in a real exam
- Navigate between questions with buttons
- Save answers before moving to the next one
- Visual map of answered questions
- Result for each module + overall score

### TODO: Move JSON Files from In-Memory to Persistent Storage

## 🗂️ File Structure

```
.
├── streamlit_app.py              # Main app
├── quiz_loader.py                # JSON loader
├── quiz_engine.py                # Single quiz engine
├── complete_quiz_engine.py       # Complete quiz engine
├── exam_engine.py                # Exam engine
├── auth.py                       # Authentication with gsheets
├── logger.py                     # Logging (to be integrated)
├── requirements.txt              # Python dependencies
├── README.md                     # This file
└── QUIZ_CLEAN/
    └── JSON/
        ├── *_final.json        
        
```
