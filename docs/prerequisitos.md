# Pré-requisitos — ZX Control Semana 4

Antes de iniciar o Setup 4, confirme que todos os itens abaixo estão atendidos.

---

## 1. Semanas 1, 2 e 3 concluídas

O config gerado nas semanas anteriores deve estar presente. Para verificar:

```bash
python3 -c "
import json, os
path = os.path.expanduser('~/.operacao-ia/config/config.json')
data = json.load(open(path))
print('Phase completed:', data.get('phase_completed'))
"
```

Resultado esperado: `phase_completed: 3` (ou superior).

Se o arquivo não existir ou `phase_completed` for menor que 3, complete os setups anteriores antes de prosseguir.

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
| Semanas anteriores | `cat ~/.operacao-ia/config/config.json` | `phase_completed: 3` |
| Claude Code CLI | `claude --version` | versão atual |
| Node.js | `node --version` | v20.0.0+ |
| Python | `python3 --version` | 3.9+ |
| Git | `git --version` | qualquer |

Todos os itens OK? Digite `INICIAR SETUP SEMANA 4` no Claude para começar.
