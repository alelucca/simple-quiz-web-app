"""
Quiz App - Applicazione Streamlit per la fruizione di quiz interattivi
Supporta tre modalità:
1. Quiz domanda per domanda (con retry e tracking)
2. Quiz completo (tutte le domande insieme)
3. Simulazione esame (X domande per modulo con timer)

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
    """Mostra la pagina di login e registrazione"""
    st.title("🔐 Accesso")
    
    # Flag per evitare duplicazione durante autenticazione
    if "is_authenticating" not in st.session_state:
        st.session_state.is_authenticating = False
    
    # Tabs per login e registrazione
    tab1, tab2 = st.tabs(["Login", "Registrazione"])
    
    with tab1:
        st.subheader("Accedi con le tue credenziali")
        
        # Mostra spinner durante autenticazione
        if st.session_state.is_authenticating:
            with st.spinner("Autenticazione in corso..."):
                pass
            return

        # Form con attributi HTML per autocomplete del browser
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username", autocomplete="username")
            password = st.text_input("Password", type="password", key="login_password", autocomplete="current-password")
            submit = st.form_submit_button("Accedi")
            
            if submit:
                if not username or not password:
                    st.error("Inserisci username e password")
                else:
                    # Imposta flag per evitare duplicazione
                    st.session_state.is_authenticating = True
                    st.rerun()
    
    with tab2:
        st.subheader("Crea un nuovo account")        
        
        with st.form("register_form"):
            new_username = st.text_input(
                "Username", 
                key="register_username",
                help="Minimo 3 caratteri, solo lettere, numeri, underscore e trattino",
                autocomplete="username"
            )
            new_display_name = st.text_input(
                "Nome da visualizzare (opzionale)", 
                key="register_display_name",
                autocomplete="name"
            )
            new_password = st.text_input(
                "Password", 
                type="password", 
                key="register_password",
                help="Minimo 6 caratteri",
                autocomplete="new-password"
            )
            confirm_password = st.text_input(
                "Conferma Password", 
                type="password", 
                key="register_confirm_password",
                autocomplete="new-password"
            )
            register_submit = st.form_submit_button("Registrati")
            
            if register_submit:
                # Validazione
                if not new_username or not new_password:
                    st.error("Username e password sono obbligatori")
                elif new_password != confirm_password:
                    st.error("Le password non corrispondono")
                else:
                    # Registra utente
                    success, message = st.session_state.auth_manager.register_user(
                        new_username, 
                        new_password, 
                        new_display_name or new_username
                    )
                    
                    if success:
                        st.success(message)
                        st.info("Ora puoi effettuare il login con le tue credenziali!")
                        st.balloons()
                    else:
                        st.error(message)


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
        st.write("Domanda per domanda con feedback immediato")
        if st.button("Inizia", key="btn_single", width="stretch"):
            st.session_state.app_mode = "single_question_setup"
            st.rerun()
    
    with col2:
        st.markdown("### 📝 Quiz Completo")
        st.write("Rispondi a tutte le domande e ricevi il risultato finale")
        if st.button("Inizia", key="btn_complete", width="stretch"):
            st.session_state.app_mode = "complete_setup"
            st.rerun()
    
    with col3:
        st.markdown("### ⏱️ Simula Esame")
        st.write("Come se fossi in sede d'esame")
        if st.button("Inizia", key="btn_exam", width="stretch"):
            st.session_state.app_mode = "exam_setup"
            st.rerun()
    
    # Stats utente (se autenticato)
    # if user:
    #     st.markdown("---")
    #     st.subheader("📊 Le tue statistiche")
    #     stats = st.session_state.quiz_logger.get_user_stats(user.username)
        
    #     col1, col2, col3 = st.columns(3)
    #     col1.metric("Totale domande a cui hai risposto: ", stats["total_questions_answered"])
    #     col2.metric("Percentuale corrette", f"{stats['correct_rate']:.1f}%")
    #     col3.metric("Moduli affrontati", len(stats["modules_practiced"]))
        
    #     # Mostra statistiche per modulo
    #     if stats["modules_stats"]:
    #         st.markdown("---")
    #         st.subheader("📚 Statistiche per Modulo")
            
    #         for module_name, module_stats in stats["modules_stats"].items():
    #             with st.expander(f"📖 {module_name}"):
    #                 col1, col2, col3 = st.columns(3)
    #                 col1.metric("Domande totali", module_stats["total_questions"])
    #                 col2.metric("Risposte corrette", module_stats["correct_answers"])
    #                 col3.metric("Percentuale corrette", f"{module_stats['correct_rate']:.1f}%")

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
    
    st.markdown("**Seleziona uno o più moduli:**")
    selected_files = []
    
    # Mostra checkbox per ogni quiz disponibile
    for quiz in available_quizzes:
        if st.checkbox(quiz["name"], key=f"quiz_select_{quiz['file']}"):
            selected_files.append(quiz["file"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Inizia Quiz", disabled=len(selected_files) == 0):
            # Carica e unisci i quiz selezionati
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
    
    # Variabile per tracciare se stiamo mostrando una risposta
    if "showing_answer" not in st.session_state:
        st.session_state.showing_answer = False
    
    # Ottieni domanda corrente o prossima
    if st.session_state.showing_answer:
        # Se stiamo mostrando la risposta, rimaniamo sulla domanda corrente
        question = engine.questions[engine.current_question_idx] if engine.current_question_idx is not None else None
    elif not engine.is_current_question_completed():
        question = engine.questions[engine.current_question_idx] if engine.current_question_idx is not None else None
        if question is None:
            question = engine.get_next_question()
    else:
        question = engine.get_next_question()
        st.session_state.showing_answer = False
    
    #print("Question: ", question)
    
    if question is None:
        # Quiz terminato
        show_single_question_results()
        return
    
    # Mostra domanda e provenienza
    source = question["source_quiz"].replace("_final.json","")

    st.markdown("### Domanda")
    st.write(f"[{source}] - ", question["domanda"])
    
    st.markdown("### Opzioni")
    
    # Radio button per le opzioni
    answer = st.radio(
        "Seleziona la tua risposta:",
        index=None,
        options=question["opzioni"],
        disabled=st.session_state.showing_answer
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
        if st.button("✔️ Invia Risposta", width="stretch", disabled=st.session_state.showing_answer):
            is_correct, correct_answer = engine.check_answer(answer)
            
            # Log risposta
            # if is_authenticated(st.session_state):
            #     user = get_current_user(st.session_state)
            #     attempt_num = engine.attempts[engine.current_question_idx].num_attempts
            #     st.session_state.quiz_logger.log_answer(
            #         username=user.username,
            #         quiz_mode="single_question",
            #         module_name=question.get("source_quiz", "unknown"),
            #         question_id=question.get("cod_domanda","unknown"),
            #         user_answer=answer,
            #         correct_answer=correct_answer,
            #         is_correct=is_correct,
            #         attempt_number=attempt_num,
            #         session_id=st.session_state.session_id
            #     )
            
            if is_correct:
                st.session_state.feedback_message = f"✅ Corretto! Risposta: {correct_answer}"
                st.session_state.showing_answer = True
            else:
                st.session_state.feedback_message = f"❌ La risposta: {answer} è sbagliata. Riprova!"
            
            st.rerun()
    
    with col2:
        button_label = "➡️ Domanda Successiva" if st.session_state.showing_answer else "⏭️ Salta Domanda"
        if st.button(button_label, width="stretch"):
            if not st.session_state.showing_answer:
                engine.skip_question()
            st.session_state.feedback_message = None
            st.session_state.showing_answer = False
            st.rerun()
    
    with col3:
        if st.button("👁️ Mostra Risposta", width="stretch", disabled=st.session_state.showing_answer):
            correct = engine.show_answer()
            st.session_state.feedback_message = f"💡 La risposta corretta è: {correct}"
            st.session_state.showing_answer = True
            st.rerun()
    
    with col4:
        if st.button("🛑 Termina Quiz", width="stretch"):
            st.session_state.app_mode = "single_question_results"
            st.session_state.showing_answer = False
            st.rerun()


def show_single_question_results():
    """Mostra i risultati del quiz domanda per domanda"""
    engine = st.session_state.active_engine
    stats = engine.get_stats()
    
    st.title("📊 Risultati Quiz")
    
    # Riepilogo generale
    st.markdown("---")
    st.subheader("Riepilogo Generale")
    
    col1, col2, col3 = st.columns(3)
    
    total_attempted = stats.get_total_attempted()
    total_correct = stats.get_total_correct()
    
    with col1:
        st.metric("Totale domande lette", total_attempted)
    
    with col2:
        st.metric("Risposte corrette", total_correct)
    
    with col3:
        percentage = (total_correct / total_attempted * 100) if total_attempted > 0 else 0
        st.metric("Percentuale", f"{percentage:.1f}%")
    
    # Statistiche per modulo
    st.markdown("---")
    st.subheader("Statistiche per Modulo")
    
    if not stats.modules:
        st.info("Nessuna domanda completata")
    else:
        for module_name, module_stats in stats.modules.items():
            with st.expander(f"📖 {module_name}", expanded=True):
                # Metriche generali
                col1, col2, col3 = st.columns(3)
                col1.metric("Domande lette", module_stats.total_attempted)
                col2.metric("Risposte corrette", module_stats.get_total_correct())
                
                module_percentage = (module_stats.get_total_correct() / module_stats.total_attempted * 100) if module_stats.total_attempted > 0 else 0
                col3.metric("Percentuale", f"{module_percentage:.1f}%")
                
                # Dettaglio tentativi
                st.markdown("**Dettaglio tentativi:**")
                col1, col2 = st.columns(2)
                col1.metric("✅ Primo tentativo", module_stats.correct_first_try)
                col2.metric("🔄 Più tentativi", module_stats.correct_multiple_tries)
                
                # Altre info
                if module_stats.skipped > 0 or module_stats.shown > 0:
                    st.markdown("**Altro:**")
                    col1, col2 = st.columns(2)
                    col1.metric("⏭️ Domande saltate", module_stats.skipped)
                    col2.metric("👁️ Risposte mostrate", module_stats.shown)
    
    # Log session summary
    # if is_authenticated(st.session_state):
    #     user = get_current_user(st.session_state)
    #     st.session_state.quiz_logger.log_session_summary(
    #         username=user.username,
    #         quiz_mode="single_question",
    #         session_id=st.session_state.session_id,
    #         summary_data={
    #             "total_attempted": total_attempted,
    #             "correct": total_correct,
    #             "percentage": percentage
    #         }
    #     )
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Ricomincia da capo", width="stretch"):
            engine.reset()
            st.session_state.feedback_message = None
            st.session_state.session_id = generate_session_id()
            st.session_state.app_mode = "single_question_quiz"
            st.rerun()
    
    with col2:
        if st.button("🏠 Torna alla Home", width="stretch"):
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
    
    # Usa radio buttons per permettere solo una selezione
    quiz_names = [quiz["name"] for quiz in available_quizzes]
    quiz_files = {quiz["name"]: quiz["file"] for quiz in available_quizzes}
    
    selected_quiz_name = st.radio(
        "Seleziona il modulo:",
        options=quiz_names,
        index=None
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Inizia Quiz", disabled=selected_quiz_name is None):
            selected_file = quiz_files[selected_quiz_name]
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
        saved_answer = engine.get_saved_answer(question["cod_domanda"])
        default_idx = question["opzioni"].index(saved_answer) if saved_answer in question["opzioni"] else None
        
        answer = st.radio(
            "Seleziona la risposta:",
            options=question["opzioni"],
            index=default_idx,
            key=f"complete_quiz_q_{question['cod_domanda']}"
        )
        
        # Salva la risposta solo se non è None
        if answer is not None:
            engine.save_answer(question["cod_domanda"], answer)
        
        st.markdown("---")
    
    # Progress
    answered_count = engine.get_answered_count()
    st.progress(answered_count / len(questions) if len(questions) > 0 else 0)
    st.caption(f"Domande risposte: {answered_count}/{len(questions)}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Invia Risposte", width="stretch", type="primary"):
            st.session_state.app_mode = "complete_results"
            st.rerun()
    
    with col2:
        if st.button("🏠 Annulla", width="stretch"):
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
            # if is_authenticated(st.session_state):
            #     user = get_current_user(st.session_state)
            #     st.session_state.quiz_logger.log_answer(
            #         username=user.username,
            #         quiz_mode="complete",
            #         module_name=st.session_state.get("selected_quiz_file", "unknown"),
            #         question_id=q_result['cod_domanda'],
            #         user_answer=q_result['user_answer'],
            #         correct_answer=q_result['correct_answer'],
            #         is_correct=q_result['is_correct'],
            #         session_id=st.session_state.session_id
            #     )
    
    # Log session summary
    # if is_authenticated(st.session_state):
    #     user = get_current_user(st.session_state)
    #     st.session_state.quiz_logger.log_session_summary(
    #         username=user.username,
    #         quiz_mode="complete",
    #         session_id=st.session_state.session_id,
    #         summary_data={
    #             "total_questions": result.total_questions,
    #             "correct": result.correct_answers,
    #             "percentage": result.score_percentage
    #         }
    #     )
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Ricomincia", width="stretch"):
            engine.reset()
            st.session_state.session_id = generate_session_id()
            st.session_state.app_mode = "complete_quiz"
            st.rerun()
    
    with col2:
        if st.button("🏠 Torna alla Home", width="stretch"):
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
    
    # Mostra checkbox per ogni quiz disponibile
    selected_files=[]
    for quiz in available_quizzes:
        if st.checkbox(quiz["name"], key=f"quiz_select_{quiz['file']}"):
            selected_files.append(quiz["file"])    
    
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
    
    # Pulisci i risultati del modulo precedente all'inizio del quiz
    if "last_module_result" in st.session_state:
        st.session_state.last_module_result = None
    if "last_module_engine" in st.session_state:
        st.session_state.last_module_engine = None
    
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
    remaining_seconds = module_engine.get_remaining_seconds(module_engine.module_name)
    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60
    
    # Usa 3 colonne per sovrascrivere completamente i componenti della pagina precedente
    timer_col1, timer_col2, timer_col3 = st.columns([3, 1, 1])
    
    with timer_col1:
        # Clampa il valore tra 0 e 1 per evitare errori
        progress_value = max(0.0, min(1.0, 1 - (remaining_seconds / (module_engine.QUESTIONS_AND_TIMES_PER_MODULE[module_engine.module_name]*60))))
        st.progress(progress_value)
    
    with timer_col2:
        if remaining_seconds > 60:
            st.metric("⏱️ Tempo", f"{minutes}:{seconds:02d}")
        else:
            st.error(f"⏱️ {minutes}:{seconds:02d}")
    
    with timer_col3:
        # Colonna vuota per sovrascrivere eventuali componenti residui
        st.empty()
    
    # Verifica scadenza tempo
    if module_engine.is_time_expired(module_engine.module_name):
        st.error("⏰ Tempo scaduto!")
        result = exam_engine.finish_current_module()
        
        # Log
        # if is_authenticated(st.session_state):
        #     user = get_current_user(st.session_state)
        #     st.session_state.quiz_logger.log_session_summary(
        #         username=user.username,
        #         quiz_mode="exam",
        #         session_id=st.session_state.session_id,
        #         summary_data={
        #             "module": result.module_name,
        #             "score": result.score_percentage,
        #             "time_expired": True
        #         }
        #     )
        
        st.markdown("---")
        st.subheader("📊 Risultato Modulo")
        col1, col2 = st.columns(2)
        col1.metric("Risposte corrette", f"{result.correct_answers}/{result.total_questions}")
        col2.metric("Percentuale", f"{result.score_percentage:.1f}%")
        
        # Mostra dettaglio risposte
        st.markdown("---")
        st.subheader("📋 Dettaglio Risposte")
        
        for idx, question in enumerate(module_engine.questions):
            cod_domanda = question.get("cod_domanda", str(idx))
            user_answer = module_engine.user_answers.get(cod_domanda)
            correct_answer = question["risposta_corretta"]
            
            if user_answer is None or user_answer == "":
                is_correct = False
                user_answer_display = "(Non hai risposto)"
            else:
                is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
                user_answer_display = user_answer
            
            icon = "✅" if is_correct else "❌"
            status = "Corretto" if is_correct else "Errato"
            
            with st.expander(f"Domanda {idx + 1} - {icon} {status}"):
                st.write(f"**Domanda:** {question['domanda']}")
                st.write(f"**La tua risposta:** {user_answer_display}")
                st.write(f"**Risposta corretta:** {correct_answer}")
        
        st.markdown("---")
        has_next = exam_engine.next_module()
        
        col1, col2 = st.columns(2)
        
        if has_next:
            with col1:
                if st.button("▶️ Prossimo Modulo", width="stretch"):                    
                    exam_engine.start_current_module()
                    st.rerun()
        
        with col2 if has_next else col1:
            if st.button("🛑 Termina Esame", width="stretch"):
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
        index=None
    )
    
    # Pulsanti navigazione
    is_first_question = module_engine.current_question_idx == 0
    is_last_question = module_engine.current_question_idx == len(module_engine.questions) - 1
    
    # Layout colonne: 2 colonne se prima domanda, 3 se domanda intermedia
    if is_first_question:
        col1, col2 = st.columns([1, 1])
    else:
        col1, col2, col3 = st.columns([1, 1, 1])
    
    # Bottone Precedente solo se NON è la prima domanda
    if not is_first_question:
        with col1:
            if st.button("⬅️ Precedente", width="stretch"):
                module_engine.previous_question()
                st.rerun()
    
    # Bottone Invia: col1 se prima domanda, col2 altrimenti
    button_col = col1 if is_first_question else col2
    
    with button_col:
        if st.button("✔️ Invia", width="stretch", key="btn_invia_risposta"):
            module_engine.save_current_answer(answer)
            
            # Log risposta
            if is_authenticated(st.session_state):
                user = get_current_user(st.session_state)
                # Gestisce None nelle risposte
                if answer is None or answer == "":
                    is_correct = False
                else:
                    is_correct = answer.strip().lower() == question["risposta_corretta"].strip().lower()
                
                # st.session_state.quiz_logger.log_answer(
                #     username=user.username,
                #     quiz_mode="exam",
                #     module_name=module_engine.module_name,
                #     question_id=question["cod_domanda"],
                #     user_answer=answer if answer is not None else "(Non hai risposto)",
                #     correct_answer=question["risposta_corretta"],
                #     is_correct=is_correct,
                #     session_id=st.session_state.session_id
                # )
            
            # Passa automaticamente alla domanda successiva
            has_next = module_engine.current_question_idx < len(module_engine.questions) - 1
            if has_next:
                module_engine.next_question()
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
    
    # Bottone Termina Modulo solo all'ultima domanda: col2 se prima domanda, col3 altrimenti
    if is_last_question:
        last_button_col = col2 if is_first_question else col3
        
        with last_button_col:
            if st.button("✅ Termina Modulo", width="stretch", type="primary", key="btn_termina_modulo"):
                # print(f"[DEBUG] Termina Modulo clicked - Saving answer: {answer}")
                module_engine.save_current_answer(answer)
                
                # print(f"[DEBUG] Finishing current module...")
                result = exam_engine.finish_current_module()
                # print(f"[DEBUG] Module finished - Score: {result.score_percentage:.1f}%")
                
                # Salva il risultato in session state per mostrarlo
                st.session_state.last_module_result = result
                st.session_state.last_module_engine = module_engine
                
                # Log modulo completato
                # if is_authenticated(st.session_state):
                #     user = get_current_user(st.session_state)
                #     st.session_state.quiz_logger.log_session_summary(
                #         username=user.username,
                #         quiz_mode="exam",
                #         session_id=st.session_state.session_id,
                #         summary_data={
                #             "module": result.module_name,
                #             "score": result.score_percentage,
                #             "completed": True
                #         }
                #     )
                
                # Mostra i risultati del modulo
                st.session_state.app_mode = "exam_module_results"
                st.rerun()
        return
    
    # Auto-refresh per aggiornare timer (solo se non siamo all'ultima domanda)
    time.sleep(1)
    st.rerun()


def show_exam_module_results():
    """Mostra i risultati del modulo appena completato"""
    exam_engine = st.session_state.active_engine
    result = st.session_state.get("last_module_result")
    module_engine = st.session_state.get("last_module_engine")
    
    if result is None or module_engine is None:
        st.error("Errore: dati del modulo non trovati")
        st.session_state.app_mode = "exam_quiz"
        st.rerun()
        return
    
    st.title(f"📊 Risultato Modulo: {result.module_name}")
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Risposte corrette", f"{result.correct_answers}/{result.total_questions}")
    col2.metric("Percentuale", f"{result.score_percentage:.1f}%")
    minutes = result.time_spent_seconds // 60
    seconds = result.time_spent_seconds % 60
    col3.metric("Tempo impiegato", f"{minutes}:{seconds:02d}")
    
    # Mostra dettaglio risposte
    st.markdown("---")
    st.subheader("📋 Dettaglio Risposte")
    
    for idx, question in enumerate(module_engine.questions):
        cod_domanda = question.get("cod_domanda", str(idx))
        user_answer = module_engine.user_answers.get(cod_domanda)
        correct_answer = question["risposta_corretta"]
        
        if user_answer is None or user_answer == "":
            is_correct = False
            user_answer_display = "(Non hai risposto)"
        else:
            is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
            user_answer_display = user_answer
        
        icon = "✅" if is_correct else "❌"
        status = "Corretto" if is_correct else "Errato"
        
        with st.expander(f"Domanda {idx + 1} - {icon} {status}"):
            st.write(f"**Domanda:** {question['domanda']}")
            st.write(f"**La tua risposta:** {user_answer_display}")
            if not is_correct:
                st.write(f"**Risposta corretta:** {correct_answer}")
    
    st.markdown("---")
    
    # Verifica se ci sono altri moduli (l'indice è ancora sul modulo appena completato)
    has_next = exam_engine.current_module_idx < len(exam_engine.module_engines) - 1
    
    col1, col2 = st.columns(2)
    
    if has_next:
        with col1:
            if st.button("▶️ Prossimo Modulo", width="stretch", type="primary"):
                # Incrementa l'indice per passare al modulo successivo
                exam_engine.next_module()
                # Avvia il timer del prossimo modulo
                exam_engine.start_current_module()
                # Pulisci i risultati temporanei
                st.session_state.last_module_result = None
                st.session_state.last_module_engine = None
                st.session_state.app_mode = "exam_quiz"
                st.rerun()
    
    with col2 if has_next else col1:
        if st.button("🛑 Termina Esame", width="stretch"):
            st.session_state.app_mode = "exam_final_results"
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
    col1.metric("Risposte esatte su totale:", f"{final_results.total_correct} su {final_results.total_questions}")
    
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
    # if is_authenticated(st.session_state):
    #     user = get_current_user(st.session_state)
    #     st.session_state.quiz_logger.log_session_summary(
    #         username=user.username,
    #         quiz_mode="exam",
    #         session_id=st.session_state.session_id,
    #         summary_data={
    #             "total_score": final_results.total_score_percentage,
    #             "modules": [
    #                 {"name": r.module_name, "score": r.score_percentage}
    #                 for r in final_results.module_results
    #             ]
    #         }
    #     )
    
    st.markdown("---")
    
    if st.button("🏠 Torna alla Home", width="stretch"):
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
        
        st.markdown("---")        
        st.markdown("Segnala errori con [questo modulo](https://docs.google.com/forms/d/e/1FAIpQLSdD4ulcR7G87GMbYjEv4EsXgGX-aZvtYHsf_z3B0SxOOtaZlA/viewform?usp=dialog)")
    
        st.markdown("---")
        st.markdown("Sviluppata da Alessandro Lucca & Claude Sonnet")
        st.markdown("Contattami su [LinkedIn](https://www.linkedin.com/in/alessandro-lucca-1b110b214/)")
    
    # Gestione autenticazione in background
    if st.session_state.get("is_authenticating", False):
        # Esegui l'autenticazione
        if "login_username" in st.session_state and "login_password" in st.session_state:
            username = st.session_state.login_username
            password = st.session_state.login_password
            
            with st.spinner("Autenticazione in corso..."):
                user = st.session_state.auth_manager.authenticate(username, password)
                
            st.session_state.is_authenticating = False
            
            if user:
                login_user(st.session_state, user)
                st.success(f"Benvenuto, {user.display_name}!")
                st.rerun()
            else:
                st.error("Credenziali non valide")
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
    
    elif st.session_state.app_mode == "exam_module_results":
        show_exam_module_results()
    
    elif st.session_state.app_mode == "exam_final_results":
        show_exam_final_results()
    
    else:
        st.error(f"Modalità sconosciuta: {st.session_state.app_mode}")
        if st.button("Torna alla Home"):
            st.session_state.app_mode = "home"
            st.rerun()


if __name__ == "__main__":
    main()
