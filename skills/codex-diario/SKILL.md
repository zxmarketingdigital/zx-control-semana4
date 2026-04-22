---
name: codex-diario
description: "Dispara revisao Codex manualmente nos projetos ativos. Trigger: /codex-diario"
model: haiku
effort: low
---

# /codex-diario

Dispara uma revisão Codex manual nos projetos ativos. Útil quando quiser uma análise fora do horário agendado.

## Execucao

```bash
python3 ~/zx-control-semana4/scripts/codex_runner.py --effort medium
```

## Opcoes

```bash
# Revisao rapida
python3 ~/zx-control-semana4/scripts/codex_runner.py --effort low

# Revisao profunda
python3 ~/zx-control-semana4/scripts/codex_runner.py --effort high

# Revisao de um projeto especifico
python3 ~/zx-control-semana4/scripts/codex_runner.py --project zx-control-s4

# Revisao de resgate (segundo olhar)
python3 ~/zx-control-semana4/scripts/codex_runner.py --rescue
```

## Agendamentos automaticos

O Codex ja roda automaticamente:
- Todo dia às 9h (effort: low)
- Toda segunda às 8h30 (effort: medium)
- Todo domingo às 22h (effort: high)

Logs em: `~/.codex/logs/`

## Verificar proxima execucao

```bash
launchctl list | grep codex
```
