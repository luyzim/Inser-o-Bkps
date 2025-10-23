# Projeto de Inserção de Backups (bkpsOxizzed)

Este projeto é uma ferramenta de linha de comando (CLI) desenvolvida em Python para gerar configurações ou scripts textuais a partir de arquivos de template. O sistema permite ao usuário escolher um template, preencher as variáveis necessárias e gerar o conteúdo final, que é exibido no terminal.

## Funcionalidades

- **Seleção Interativa de Templates**: O script lista todos os templates `.txt` disponíveis no diretório `data/` e permite que o usuário escolha qual deles usar.
- **Preenchimento Dinâmico**: O sistema identifica automaticamente as variáveis (placeholders no formato `{variavel}`) dentro dos templates selecionados.
- **Coleta de Dados Unificada**: O usuário fornece os valores para todas as variáveis de uma só vez, e esses valores são aplicados a todos os templates escolhidos.
- **Geração em Massa (Opcional)**: Para templates específicos, o sistema oferece a opção de gerar uma saída agregada a partir de um segundo template.
- **Formatação Automática**: Os dados inseridos pelo usuário são automaticamente convertidos para maiúsculas e têm os espaços removidos para garantir a consistência.

## Como Usar

1.  **Pré-requisitos**:
    *   Python 3.x instalado.

2.  **Estrutura de Arquivos**:
    *   `main.py`: O script principal a ser executado.
    *   `data/`: Diretório que armazena os arquivos de template (`.txt`).

3.  **Execução**:
    *   Abra um terminal no diretório do projeto.
    *   Execute o comando:
        ```bash
        python main.py
        ```
    *   Siga as instruções no terminal:
        1.  Escolha o número do template principal que deseja usar.
        2.  Se aplicável, decida se deseja gerar uma saída em massa com um template agregado.
        3.  Preencha os valores para cada variável solicitada (ex: `{NOME_CLIENTE}`, `{IP_REDE}`, etc.).
        4.  O resultado final será impresso diretamente no console.

## Templates

O diretório `data/` contém os arquivos de texto que servem como base para a geração dos scripts. As variáveis dentro desses arquivos devem seguir o formato `{placeholder}`.

**Exemplo de um placeholder em um arquivo de template:**

```
hostname {NOME_DO_HOST}
!
interface GigabitEthernet0/1
 ip address {ENDERECO_IP} {MASCARA_REDE}
 description Link para {DESCRICAO_LINK}
```
