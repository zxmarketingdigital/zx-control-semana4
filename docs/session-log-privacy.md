# Session Log — Privacidade e Dados

## O que é registrado

Ao concluir a Semana 4, o sistema registra automaticamente uma sessão de aprendizado com os seguintes dados:

| Campo | Exemplo | Finalidade |
|-------|---------|------------|
| `date` | 2026-04-22 | Identificar quando foi concluído |
| `etapas_concluidas` | 9 | Quantas etapas foram executadas |
| `duration_minutes` | 87 | Duração estimada da sessão |
| `feedback` | "Muito bom!" | Feedback opcional do aluno |
| `platform` | Darwin | Sistema operacional |
| `checkpoints` | lista | Quais etapas foram marcadas como concluídas |

## O que NÃO é registrado

- Tokens de acesso (Supabase, APIs, etc.)
- Credenciais ou chaves de API
- Conteúdo das mensagens enviadas
- Dados de clientes ou leads
- Informações pessoais além do que está listado acima

## Onde os dados ficam

1. **Local** — `~/.operacao-ia/data/logs/` — formato JSON e Markdown, acessível apenas no seu computador
2. **Supabase** — banco de dados do seu projeto, configurado na Semana 1, sob seu controle total

## Controle total

O registro é feito na sua própria instância do Supabase. Você é o dono dos dados. O ZX LAB não tem acesso ao seu banco de dados.

Para desativar o envio ao Supabase, defina `disable_supabase_log: true` em `~/.operacao-ia/config.json`.

## Retenção

Não há política de expiração automática local. Os logs ficam em `~/.operacao-ia/data/logs/` até você os remover.
