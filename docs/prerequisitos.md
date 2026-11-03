# Pré-requisitos — ZX Control Semana 4

Antes de iniciar o Setup 4, confirme que todos os itens abaixo estão atendidos.

---

## 1. Nenhum setup anterior é necessário

Não exige setup anterior — se você já tem outro setup instalado, ele aproveita o que estiver válido.

A Etapa 1 cria o `~/.operacao-ia/config/config.json` mínimo se ele não existir (e, se estiver corrompido, guarda um backup `config.json.bak-<data>` e recria). Para ver quais campos existem hoje (sem exibir valores):

```bash
python3 -c "
import json, os
path = os.path.expanduser('~/.operacao-ia/config/config.json')
print(sorted(json.load(open(path))) if os.path.exists(path) else 'sem config.json — a Etapa 1 cria')
"
```

---

## 2. Claude Code CLI atualizado

```bash
claude --version
```

A versão deve ser recente (verifique em [claude.ai/code](https://claude.ai/code) qual é a atual). Se estiver desatualizado:

```bash
npm install -g @anthropic-ai/claude-code
```

---

## 3. Node.js >= 20

O plugin Codex requer Node.js na versão 20 ou superior.

```bash
node --version
```

Se não tiver ou a versão for inferior a 20:

- **macOS:** `brew install node` ou acesse [nodejs.org](https://nodejs.org)
- **Linux (Ubuntu/Debian):** `curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt-get install -y nodejs`
- **Windows:** baixe o instalador em [nodejs.org/en/download](https://nodejs.org/en/download)

---

## 4. Python 3.9+

```bash
python3 --version
```

Se a versão for inferior a 3.9:

- **macOS:** `brew install python@3.11`
- **Linux:** `sudo apt install python3.11`
- **Windows:** baixe em [python.org/downloads](https://python.org/downloads)

---

## 5. Git instalado

Necessário para a Etapa 4 (Skills e MCPs em Sync).

```bash
git --version
```

Se não estiver instalado:

- **macOS:** `xcode-select --install` (instala as ferramentas de linha de comando, inclui git)
- **Linux:** `sudo apt install git`
- **Windows:** [git-scm.com/download/win](https://git-scm.com/download/win)

---

## Resumo rápido

| Item | Comando de verificação | Mínimo |
|------|------------------------|--------|
| Setup anterior | — | não é necessário |
| Claude Code CLI | `claude --version` | versão atual |
| Node.js | `node --version` | v20.0.0+ |
| Python | `python3 --version` | 3.9+ |
| Git | `git --version` | qualquer |

Todos os itens OK? Digite `INICIAR SETUP SEMANA 4` no Claude para começar.
