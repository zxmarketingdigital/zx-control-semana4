# ZX Control — Semana 4: Inteligência & Escala

> Módulo final da mentoria ZX Control. Transforma sua operação de IA em uma máquina inteligente e escalável.

## O que você vai construir

- **Codex Revisor Manual** — skill `/codex-review` chamável a qualquer hora + automação opt-in
- **Memória Unificada** — Claude Desktop + Terminal compartilhando a mesma memória
- **Skills + MCPs em Sync** — skills sincronizadas via git entre máquinas
- **Graphify — Economia de Tokens** — 60-90% menos tokens em perguntas sobre projetos
- **Mission Control 2.0** — painel atualizado com todas as semanas
- **Log de Sessão** — feedback automático para o Supabase

## Pré-requisitos

- Semanas 1, 2 e 3 do ZX Control concluídas
- Claude Code CLI instalado e autenticado
- Node.js >= 20 (para o plugin Codex)
- Python 3.9+
## Como usar

```bash
gh repo clone zxmarketingdigital/zx-control-semana4 ~/zx-control-semana4
cd ~/zx-control-semana4
claude
```

Ao abrir o Claude, aguarde a mensagem de boas-vindas e digite:

```
INICIAR SETUP SEMANA 4
```

O Claude conduz todo o setup — você não precisa digitar nenhum comando técnico.

## Estrutura

```
zx-control-semana4/
├── CLAUDE.md              # Instrutor automático (carregado pelo Claude)
├── setup/                 # 8 scripts de setup (Etapas 1-8)
├── scripts/               # Engines e helpers
├── templates/             # Templates de LaunchAgents, systemd, etc.
├── docs/                  # Documentação detalhada
└── sql/                   # Migrations Supabase
```

## Etapas

| # | Nome | Tempo estimado |
|---|------|----------------|
| 1 | Boas-vindas + Base | ~5 min |
| 2 | Codex — Skill manual + Automação opt-in | ~10 min |
| 3 | Memória Desktop ↔ Terminal | ~5 min |
| 4 | Skills e MCPs em Sync | ~10 min |
| 5 | Graphify — Economia de tokens + Velocidade | ~5 min |
| 6 | Mission Control 2.0 | ~5 min |
| 7 | Auditoria Técnica | ~5 min |
| 8 | Finalização + ZX Control 2.0 | ~10 min |

**Total estimado:** ~55 min

## Suporte

Problemas? Consulte `docs/troubleshooting.md` ou entre no grupo de alunos.

---
*ZX LAB — [zxlab.com.br](https://zxlab.com.br)*
