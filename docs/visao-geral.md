# ZX Control — Semana 4: Visão Geral

## O que é

A Semana 4 finaliza a jornada de 30 dias do ZX Control com foco em **Inteligência & Escala**. O objetivo é transformar a operação individual em um sistema autônomo e escalável.

## Etapas (10 + encerramento)

| # | Etapa | O que faz |
|---|-------|-----------|
| 0 | Boas-vindas S4 | Orienta o aluno e valida pré-requisitos |
| 1 | Base S4 | Cria estrutura de diretórios e config base |
| 2 | Codex Revisor | Instala plugin Codex + agendadores automáticos |
| 3 | Memória Unificada | Symlink Desktop ↔ Terminal |
| 4 | Skills & MCPs Sync | Registra e sincroniza skills/MCPs entre máquinas |
| 5 | Graphify | Instala segundo cérebro e mapeia projetos ativos |
| 6 | Instagram App | Configura App Meta + token long-lived |
| 7 | Instagram Responder | Auto-responder comentários + DMs (LaunchAgent) |
| 8 | Mission Control 2.0 | Adiciona widgets S4 ao dashboard diário |
| 9 | Auditoria S4 | 15 checks técnicos com auto-fix |
| 10 | Encerramento | Log Supabase + pitch ZX Control 2.0 |

## Fluxo de dados

```
Aluno executa setup_*.py
  └─> ~/.operacao-ia/config.json (atualizado com phase_completed=4)
  └─> ~/.openclaw/workspace/.env (tokens Instagram)
  └─> ~/.openclaw/workspace/ig_state.json (estado Instagram)
  └─> ~/.codex/automations/project-review/ (configuração Codex)
  └─> ~/.operacao-ia/graphs/ (grafos Graphify)
  └─> ~/.operacao-ia/data/logs/ (session logs locais)
  └─> Supabase session_logs_s4 (via edge function)
```

## Pré-requisitos

- Semanas 1, 2 e 3 concluídas (`phase_completed >= 3` em config.json)
- Claude Code CLI instalado
- Conta Instagram Business ativa
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
