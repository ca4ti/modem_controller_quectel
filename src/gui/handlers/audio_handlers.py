# src/gui/handlers/audio_handlers.py
# Importações agora absolutas, assumindo que src está no sys.path
from src.gui.handlers.common_handlers import execute_modem_command, execute_modem_command_and_print_result
import src.gui.handlers.common_handlers as common_handlers # Importa o módulo para acessar as globais

def handle_set_volume_event(values):
    """Handler para o botão 'Definir Volume' (AT+CLVL)."""
    try:
        volume_level = int(values['-VOLUME-'])
        execute_modem_command(common_handlers.modem_controller.set_speaker_volume, volume_level)
    except ValueError:
        print("Erro: Nível de volume inválido. Use um valor entre 0 e 5.")

def handle_mute_mic_on_event():
    """Handler para o botão 'Mutar Microfone' (AT+CMUT=1)."""
    execute_modem_command(common_handlers.modem_controller.mute_microphone, True)

def handle_mute_mic_off_event():
    """Handler para o botão 'Desmutar Microfone' (AT+CMUT=0)."""
    execute_modem_command(common_handlers.modem_controller.mute_microphone, False)

def handle_loop_audio_on_event():
    """Handler para o botão 'Ativar Loop Áudio' (AT+QAUDLOOP=1)."""
    execute_modem_command(common_handlers.modem_controller.set_audio_loop_test, True)

def handle_loop_audio_off_event():
    """Handler para o botão 'Desativar Loop Áudio' (AT+QAUDLOOP=0)."""
    execute_modem_command(common_handlers.modem_controller.set_audio_loop_test, False)

def handle_set_audio_mode_event(values):
    """Handler para o botão 'Definir Modo Áudio' (AT+QAUDMOD)."""
    try:
        mode = int(values['-AUDIO_MODE_SET-'])
        execute_modem_command(common_handlers.modem_controller.set_audio_mode, mode)
    except ValueError:
        print("Erro: Modo de áudio deve ser um número inteiro (0, 1, 2 ou 3).")

def handle_get_audio_mode_event():
    """Handler para o botão 'Ler Modo Áudio' (AT+QAUDMOD?)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_audio_mode)

def handle_set_mic_gains_event(values):
    """Handler para o botão 'Definir Ganhos Mic' (AT+QMIC)."""
    try:
        txgain = int(values['-MIC_TXGAIN-'])
        txdgain_str = values['-MIC_TXDGAIN-'].strip()
        txdgain = int(txdgain_str) if txdgain_str.isdigit() else None
        execute_modem_command(common_handlers.modem_controller.set_mic_gains, txgain, txdgain)
    except ValueError:
        print("Erro: Ganhos do microfone (TxGain, TxDGain) devem ser números inteiros.")

def handle_get_mic_gains_event():
    """Handler para o botão 'Ler Ganhos Mic' (AT+QMIC?)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_mic_gains)

def handle_set_rx_gains_event(values):
    """Handler para o botão 'Definir Ganhos Rx' (AT+QRXGAIN)."""
    try:
        rxgain = int(values['-RX_GAIN-'])
        execute_modem_command(common_handlers.modem_controller.set_rx_gains, rxgain)
    except ValueError:
        print("Erro: Ganho de RX deve ser um número inteiro.")

def handle_get_rx_gains_event():
    """Handler para o botão 'Ler Ganhos Rx' (AT+QRXGAIN?)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_rx_gains)

def handle_config_dai_event(values):
    """Handler para o botão 'Configurar DAI' (AT+QDAI)."""
    try:
        io_mode = int(values['-DAI_IO-'])
        if io_mode == 1:
            audio_mode = int(values['-DAI_MODE-'])
            fsync = int(values['-DAI_FSYNC-'])
            clock = int(values['-DAI_CLOCK-'])
            audio_format = int(values['-DAI_FORMAT-'])
            sample = int(values['-DAI_SAMPLE-'])
            num_slots = int(values['-DAI_NUM_SLOTS-'])
            slot_mapping = int(values['-DAI_SLOT_MAP-'])
            execute_modem_command(common_handlers.modem_controller.config_dai, io_mode, audio_mode, fsync, clock, audio_format, sample, num_slots, slot_mapping)
        else:
            execute_modem_command(common_handlers.modem_controller.config_dai, io_mode)
    except ValueError:
        print("Erro: Verifique os valores de configuração DAI. Devem ser números inteiros.")
