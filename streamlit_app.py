"""
Quiz App - Applicazione Streamlit per la fruizione di quiz interattivi
Supporta tre modalità:
1. Quiz domanda per domanda (con retry e tracking)
2. Quiz completo (tutte le domande insieme)
3. Simulazione esame (15 domande per modulo con timer)

Con autenticazione e logging opzionali.
"""

import streamlit as st
from datetime import datetime
import time

# Import dei moduli custom
from quiz_loader import QuizLoader
from quiz_engine import SingleQuestionQuizEngine
from complete_quiz_engine import CompleteQuizEngine
from exam_engine import ExamEngine
from auth import (
    AuthManager, init_session_auth, login_user, logout_user,
    is_authenticated, get_current_user
)
from logger import QuizLogger, generate_session_id


# ============================================================================
# CONFIGURAZIONE E INIZIALIZZAZIONE
# ============================================================================

def init_session_state():
    """Inizializza tutte le variabili di sessione necessarie"""
    
    # Autenticazione
    init_session_auth(st.session_state)
    
    # Modalità app
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = "home"  # home, single_question, complete, exam
    
    # Quiz loader
    if "quiz_loader" not in st.session_state:
        st.session_state.quiz_loader = QuizLoader()
    
    # Auth manager
    if "auth_manager" not in st.session_state:
        st.session_state.auth_manager = AuthManager()
    
    # Logger
    if "quiz_logger" not in st.session_state:
        st.session_state.quiz_logger = QuizLogger()
    
    # Engine attivo
    if "active_engine" not in st.session_state:
        st.session_state.active_engine = None
    
    # Session ID per logging
    if "session_id" not in st.session_state:
        st.session_state.session_id = generate_session_id()
    
    # Stato quiz (per evitare re-render issues)
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False
    
    # Feedback temporaneo
    if "feedback_message" not in st.session_state:
        st.session_state.feedback_message = None


# ============================================================================
# LOGIN / AUTENTICAZIONE
# ============================================================================

def show_login_page():
    """Mostra la pagina di login"""
    st.title("🔐 Login")
    
    st.info("**Utenti demo:**\n- Username: `demo` / Password: `demo123`\n- Username: `admin` / Password: `admin123`")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Accedi")
        
        if submit:
            user = st.session_state.auth_manager.authenticate(username, password)
            if user:
                login_user(st.session_state, user)
                st.success(f"Benvenuto, {user.display_name}!")
                st.rerun()
            else:
                st.error("Credenziali non valide")


# ============================================================================
# HOME PAGE
# ============================================================================

def show_home_page():
    """Mostra la home page con le opzioni principali"""
    
    user = get_current_user(st.session_state)
    if user:
        st.title(f"👋 Benvenuto, {user.display_name}")
    else:
        st.title("📚 Quiz App")
    
    st.markdown("---")
    st.subheader("Seleziona una modalità di quiz:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🎯 Quiz Singolo")
        st.write("Rispondi domanda per domanda con possibilità di riprovare")
        if st.button("Inizia", key="btn_single", use_container_width=True):
            st.session_state.app_mode = "single_question_setup"
            st.rerun()
    
    with col2:
        st.markdown("### 📝 Quiz Completo")
        st.write("Rispondi a tutte le domande e ricevi il risultato finale")
        if st.button("Inizia", key="btn_complete", use_container_width=True):
            st.session_state.app_mode = "complete_setup"
            st.rerun()
    
    with col3:
        st.markdown("### ⏱️ Simula Esame")
        st.write("15 domande per modulo con timer di 15 minuti")
        if st.button("Inizia", key="btn_exam", use_container_width=True):
            st.session_state.app_mode = "exam_setup"
            st.rerun()
    
    # Stats utente (se autenticato)
    if user:
        st.markdown("---")
        st.subheader("📊 Le tue statistiche")
        stats = st.session_state.quiz_logger.get_user_stats(user.username)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Domande risposte", stats["total_questions_answered"])
        col2.metric("Percentuale corrette", f"{stats['correct_rate']:.1f}%")
        col3.metric("Moduli praticati", len(stats["modules_practiced"]))


# ============================================================================
# MODALITÀ 1: QUIZ DOMANDA PER DOMANDA
# ============================================================================

def show_single_question_setup():
    """Setup iniziale per quiz domanda per domanda"""
    st.title("🎯 Quiz Domanda per Domanda")
    st.markdown("Seleziona uno o più moduli da cui estrarre le domande.")
    
    available_quizzes = st.session_state.quiz_loader.get_available_quizzes()
    
    if not available_quizzes:
        st.error("Nessun quiz disponibile nella cartella QUIZ_CLEAN/JSON")
        if st.button("Torna alla home"):
            st.session_state.app_mode = "home"
            st.rerun()
        return
    
    selected_files = st.multiselect(
        "Seleziona i moduli:",
        options=[q["file"] for q in available_quizzes],
        format_func=lambda x: next(q["name"] for q in available_quizzes if q["file"] == x)
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Inizia Quiz", disabled=len(selected_files) == 0):
            # Carica e unisci i quiz
            questions = st.session_state.quiz_loader.merge_quizzes(selected_files)
            st.session_state.active_engine = SingleQuestionQuizEngine(questions)
            st.session_state.app_mode = "single_question_quiz"
            st.session_state.session_id = generate_session_id()
            st.rerun()
    
    with col2:
        if st.button("Annulla"):
            st.session_state.app_mode = "home"
            st.rerun()


def show_single_question_quiz():
    """Mostra il quiz domanda per domanda"""
    engine = st.session_state.active_engine
    
    if engine is None:
        st.error("Errore: engine non inizializzato")
        return
    
    st.title("🎯 Quiz Domanda per Domanda")
    
    # Progress bar
    total = engine.total_questions
    remaining = engine.get_remaining_count()
    answered = total - remaining
    
    st.progress(answered / total if total > 0 else 0)
    st.caption(f"Domande completate: {answered}/{total}")
    
    # Ottieni domanda corrente o prossima
    if not engine.is_current_question_completed():
        question = engine.questions[engine.current_question_idx] if engine.current_question_idx is not None else None
        if question is None:
            question = engine.get_next_question()
    else:
        question = engine.get_next_question()
    
    if question is None:
        # Quiz terminato
        show_single_question_results()
        return
    
    # Mostra domanda
    st.markdown("### Domanda")
    st.write(question["domanda"])
    
    st.markdown("### Opzioni")
    
    # Radio button per le opzioni
    answer = st.radio(
        "Seleziona la tua risposta:",
        options=question["opzioni"],
        key=f"answer_{question['question_id']}"
    )
    
    # Feedback message
    if st.session_state.feedback_message:
        if "✅" in st.session_state.feedback_message:
            st.success(st.session_state.feedback_message)
        elif "❌" in st.session_state.feedback_message:
            st.error(st.session_state.feedback_message)
        else:
            st.info(st.session_state.feedback_message)
    
    # Pulsanti azione
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("✔️ Invia Risposta", use_container_width=True):
            is_correct, correct_answer = engine.check_answer(answer)
            
            # Log risposta
            if is_authenticated(st.session_state):
                user = get_current_user(st.session_state)
                attempt_num = engine.attempts[engine.current_question_idx].num_attempts
                st.session_state.quiz_logger.log_answer(
                    username=user.username,
                    quiz_mode="single_question",
                    module_name=question.get("source_quiz", "unknown"),
                    question_id=question["num_domanda"],
                    user_answer=answer,
                    correct_answer=correct_answer,
                    is_correct=is_correct,
                    attempt_number=attempt_num,
                    session_id=st.session_state.session_id
                )
            
            if is_correct:
                st.session_state.feedback_message = f"✅ Corretto! Risposta: {correct_answer}"
            else:
                st.session_state.feedback_message = f"❌ Errato. Riprova!"
            
            st.rerun()
    
    with col2:
        if st.button("⏭️ Salta Domanda", use_container_width=True):
            engine.skip_question()
            st.session_state.feedback_message = None
            st.rerun()
    
    with col3:
        if st.button("👁️ Mostra Risposta", use_container_width=True):
            correct = engine.show_answer()
            st.session_state.feedback_message = f"💡 La risposta corretta è: {correct}"
            st.rerun()
    
    with col4:
        if st.button("🛑 Termina Quiz", use_container_width=True):
            st.session_state.app_mode = "single_question_results"
            st.rerun()


def show_single_question_results():
    """Mostra i risultati del quiz domanda per domanda"""
    engine = st.session_state.active_engine
    stats = engine.get_stats()
    
    st.title("📊 Risultati Quiz")
    
    st.markdown("---")
    st.subheader("Riepilogo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Totale domande", stats.total_questions)
        st.metric("Risposte corrette", stats.get_total_correct())
    
    with col2:
        percentage = (stats.get_total_correct() / stats.total_questions * 100) if stats.total_questions > 0 else 0
        st.metric("Percentuale", f"{percentage:.1f}%")
    
    st.markdown("---")
    st.subheader("Dettaglio tentativi")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("1° tentativo", stats.correct_first_try)
    col2.metric("2° tentativo", stats.correct_second_try)
    col3.metric("3° tentativo", stats.correct_third_try)
    col4.metric("4° tentativo", stats.correct_fourth_try)
    col5.metric("5+ tentativi", stats.correct_more_tries)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    col1.metric("Domande saltate", stats.skipped)
    col2.metric("Risposte mostrate", stats.shown)
    
    # Log session summary
    if is_authenticated(st.session_state):
        user = get_current_user(st.session_state)
        st.session_state.quiz_logger.log_session_summary(
            username=user.username,
            quiz_mode="single_question",
            session_id=st.session_state.session_id,
            summary_data={
                "total_questions": stats.total_questions,
                "correct": stats.get_total_correct(),
                "percentage": percentage
            }
        )
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Ricomincia da capo", use_container_width=True):
            engine.reset()
            st.session_state.feedback_message = None
            st.session_state.session_id = generate_session_id()
            st.session_state.app_mode = "single_question_quiz"
            st.rerun()
    
    with col2:
        if st.button("🏠 Torna alla Home", use_container_width=True):
            st.session_state.active_engine = None
            st.session_state.feedback_message = None
            st.session_state.app_mode = "home"
            st.rerun()


# ============================================================================
# MODALITÀ 2: QUIZ COMPLETO
# ============================================================================

def show_complete_quiz_setup():
    """Setup per quiz completo"""
    st.title("📝 Quiz Completo")
    st.markdown("Seleziona **un solo modulo** per il quiz completo.")
    
    available_quizzes = st.session_state.quiz_loader.get_available_quizzes()
    
    if not available_quizzes:
        st.error("Nessun quiz disponibile")
        if st.button("Torna alla home"):
            st.session_state.app_mode = "home"
            st.rerun()
        return
    
    selected_file = st.selectbox(
        "Seleziona il modulo:",
        options=[q["file"] for q in available_quizzes],
        format_func=lambda x: next(q["name"] for q in available_quizzes if q["file"] == x)
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Inizia Quiz"):
            questions = st.session_state.quiz_loader.load_quiz(selected_file)
            st.session_state.active_engine = CompleteQuizEngine(questions)
            st.session_state.selected_quiz_file = selected_file
            st.session_state.app_mode = "complete_quiz"
            st.session_state.session_id = generate_session_id()
            st.rerun()
    
    with col2:
        if st.button("Annulla"):
            st.session_state.app_mode = "home"
            st.rerun()


def show_complete_quiz():
    """Mostra il quiz completo (tutte le domande insieme)"""
    engine = st.session_state.active_engine
    
    if engine is None:
        st.error("Errore: engine non inizializzato")
        return
    
    st.title("📝 Quiz Completo")
    
    questions = engine.get_all_questions()
    
    st.info(f"Rispondi a tutte le {len(questions)} domande e poi clicca 'Invia Risposte' per vedere il risultato.")
    
    # Mostra tutte le domande
    for idx, question in enumerate(questions):
        st.markdown(f"### Domanda {idx + 1}")
        st.write(question["domanda"])
        
        # Recupera risposta salvata se presente
        saved_answer = engine.get_saved_answer(question["question_id"])
        default_idx = question["opzioni"].index(saved_answer) if saved_answer in question["opzioni"] else 0
        
        answer = st.radio(
            "Seleziona la risposta:",
            options=question["opzioni"],
            key=f"complete_q_{question['question_id']}",
            index=default_idx if saved_answer else None
        )
        
        # Salva la risposta
        engine.save_answer(question["question_id"], answer)
        
        st.markdown("---")
    
    # Progress
    answered_count = engine.get_answered_count()
    st.progress(answered_count / len(questions) if len(questions) > 0 else 0)
    st.caption(f"Domande risposte: {answered_count}/{len(questions)}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Invia Risposte", use_container_width=True, type="primary"):
            st.session_state.app_mode = "complete_results"
            st.rerun()
    
    with col2:
        if st.button("🏠 Annulla", use_container_width=True):
            st.session_state.active_engine = None
            st.session_state.app_mode = "home"
            st.rerun()


def show_complete_quiz_results():
    """Mostra i risultati del quiz completo"""
    engine = st.session_state.active_engine
    result = engine.evaluate()
    
    st.title("📊 Risultati Quiz Completo")
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Totale domande", result.total_questions)
    col2.metric("Risposte corrette", result.correct_answers)
    col3.metric("Percentuale", f"{result.score_percentage:.1f}%")
    
    # Mostra dettaglio domande
    st.markdown("---")
    st.subheader("Dettaglio risposte")
    
    for idx, q_result in enumerate(result.question_results):
        with st.expander(f"Domanda {idx + 1} - {'✅ Corretta' if q_result['is_correct'] else '❌ Errata'}"):
            st.write(f"**Domanda:** {q_result['domanda']}")
            st.write(f"**La tua risposta:** {q_result['user_answer']}")
            if not q_result['is_correct']:
                st.write(f"**Risposta corretta:** {q_result['correct_answer']}")
            
            # Log risposta
            if is_authenticated(st.session_state):
                user = get_current_user(st.session_state)
                st.session_state.quiz_logger.log_answer(
                    username=user.username,
                    quiz_mode="complete",
                    module_name=st.session_state.get("selected_quiz_file", "unknown"),
                    question_id=q_result['question_id'],
                    user_answer=q_result['user_answer'],
                    correct_answer=q_result['correct_answer'],
                    is_correct=q_result['is_correct'],
                    session_id=st.session_state.session_id
                )
    
    # Log session summary
    if is_authenticated(st.session_state):
        user = get_current_user(st.session_state)
        st.session_state.quiz_logger.log_session_summary(
            username=user.username,
            quiz_mode="complete",
            session_id=st.session_state.session_id,
            summary_data={
                "total_questions": result.total_questions,
                "correct": result.correct_answers,
                "percentage": result.score_percentage
            }
        )
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Ricomincia", use_container_width=True):
            engine.reset()
            st.session_state.session_id = generate_session_id()
            st.session_state.app_mode = "complete_quiz"
            st.rerun()
    
    with col2:
        if st.button("🏠 Torna alla Home", use_container_width=True):
            st.session_state.active_engine = None
            st.session_state.app_mode = "home"
            st.rerun()


# ============================================================================
# MODALITÀ 3: SIMULAZIONE ESAME
# ============================================================================

def show_exam_setup():
    """Setup per simulazione esame"""
    st.title("⏱️ Simulazione Esame")
    st.markdown("Seleziona uno o più moduli. Per ogni modulo verranno estratte 15 domande random con 15 minuti di tempo.")
    
    available_quizzes = st.session_state.quiz_loader.get_available_quizzes()
    
    if not available_quizzes:
        st.error("Nessun quiz disponibile")
        if st.button("Torna alla home"):
            st.session_state.app_mode = "home"
            st.rerun()
        return
    
    selected_files = st.multiselect(
        "Seleziona i moduli per l'esame:",
        options=[q["file"] for q in available_quizzes],
        format_func=lambda x: next(q["name"] for q in available_quizzes if q["file"] == x)
    )
    
    if selected_files:
        st.info(f"Saranno estratte 15 domande per {len(selected_files)} modulo/i = {15 * len(selected_files)} domande totali")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Inizia Esame", disabled=len(selected_files) == 0):
            # Carica i moduli
            modules_data = st.session_state.quiz_loader.load_multiple_quizzes(selected_files)
            
            try:
                st.session_state.active_engine = ExamEngine(modules_data)
                st.session_state.app_mode = "exam_quiz"
                st.session_state.session_id = generate_session_id()
                # Avvia il primo modulo
                st.session_state.active_engine.start_current_module()
                st.rerun()
            except ValueError as e:
                st.error(f"Errore: {str(e)}")
    
    with col2:
        if st.button("Annulla"):
            st.session_state.app_mode = "home"
            st.rerun()


def show_exam_quiz():
    """Mostra la simulazione d'esame"""
    exam_engine = st.session_state.active_engine
    
    if exam_engine is None:
        st.error("Errore: engine non inizializzato")
        return
    
    module_engine = exam_engine.get_current_module()
    
    if module_engine is None:
        # Esame terminato
        show_exam_results()
        return
    
    # Header con info modulo
    progress = exam_engine.get_exam_progress()
    st.title(f"⏱️ Esame - Modulo {progress['current_module']}/{progress['total_modules']}")
    st.subheader(f"📚 {module_engine.module_name}")
    
    # Timer
    remaining_seconds = module_engine.get_remaining_seconds()
    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60
    
    timer_col1, timer_col2 = st.columns([3, 1])
    
    with timer_col1:
        st.progress(1 - (remaining_seconds / module_engine.TIME_LIMIT_SECONDS))
    
    with timer_col2:
        if remaining_seconds > 60:
            st.metric("⏱️ Tempo", f"{minutes}:{seconds:02d}")
        else:
            st.error(f"⏱️ {minutes}:{seconds:02d}")
    
    # Verifica scadenza tempo
    if module_engine.is_time_expired():
        st.error("⏰ Tempo scaduto!")
        result = exam_engine.finish_current_module()
        
        # Log
        if is_authenticated(st.session_state):
            user = get_current_user(st.session_state)
            st.session_state.quiz_logger.log_session_summary(
                username=user.username,
                quiz_mode="exam",
                session_id=st.session_state.session_id,
                summary_data={
                    "module": result.module_name,
                    "score": result.score_percentage,
                    "time_expired": True
                }
            )
        
        st.markdown("---")
        st.subheader("📊 Risultato Modulo")
        col1, col2 = st.columns(2)
        col1.metric("Risposte corrette", f"{result.correct_answers}/{result.total_questions}")
        col2.metric("Percentuale", f"{result.score_percentage:.1f}%")
        
        has_next = exam_engine.next_module()
        
        col1, col2 = st.columns(2)
        
        if has_next:
            with col1:
                if st.button("▶️ Prossimo Modulo", use_container_width=True):
                    exam_engine.start_current_module()
                    st.rerun()
        
        with col2 if has_next else col1:
            if st.button("🛑 Termina Esame", use_container_width=True):
                st.session_state.app_mode = "exam_final_results"
                st.rerun()
        
        return
    
    # Domanda corrente
    question = module_engine.get_current_question()
    
    if question is None:
        st.error("Errore nel caricamento della domanda")
        return
    
    st.markdown(f"### Domanda {question['question_number']}/{question['total_questions']}")
    st.write(question["domanda"])
    
    # Recupera risposta salvata
    saved_answer = module_engine.get_saved_answer(module_engine.current_question_idx)
    
    answer = st.radio(
        "Seleziona la risposta:",
        options=question["opzioni"],
        key=f"exam_q_{question['question_id']}",
        index=question["opzioni"].index(saved_answer) if saved_answer in question["opzioni"] else 0
    )
    
    # Pulsanti navigazione
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if module_engine.current_question_idx > 0:
            if st.button("⬅️ Precedente", use_container_width=True):
                module_engine.previous_question()
                st.rerun()
    
    with col2:
        if st.button("💾 Salva", use_container_width=True):
            module_engine.save_current_answer(answer)
            
            # Log risposta
            if is_authenticated(st.session_state):
                user = get_current_user(st.session_state)
                is_correct = answer.strip().lower() == question["risposta_corretta"].strip().lower()
                st.session_state.quiz_logger.log_answer(
                    username=user.username,
                    quiz_mode="exam",
                    module_name=module_engine.module_name,
                    question_id=question["num_domanda"],
                    user_answer=answer,
                    correct_answer=question["risposta_corretta"],
                    is_correct=is_correct,
                    session_id=st.session_state.session_id
                )
            
            st.success("Risposta salvata!")
            time.sleep(0.3)
            st.rerun()
    
    with col3:
        has_next = module_engine.current_question_idx < len(module_engine.questions) - 1
        
        if has_next:
            if st.button("➡️ Successiva", use_container_width=True):
                module_engine.save_current_answer(answer)
                module_engine.next_question()
                st.rerun()
        else:
            if st.button("✅ Termina Modulo", use_container_width=True, type="primary"):
                module_engine.save_current_answer(answer)
                result = exam_engine.finish_current_module()
                st.rerun()
    
    # Mappa domande
    st.markdown("---")
    st.caption("Mappa domande:")
    
    cols = st.columns(15)
    for i in range(len(module_engine.questions)):
        with cols[i % 15]:
            is_answered = module_engine.get_saved_answer(i) is not None
            is_current = i == module_engine.current_question_idx
            
            label = "🟢" if is_answered else "⚪"
            if is_current:
                label = "🔵"
            
            if st.button(label, key=f"goto_{i}", help=f"Domanda {i+1}"):
                module_engine.go_to_question(i)
                st.rerun()
    
    # Auto-refresh per aggiornare timer
    time.sleep(1)
    st.rerun()


def show_exam_results():
    """Mostra i risultati finali dell'esame (chiamato quando non ci sono più moduli)"""
    st.session_state.app_mode = "exam_final_results"
    st.rerun()


def show_exam_final_results():
    """Mostra la schermata finale dell'esame"""
    exam_engine = st.session_state.active_engine
    final_results = exam_engine.get_final_results()
    
    st.title("🎓 Risultati Finali Esame")
    
    st.markdown("---")
    
    # Risultati generali
    col1, col2 = st.columns(2)
    col1.metric("Punteggio medio", f"{final_results.total_score_percentage:.1f}%")
    
    total_minutes = final_results.total_time_spent_seconds // 60
    col2.metric("Tempo totale", f"{total_minutes} minuti")
    
    st.markdown("---")
    st.subheader("Risultati per modulo")
    
    for result in final_results.module_results:
        with st.expander(f"📚 {result.module_name}"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Corrette", f"{result.correct_answers}/{result.total_questions}")
            col2.metric("Percentuale", f"{result.score_percentage:.1f}%")
            minutes = result.time_spent_seconds // 60
            col3.metric("Tempo", f"{minutes} min")
    
    # Log final summary
    if is_authenticated(st.session_state):
        user = get_current_user(st.session_state)
        st.session_state.quiz_logger.log_session_summary(
            username=user.username,
            quiz_mode="exam",
            session_id=st.session_state.session_id,
            summary_data={
                "total_score": final_results.total_score_percentage,
                "modules": [
                    {"name": r.module_name, "score": r.score_percentage}
                    for r in final_results.module_results
                ]
            }
        )
    
    st.markdown("---")
    
    if st.button("🏠 Torna alla Home", use_container_width=True):
        st.session_state.active_engine = None
        st.session_state.app_mode = "home"
        st.rerun()


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Funzione principale dell'app"""
    
    st.set_page_config(
        page_title="Quiz App",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Inizializza session state
    init_session_state()
    
    # Sidebar con logout
    with st.sidebar:
        st.title("⚙️ Menu")
        
        if is_authenticated(st.session_state):
            user = get_current_user(st.session_state)
            st.success(f"👤 {user.display_name}")
            
            if st.button("🚪 Logout"):
                logout_user(st.session_state)
                st.session_state.app_mode = "home"
                st.rerun()
        
        st.markdown("---")
        
        if st.button("🏠 Home"):
            st.session_state.app_mode = "home"
            st.session_state.active_engine = None
            st.rerun()
    
    # Routing basato su app_mode
    if not is_authenticated(st.session_state):
        # Se non autenticato, mostra login (opzionale - commentare per disabilitare auth)
        show_login_page()
        return
        
        # Se vuoi disabilitare l'autenticazione, usa direttamente il routing normale
        # pass
    
    # Routing
    if st.session_state.app_mode == "home":
        show_home_page()
    
    elif st.session_state.app_mode == "single_question_setup":
        show_single_question_setup()
    
    elif st.session_state.app_mode == "single_question_quiz":
        show_single_question_quiz()
    
    elif st.session_state.app_mode == "single_question_results":
        show_single_question_results()
    
    elif st.session_state.app_mode == "complete_setup":
        show_complete_quiz_setup()
    
    elif st.session_state.app_mode == "complete_quiz":
        show_complete_quiz()
    
    elif st.session_state.app_mode == "complete_results":
        show_complete_quiz_results()
    
    elif st.session_state.app_mode == "exam_setup":
        show_exam_setup()
    
    elif st.session_state.app_mode == "exam_quiz":
        show_exam_quiz()
    
    elif st.session_state.app_mode == "exam_final_results":
        show_exam_final_results()
    
    else:
        st.error(f"Modalità sconosciuta: {st.session_state.app_mode}")
        if st.button("Torna alla Home"):
            st.session_state.app_mode = "home"
            st.rerun()


if __name__ == "__main__":
    main()
