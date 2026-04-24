# ZX Control — Semana 4: Visão Geral

## O que é

A Semana 4 finaliza a jornada de 30 dias do ZX Control com foco em **Inteligência & Escala**. O objetivo é transformar a operação individual em um sistema autônomo e escalável.

## Etapas (8 + encerramento)

| # | Etapa | O que faz |
|---|-------|-----------|
| 0 | Boas-vindas S4 | Orienta o aluno e valida pré-requisitos |
| 1 | Base S4 | Cria estrutura de diretórios e config base |
| 2 | Codex Revisor | Instala skill /codex-review + automação opt-in |
| 3 | Memória Unificada | Symlink Desktop ↔ Terminal |
| 4 | Skills & MCPs Sync | Registra e sincroniza skills/MCPs entre máquinas |
| 5 | Graphify | Economia de 60-90% tokens em projetos |
| 6 | Mission Control 2.0 | Adiciona widgets S4 ao dashboard diário |
| 7 | Auditoria S4 | 11 checks técnicos com auto-fix |
| 8 | Encerramento | Log Supabase + pitch ZX Control 2.0 |

## Fluxo de dados

```
Aluno executa setup_*.py
  └─> ~/.operacao-ia/config.json (atualizado com phase_completed=4)
  └─> ~/.codex/automations/project-review/ (configuração Codex)
  └─> ~/.operacao-ia/graphs/ (grafos Graphify)
  └─> ~/.operacao-ia/data/logs/ (session logs locais)
  └─> Supabase session_logs_s4 (via edge function)
```

## Pré-requisitos

- Semanas 1, 2 e 3 concluídas (`phase_completed >= 3` em config.json)
- Claude Code CLI instalado
- Supabase configurado (Semana 1)

## Comandos do dia a dia pós-S4

```bash
/graphify [projeto]    # mapear projeto no segundo cérebro
/status                # health check da operação
/diagnostico-360       # auditoria profunda
/prospectar            # buscar e disparar leads
```

## Repositório

`https://github.com/zxmarketingdigital/zx-control-semana4`
