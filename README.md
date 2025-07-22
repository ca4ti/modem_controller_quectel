# Quectel EC25 - Painel de Controle AT

[![Python 3.x](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![PySimpleGUI](https://img.shields.io/badge/GUI-PySimpleGUI-green.svg)](https://pysimplegui.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Este projeto oferece uma **Interface Gráfica de Usuário (GUI)** intuitiva para interagir e controlar o modem Quectel EC25 (e possivelmente outros modems compatíveis com comandos AT) via porta serial. Ele foi projetado para facilitar testes, configurações e monitoramento de diversas funcionalidades do modem.

## 🚀 Funcionalidades Principais

O Painel de Controle AT abrange uma ampla gama de funcionalidades do modem Quectel EC25, organizadas em abas para uma navegação facilitada:

### Conexão e Controle Básico
* **Conexão Serial**: Permite conectar e desconectar do modem, selecionar a porta serial disponível e configurar o baudrate.
* **Controle do Modem**: Inclui opções para desligar o modem de forma segura (`AT+QPOWD`), reiniciar (`AT+CFUN=1,1`), e resetar para os padrões de fábrica (`AT&F`). Um botão "Ligar Modem (Hardware)" serve como lembrete visual para ações físicas necessárias.
* **Configuração de URCs**: Permite definir e ler a porta de saída para Unsolicited Result Codes (URCs) (`AT+QURCCFG="urcport"`).

### Informações e Status do Modem
* **Identificação**: Obtém informações de identificação do produto (`ATI`), IMEI (`AT+CGSN`), IMSI do SIM (`AT+CIMI`), e ICCID do SIM (`AT+QCCID`).
* **Monitoramento**: Consulta o status e nível de carga da bateria (`AT+CBC`), a hora e data do relógio interno do modem (`AT+CCLK`), e lê valores de voltagem de canais ADC (`AT+QADC`).
* **Status do SIM**: Verifica o status de inserção do cartão (U)SIM (`AT+QSIMSTAT`).

### Rede e APN
* **Qualidade de Sinal**: Obtém a qualidade do sinal (RSSI e BER) (`AT+CSQ`).
* **Informações de Rede**: Consulta informações detalhadas da rede (tecnologia, operador, banda, canal) (`AT+QNWINFO`).
* **Registro na Rede**: Verifica o status de registro na rede (`AT+CREG?`).
* **Configuração de APN**: Permite definir contextos PDP (APN, tipo PDP, compressão) (`AT+CGDCONT`), ativar e desativar contextos PDP (`AT+CGACT`), e obter o endereço IP atribuído (`AT+CGPADDR`).
* **Bandas de Frequência**: Configura e lê as bandas de frequência preferenciais (GSM, WCDMA, LTE, TD-SCDMA) (`AT+QCFG="band"`).
* **Modo de Varredura de Rede**: Define e lê o modo de varredura de rede (2G/3G/4G/Automático) (`AT+QCFG="nwscanmode"`).
* **Serviço de Roaming**: Habilita ou desabilita o serviço de roaming (`AT+QCFG="roamservice"`).

### Serviço de Mensagens (SMS)
* **Envio de SMS**: Envia mensagens SMS (`AT+CMGS`).
* **Leitura de SMS**: Lê todas as mensagens SMS da memória (`AT+CMGL="ALL"`) ou uma mensagem específica por índice (`AT+CMGR`).
* **Gerenciamento de SMS**: Apaga todas as mensagens SMS (`AT+CMGD=1,4`) ou uma mensagem específica por índice (`AT+CMGD`).
* **Gerenciamento Avançado de SMS**: Inclui funcionalidade para "Inbox" e "Outbox" visual.

### Serviço de Chamadas
* **Controle de Chamadas**: Permite fazer chamadas de voz (`ATD`), atender chamadas recebidas (`ATA`), e desligar chamadas (`ATH`).
* **Status de Chamadas**: Verifica o status de todas as chamadas ativas ou em espera (`AT+CLCC`).

### Controle de Áudio
* **Volume e Mudo**: Define o nível de volume do alto-falante (`AT+CLVL`) e muta/desmuta o microfone (uplink) durante uma chamada (`AT+CMUT`).
* **Teste de Áudio**: Ativa e desativa o teste de loop de áudio (`AT+QAUDLOOP`).
* **Modo de Áudio**: Define e lê o modo de áudio (Handset, Headset, Speaker) (`AT+QAUDMOD`).
* **Ganhos de Áudio**: Define e lê os ganhos do microfone (uplink) (`AT+QMIC`) e os ganhos do RX (downlink/volume do alto-falante) (`AT+QRXGAIN`).
* **Interface de Áudio Digital (DAI)**: Configura a Interface de Áudio Digital (DAI/PCM) para roteamento de áudio externo (`AT+QDAI`).

### GPS e Interfaces USB
* **Controle de GPS**: Ativa e desativa o módulo GPS (`AT+QGPS=1`, `AT+QGPS=0`).
* **Localização GPS**: Obtém a localização GPS atual (`AT+QGPSLOC?`).
* **Configuração de Porta NMEA GPS**: Define e lê a porta de saída NMEA do GPS (`AT+QGPSCFG="outport"`).
* **Configuração de USB**: Lê a configuração atual da interface USB do modem (`AT+QCFG="USBCFG"`).
* **Voz sobre USB (PCM)**: Habilita/desabilita a transferência de dados PCM (`AT+QPCMV`) e obtém seu status.

### Sumário do Modem
* **Relatório Completo**: Gera um sumário detalhado de todas as informações e status relevantes do modem em um só lugar.

### Comandos Personalizados
* **Envio Flexível**: Permite enviar comandos AT personalizados, com resposta esperada e timeout configuráveis.
* **Pesquisa de Comandos**: Inclui uma lista pesquisável de comandos AT do manual para facilitar o uso.

## ✨ Destaques da Arquitetura e Melhorias Atuais

Este projeto (`bkp8`) representa uma evolução significativa em relação a versões anteriores (`bkp_orig`/`bkp7`), com foco em modularidade, robustez e responsividade:

* **Modularização Aprimorada:** O código é estritamente organizado em módulos e subpacotes, tornando-o mais limpo e fácil de manter.
* **Comunicação Serial Centralizada:** A leitura da porta serial foi centralizada em uma única thread dentro do `ModemController`, resolvendo condições de corrida (`race conditions`) e problemas onde o monitor de URCs "roubava" dados das respostas de comandos.
* **Tratamento de Exceções Robusto:** Uso extensivo de `try-except` para maior resiliência da aplicação.
* **Comunicação Assíncrona (Threading):** Todas as operações do modem são executadas em threads separadas, garantindo que a interface gráfica não congele.
* **Sincronização de Threads:** Uso de `threading.Lock` para garantir acesso exclusivo e seguro à porta serial.
* **Parsers de Resposta Aprimorados:** Correções na lógica de parsing para comandos como IMEI, IMSI e Status do SIM (`AT+QSIMSTAT?`), garantindo que os dados sejam extraídos corretamente, mesmo em respostas multi-linha ou com eco de comando.
* **Gerador de Sumário Funcional:** Implementação completa do método `get_modem_summary` e seu manipulador na GUI.
* **Saída de Comandos Personalizados:** A exibição dos resultados dos comandos AT personalizados foi corrigida para aparecer no log principal da GUI.
* **Monitoramento de URCs Colaborativo:** O `UrcMonitor` agora recebe URCs do `ModemController` de forma controlada, garantindo o monitoramento em tempo real sem interferir nas respostas de comandos.

## ⚠️ Bugs e Limitações Atualmente Conhecidos (Não Resolvidos no Código)

Embora o código tenha evoluído significativamente, algumas limitações e bugs persistentes estão relacionadas a fatores externos ou a comportamentos específicos do hardware do modem:

* **`BrokenPipeError` em Conexões Iniciais:** Ocasionalmente, erros como `BrokenPipeError: [Errno 32] Broken pipe` podem ocorrer em algumas portas seriais (`/dev/ttyUSB0`). Isso geralmente indica um problema de nível de sistema operacional, driver, ou uma desconexão/uso indevido da porta por outro processo, e não é um bug no código da aplicação.
* **Configuração de Bandas (`AT+QCFG="band"`) para Desativar 4G (LTE):**
    * A tentativa de desativar o 4G usando `AT+QCFG="band","0x3FFFFFFF","0x0","0x0",0` resulta em `ERROR` do modem.
    * O manual do Quectel indica que `0x0` para o parâmetro de banda LTE significa "não alterar a banda de frequência LTE", e não "desabilitar".
    * Não há uma sintaxe simples ou documentada para desabilitar *todas* as bandas LTE via `AT+QCFG="band"`.
    * **Solução alternativa atual:** Use os comandos `AT+QCFG="nwscanmode",1,0` (2G apenas) e `AT+QCFG="nwscanmode",2,0` (3G apenas) para forçar o modem a operar nessas tecnologias, ou `AT+QCFG="nwscanseq",010203,0` para priorizar 2G/3G na busca de rede.
    * **Solução definitiva:** Requer contato com o suporte técnico da Quectel para uma sintaxe específica, um valor hexadecimal para desabilitação, ou uma atualização de firmware/MBN que suporte essa funcionalidade explicitamente.
* **`AT+CEER` retornando `ERROR`:** O comando `AT+CEER` (para obter o último erro detalhado) não está funcionando como esperado em alguns casos, retornando `ERROR` em vez de um diagnóstico. Isso impede a obtenção de códigos de erro mais granulares para depuração.
* **`+CSQ: 99,99` e "No Service":** Indica ausência total de sinal celular detectável pelo modem. Não é um erro de software ou configuração, mas um problema de hardware/ambiente (antena, cobertura, SIM).

## 🛠️ Pré-requisitos

* **Python 3.x**: Certifique-se de ter uma versão compatível do Python instalada.
* **Modem Quectel EC25**: Ou qualquer outro modem 4G/LTE compatível com o conjunto de comandos AT do Quectel EC25.
* **Drivers da Porta Serial**: Os drivers USB para o modem devem estar instalados corretamente no seu sistema operacional para que a porta serial virtual (ex: `COMx` no Windows, `/dev/ttyUSBx` no Linux) seja reconhecida.

## 📦 Instalação

1.  **Clone o repositório (ou crie a pasta do projeto):**
    ```bash
    git clone [https://github.com/seu_usuario/modem_controller.git](https://github.com/seu_usuario/modem_controller.git) # Substitua pelo URL real do seu repositório
    cd modem_controller_v2 # Entre na nova pasta do projeto
    ```
    *Se você está copiando os arquivos manualmente para uma nova pasta, certifique-se de que a estrutura `modem_controller_v2/src/...` e `modem_controller_v2/resources/...` esteja correta.*

2.  **Crie e ative um ambiente virtual (opcional, mas altamente recomendado):**
    ```bash
    python -m venv venv
    # No Windows:
    .\venv\Scripts\activate
    # No macOS/Linux:
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 Uso

1.  **Conecte seu modem Quectel EC25 ao computador.**
    * Certifique-se de que o modem esteja ligado e os drivers estejam instalados.

2.  **Execute o script principal:**
    Navegue até a pasta raiz do projeto (`modem_controller_v2`):
    ```bash
    python -m src.main
    ```
    *Alternativamente:*
    ```bash
    python src/main.py
    ```

3.  **Na interface gráfica:**
    * **Porta Serial**: Selecione a porta serial correta na lista suspensa (ex: `/dev/ttyUSB2` ou `COMx`). Se a porta não aparecer, clique em "Atualizar Portas" ou tente "Auto-Discover".
    * **Baudrate**: Mantenha o valor padrão (`115200`), que é o usual para o EC25.
    * Clique em **"Conectar"** ou **"Auto-Discover"**.
    * Uma vez que a mensagem "Modem conectado e identificado (Quectel) com sucesso..." aparecer na área de saída, todos os outros botões de funcionalidade serão habilitados.
    * Explore as diferentes seções e funcionalidades. O campo de saída (`Output`) mostrará os comandos AT enviados, as respostas recebidas do modem e os URCs (eventos inesperados) em tempo real.

## Licença

MIT License

Copyright (c) 2025 Carlos Alberto

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Contato

Carlos Alberto - [Telefone/WhatsApp] +55 11 2615-2880
