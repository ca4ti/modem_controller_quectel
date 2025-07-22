# src/utils/threading_utils.py
import threading
import PySimpleGUI as sg

def _execute_command(func, *args, **kwargs):
    """Executa uma função (comando do modem) e imprime qualquer exceção."""
    try:
        func(*args, **kwargs)
    except Exception as e:
        print(f"Erro na execução do comando em thread: {e}")

def _execute_command_print_result(func, *args, **kwargs):
    """Executa uma função (comando do modem que retorna um resultado para ser impresso) e imprime qualquer exceção."""
    try:
        result = func(*args, **kwargs)
        if result is not None:
            print(result) 
    except Exception as e:
        print(f"Erro na execução do comando e impressão de resultado em thread: {e}")

def run_in_thread(func, *args, **kwargs):
    """Cria e inicia uma nova thread para executar uma função."""
    threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()

# Helper para enviar eventos de volta à thread principal da GUI
def gui_update_event(window, event_key, value):
    """Envia um evento para a janela PySimpleGUI da thread principal."""
    if window:
        window.write_event_value(event_key, value)
