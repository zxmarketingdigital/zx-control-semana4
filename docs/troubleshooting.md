# Troubleshooting — ZX Control Semana 4

Guia de problemas comuns e soluções rápidas.

---

## 1. Plugin Codex não instala

**Sintoma:** `claude plugin install` retorna "command not found" ou "unknown command".

**Causa:** Versão do Claude Code CLI desatualizada — o suporte a plugins foi adicionado em versões recentes.

**Solução:**

```bash
# Atualizar o Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Verificar versão após atualização
claude --version

# Tentar instalar novamente
claude plugin install codex
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

**Solução:** Execute o comando de symlink no Terminal nativo do macOS (não dentro de um IDE como VS Code ou Cursor):

```bash
# Abra o Terminal.app e execute:
ln -sf ~/.claude/MEMORY.md "$HOME/Library/Application Support/Claude/MEMORY.md"
```

Se ainda falhar, verifique se a pasta de destino existe:

```bash
ls "$HOME/Library/Application Support/Claude/"
# Se não existir, crie:
mkdir -p "$HOME/Library/Application Support/Claude/"
```

---

## 3. Token Instagram expirado (Etapa 7)

**Sintoma:** O auto-responder para de funcionar com erro `OAuthException` ou `Invalid OAuth access token`.

**Causa:** O token de longa duração expira após 60 dias.

**Solução:** Re-execute o script de setup do Instagram:

```bash
python3 ~/zx-control-semana4/setup/setup_instagram_app.py --refresh-token
```

O script vai guiar você pela renovação sem precisar reconfigurar tudo do zero.

Para verificar a validade do token atual:

```bash
python3 -c "
import json, os
cfg = json.load(open(os.path.expanduser('~/.operacao-ia/config/config.json')))
ig = cfg.get('instagram', {})
print('Token expira em:', ig.get('token_expires_at', 'desconhecido'))
"
```

---

## 4. Cron não executa (Etapa 7 — IG Cron)

**Sintoma:** O auto-responder do Instagram não roda automaticamente.

**Verificações:**

```bash
# Ver se o cron está registrado
crontab -l | grep ig_auto_responder

# Ver logs de execução
tail -50 ~/.openclaw/workspace/ig_cron.log

# Testar manualmente
python3 ~/.openclaw/workspace/scripts/ig_auto_responder.py --dry-run
```

**Causas comuns:**
- Path do Python no cron diferente do PATH do usuário — use `which python3` e coloque o caminho absoluto no cron
- Variáveis de ambiente ausentes — o cron não herda o PATH do shell

**Solução (path absoluto no cron):**

```bash
crontab -e
# Adicione no início do crontab:
PATH=/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin
```

---

## 5. Log não sobe para o Supabase (Etapa 10)

**Sintoma:** Sessão finalizada mas nenhum registro aparece na tabela `session_logs_s4`.

**Verificações:**

```bash
# 1. Verificar chaves no config
python3 -c "
import json, os
cfg = json.load(open(os.path.expanduser('~/.operacao-ia/config/config.json')))
sb = cfg.get('supabase', {})
print('URL:', sb.get('url', 'AUSENTE'))
print('Service key:', 'OK' if sb.get('service_key') else 'AUSENTE')
"

# 2. Verificar se há logs pendentes de retry
cat ~/.operacao-ia/logs/pending_push.json 2>/dev/null || echo "Sem pendentes"
```

**Solução:** Se a chave estiver ausente, re-execute a etapa de configuração:

```bash
python3 ~/zx-control-semana4/setup/setup_base_s4.py --reconfigure-supabase
```

O sistema faz retry automático de logs pendentes na próxima execução. Para forçar o retry manualmente:

```bash
python3 ~/zx-control-semana4/scripts/push_pending_logs.py
```

---

## 6. Rollback da Etapa 7 (remover cron do IG)

Se quiser desfazer o cron do Instagram sem perder outros crons:

```bash
# Remove apenas a linha do ig_auto_responder
crontab -l | grep -v ig_auto_responder | crontab -

# Confirmar remoção
crontab -l
```

Para rollback completo da Etapa 7 (remove config do Instagram):

```bash
python3 ~/zx-control-semana4/setup/setup_instagram_app.py --rollback
```

---

## Suporte adicional

Não encontrou seu problema aqui? Entre no grupo de alunos e descreva:
1. Em qual etapa ocorreu o erro
2. A mensagem de erro completa
3. Seu sistema operacional e versões (`python3 --version`, `node --version`, `claude --version`)
