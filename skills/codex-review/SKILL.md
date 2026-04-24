---
name: codex-review
description: "Revisa projeto atual com Codex sob demanda. Atalho para o plugin Codex ja instalado. Triggers: '/codex-review', 'revisar com codex', 'auditar com codex', 'rode uma revisao codex'."
model: sonnet
effort: medium
---

# Codex Review — Revisor Manual

## Quando usar
- Quando acabar uma feature importante e quiser segunda opiniao
- Antes de publicar/deployar algo critico
- Quando suspeitar de bug mas nao encontrar

## Como invocar
Execute `/codex:review` (comando do plugin `codex-plugin-cc`) sobre o projeto atual.
- Sem argumentos: revisa `$PWD`
- Com path: `codex review ~/projetos/<nome>`
- Com effort alto: anexe `--effort high` (consome mais tokens)

## Relatorio
- Gerado em `~/.codex/reviews/YYYY-MM-DD-<nome>.md`
- Inclui top-3 riscos, top-3 sugestoes, resumo executivo
