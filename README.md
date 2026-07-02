# Antigravity CLI Portable

Uma interface de linha de comando (CLI) portátil e interativa desenvolvida em Python para interagir de forma flexível com os agentes do ecossistema **Google Antigravity**.

## Requisitos

- Python 3.11.7 (conforme configurado no ambiente de desenvolvimento).
- Dependências instaladas (incluindo `google-antigravity`, `click`, `colorama`, `python-dotenv`).

## Instalação e Configuração

1. Certifique-se de estar com o ambiente virtual ativado:
   ```powershell
   .\.venv\Scripts\activate
   ```
2. Defina a chave de API do Gemini criando um arquivo `.env` na raiz do projeto:
   ```env
   GEMINI_API_KEY=sua_chave_de_api_aqui
   ```
   *(Ou passe via flag `--api-key` nas execuções).*

---

## Como Usar

### 1. Modo Prompt Único
Para enviar um prompt e receber a resposta diretamente:
```powershell
python main.py "Escreva uma saudação em Python"
```

### 2. Modo Interativo (REPL)
Para iniciar um chat contínuo com o agente (que mantém o histórico da sessão):
```powershell
python main.py
```
**Comandos úteis no Modo Interativo:**
- `/reset`: Limpa o histórico da conversa e redefine o contexto do agente.
- `/exit` ou `/quit`: Encerra o terminal interativo.

### 3. Modo Seguro (Safe Mode) vs Modo YOLO
- **Modo Seguro (Padrão)**: Sempre que o agente tentar executar comandos de terminal perigosos (como a ferramenta `RUN_COMMAND`), o CLI solicitará a sua permissão no console (`[y/N]`) antes de prosseguir.
- **Modo YOLO (`-y` / `--yolo`)**: Desativa todas as confirmações de segurança e executa todas as ações de forma autônoma.
  ```powershell
  python main.py -y "Crie uma pasta chamada teste e liste o diretório"
  ```

---

## Opções Disponíveis

Você pode personalizar o comportamento do CLI através de flags:

| Flag | Atalho | Descrição |
| :--- | :--- | :--- |
| `--model` | `-m` | Especifica o modelo do Gemini (padrão: `gemini-3.5-flash`). |
| `--yolo` | `-y` | Pula todas as permissões/confirmações e roda tudo livremente. |
| `--workspace` | `-w` | Restringe ferramentas de arquivos a um diretório específico (pode ser repetido). |
| `--system-instruction` | `-s` | Texto com instruções personalizadas de sistema ou o caminho de um arquivo de texto. |
| `--api-key` | | Informa a chave de API diretamente na linha de comando. |
| `--skills-path` | `-k` | Caminho para pastas de skills (pode ser repetido). Caso não informado e a pasta `./skills` exista, ela será carregada por padrão. |
| `--silent` | | Oculta os pensamentos internos e as chamadas de ferramentas no terminal. |
| `--verbose` | `-v` | Exibe os pensamentos internos de raciocínio da IA (Chain of Thought) em cinza no console. |

Exemplo de uso avançado:
```powershell
python main.py -m gemini-3.5-flash -y -s "Você é um assistente conciso que fala em espanhol" "Olá!"
```

---

## Personalização e Configurações (`.agents`)

A pasta `.agents` na raiz do seu projeto é a pasta de **Personalização Local do Workspace**. Através dela, você pode definir regras, criar novas habilidades ("skills") e customizar as respostas do agente.

### Estrutura Completa de `.agents`

```text
meu-projeto/
└── .agents/
    ├── AGENTS.md                  # Regras e diretrizes gerais do projeto
    ├── skills.json                # (Opcional) Configuração e registro de habilidades
    └── skills/                    # Pasta contendo habilidades específicas
        └── gerenciar_deploy/      # Exemplo de uma habilidade
            ├── SKILL.md           # Instruções e gatilhos da habilidade (Obrigatório)
            ├── scripts/           # Scripts de apoio
            ├── examples/          # Exemplos de uso/código
            └── references/        # Documentações de referência
```

### 1. Regras do Projeto (`AGENTS.md`)
O arquivo `.agents/AGENTS.md` define as regras gerais de comportamento, estilo e restrições técnicas que o agente deve seguir neste projeto (ex: padrão de código, idioma, frameworks preferidos).

*Há também o escopo global em `C:\Users\<usuario>\.gemini\config\AGENTS.md` para regras que valem para todo o computador.*

### 2. Habilidades (`skills/`)
As **Skills** são pacotes de comportamento e ferramentas carregados dinamicamente dependendo do contexto da conversa ou solicitação do usuário.

*   **O arquivo `SKILL.md` (Obrigatório)**:
    Define os metadados em YAML (usados pela IA para a ativação automática) e o corpo com as instruções da habilidade:
    ```markdown
    ---
    name: "Ferramentas Utilitárias de Desenvolvimento"
    description: "Útil para qualquer tarefa geral de desenvolvimento, automação, script ou consulta do workspace."
    ---

    # Instruções da Habilidade
    Sempre que o usuário solicitar uma automação ou execução de script:
    1. Analise o prompt e utilize as ferramentas em `scripts/` correspondentes.
    2. Explique o resultado da execução ao final.
    ```
*   **Scripts (`scripts/`)**:
    Qualquer script executável inserido na pasta `scripts/` será exposto automaticamente como uma ferramenta que o agente pode rodar (ex: `gerenciar_deploy.nome_do_script`).

### 3. Registro de Habilidades (`skills.json`)
O arquivo `skills.json` na raiz da pasta `.agents/` permite herdar habilidades de outros diretórios compartilhados ou desativar habilidades padrão:
```json
{
  "entries": [
    { "path": "caminho/para/skills/externas" }
  ],
  "exclude": [
    "nome_da_skill_para_ignorar"
  ]
}
```

---

## Personalidade e Instruções do Agente

A personalidade, o tom de voz e as diretrizes de comportamento do agente são resolvidos em múltiplos níveis de precedência:

1. **Flag de Inicialização (`-s` / `--system-instruction`)**:
   Define as instruções de sistema diretamente na execução do comando (texto livre ou caminho de arquivo).
2. **Regras Locais e Globais (`AGENTS.md`)**:
   Lidas a partir de `.agents/AGENTS.md` (local) e de `C:\Users\<usuario>\.gemini\config\AGENTS.md` (global).
3. **Instruções de Habilidades (`SKILL.md`)**:
   Mescladas ao contexto do chat quando a skill correspondente é ativada.
4. **Personalidade Padrão (Fallback)**:
   Se nenhuma instrução for fornecida, assume o perfil padrão do ecossistema Google Antigravity.

