# 🤖 Auto-Sender Vendas: Relatórios e Automação via WhatsApp

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

Um ecossistema de automação completo para equipes de vendas, projetado para enviar relatórios de desempenho, mensagens de parabéns por metas batidas e lembretes de incentivo, tudo de forma personalizada e automática via WhatsApp.

---

## 🧭 Navegação

* [Sobre o Projeto](#-sobre-o-projeto)
* [Funcionalidades Principais](#-funcionalidades-principais)
* [Tecnologias Utilizadas](#️-tecnologias-utilizadas)
* [Instalação e Configuração](#️-instalação-e-configuração)
* [Como Executar](#️-como-executar)
* [Agradecimentos](#-agradecimentos)
* [Licença](#-licença)

---

## 📖 Sobre o Projeto

Este projeto nasceu da necessidade de automatizar a comunicação de métricas e o engajamento de equipes de vendas. Ele consiste em um conjunto de scripts modulares em Python que leem dados de desempenho de uma planilha Excel, processam essas informações e enviam mensagens customizadas para cada vendedor.

O sistema é projetado para ser robusto, com gerenciamento de estado para evitar envios duplicados, logging detalhado para auditoria e uma arquitetura que separa a lógica do programa dos dados e templates, permitindo fácil manutenção.

---

## 🚀 Funcionalidades Principais

### Gestão de Dados
- **Carregamento Flexível:** Lê dados de planilhas Excel (`.xlsx`), permitindo especificar a aba de trabalho.
- **Limpeza e Padronização:** Formata automaticamente números de telefone para o padrão internacional (`+55...`) e extrai o primeiro nome dos vendedores para uma saudação pessoal.
- **Validação de Dados:** Verifica a existência de colunas obrigatórias e alerta sobre dados nulos, garantindo a integridade da execução.

### Comunicação Inteligente
- **Templates Customizáveis:** Utiliza arquivos de texto (`.txt`) para as mensagens, permitindo que o texto seja alterado sem tocar no código.
- **Mensagens Dinâmicas:** Substitui placeholders (ex: `{Nome}`, `{Meta}`) pelos dados reais de cada vendedor, criando relatórios únicos.
- **Gerenciamento de Estado:** Mantém um histórico (`.json`) de envios diários para cada script, garantindo que a mesma mensagem (relatório, parabéns ou lembrete) não seja enviada duas vezes para a mesma pessoa no mesmo dia.

### Robustez e Monitoramento
- **Logging Detalhado:** Cria um arquivo de log diário (`.log`) registrando cada sucesso, falha ou aviso, essencial para depuração e auditoria.
- **Sistema de Retry:** Tenta reenviar uma mensagem até 3 vezes em caso de falha de conexão, aumentando a taxa de sucesso.
- **Feedback Visual:** Exibe uma barra de progresso (`tqdm`) no terminal, informando o status do processo de envio em tempo real.



## 🛠️ Tecnologias Utilizadas

* **Python 3.8+**
* **Pandas:** Para leitura e manipulação de dados da planilha.
* **PyWhatKit:** Para a automação do envio de mensagens via WhatsApp Web.
* **Openpyxl:** Como motor para o Pandas ler arquivos `.xlsx`.
* **tqdm:** Para a criação da barra de progresso no terminal.
* **PySimpleGUI:** (Opcional) Para a criação do painel de controle gráfico.

---

## ⚙️ Instalação e Configuração

Siga estes passos para configurar o ambiente e executar o projeto.

### 1. Pré-requisitos
* Python 3.8 ou superior instalado.
* Uma conta do WhatsApp ativa e conectada ao **WhatsApp Web** no seu navegador padrão.

### 2. Passos de Instalação
```bash
# 1. Clone ou baixe este repositório para sua máquina local.
# Ex: git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
# cd MensagemVendedores

# 2. Crie e ative um ambiente virtual (altamente recomendado)
python -m venv venv

# No Windows
.\venv\Scripts\activate

# No macOS/Linux
source venv/bin/activate

# 3. Instale todas as dependências com um único comando
pip install -r requirements.txt
3. Configuração dos Arquivos
data/contatosvendedores.xlsx: Preencha esta planilha com os dados da sua equipe. Garanta que a aba de trabalho e os nomes das colunas correspondem ao que está definido na classe Config dos scripts.

templates/*.txt: Revise e ajuste os textos nos arquivos de template para que se adequem à sua comunicação.

▶️ Como Executar
Com o ambiente virtual ativado e os arquivos configurados, execute o script desejado a partir da pasta raiz do projeto:

Bash

# Para executar o script de envio de relatórios
python EnviarMensagemVendedores.py

# Para executar o script de envio de parabéns
python EnviarParabens.py
Aguarde a abertura do WhatsApp Web e o envio automático das mensagens. O progresso será exibido no terminal.

🤝 Agradecimentos

Este projeto foi desenvolvido por Vinicius Xavier de Lima com conhecimento tecnicos e também VIBE CODING

