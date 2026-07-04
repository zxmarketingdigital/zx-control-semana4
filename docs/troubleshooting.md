# Troubleshooting — ZX Control Semana 4

Guia de problemas comuns e soluções rápidas.

---

## 1. Plugin Codex não instala

**Sintoma:** `claude plugin install` retorna "command not found" ou "unknown command".

**Causa:** Versão do Claude Code CLI desatualizada — o suporte a plugins foi adicionado em versões recentes.

**Solução:**

O plugin Codex vive numa *marketplace* — o comando `claude plugin install` sozinho
NÃO baixa de uma URL. O fluxo correto tem **dois passos**:

```bash
# Atualizar o Claude Code CLI (se a versão for antiga)
npm install -g @anthropic-ai/claude-code
claude --version

# 1) Adicionar a marketplace do Codex (idempotente)
claude plugin marketplace add openai/codex-plugin-cc

# 2) Instalar o plugin a partir da marketplace
claude plugin install codex@openai-codex

# Conferir que instalou
claude plugin list
```

Se o problema persistir, verifique se o `npm` global está no PATH correto:

```bash
which claude
npm root -g
```

---

## 2. Symlink falha no macOS (Etapa 3 — Memória Unificada)

**Sintoma:** Erro de permissão ao criar symlink em `~/Library/Application Support/`.

**Causa:** SIP (System Integrity Protection) ou permissões de pasta no macOS.

**O que o script faz:** o `setup_memory_symlink.py` cria um symlink dentro de
`~/.claude/projects/` ligando a pasta de memória do Claude Desktop
(`-Users-<seu-usuario>-Documents-Claude/memory`) à pasta de memória do Claude
Terminal (`-Users-<seu-usuario>/memory`), unificando as duas fontes. Ele NÃO
mexe em `~/Library/Application Support/`.

**Solução:** re-execute o script no Terminal nativo do macOS (não dentro de um
IDE como VS Code ou Cursor):

```bash
python3 ~/zx-control-semana4/setup/setup_memory_symlink.py
```

O script é idempotente: se o symlink já existir e estiver correto, ele apenas
confirma e segue. Se a pasta de memória do Terminal ainda não existir, ele avisa
e pula sem travar.

---

## 3. Log não sobe para o Supabase (Etapa 8)

**Sintoma:** Sessão finalizada mas nenhum registro aparece na tabela `session_logs_s4`.

**Verificações:**

```bash
# 1. Verificar chaves no config (aceita formato plano OU aninhado)
python3 -c "
import json, os
cfg = json.load(open(os.path.expanduser('~/.operacao-ia/config/config.json')))
sb = cfg.get('supabase', {}) if isinstance(cfg.get('supabase'), dict) else {}
url = cfg.get('supabase_url') or sb.get('url')
key = cfg.get('supabase_anon_key') or sb.get('anon_key') or sb.get('service_key')
print('URL:', url or 'AUSENTE')
print('Key:', 'OK' if key else 'AUSENTE')
"

# 2. Verificar se há logs pendentes de retry
cat ~/.operacao-ia/logs/pending_push.json 2>/dev/null || echo "Sem pendentes"
```

**Solução:** Se a chave estiver ausente, confira o `config.json` gerado na
Semana 1 e preencha `supabase_url` + `supabase_anon_key` (ou o bloco aninhado
`supabase: { url, anon_key }`). O envio tolera os dois formatos.

O sistema faz retry automático de logs pendentes na próxima execução. Para forçar o retry manualmente:

```bash
python3 -c "
import sys, os
sys.path.insert(0, os.path.expanduser('~/zx-control-semana4/scripts'))
import lib, supabase_log_push
print(supabase_log_push.push_pending(lib.load_config()))
"
```

---

## Suporte adicional

Não encontrou seu problema aqui? Entre no grupo de alunos e descreva:
1. Em qual etapa ocorreu o erro
2. A mensagem de erro completa
3. Seu sistema operacional e versões (`python3 --version`, `node --version`, `claude --version`)
