---
name: ig-responder
description: "Verifica status e inicia o auto-responder do Instagram. Trigger: /ig-responder"
model: haiku
effort: low
---

# /ig-responder

Verifica e inicia o auto-responder de comentários e DMs do Instagram.

## Execucao

```bash
python3 ~/.operacao-ia/scripts/instagram_responder.py --status
```

Para iniciar manualmente:

```bash
python3 ~/.operacao-ia/scripts/instagram_responder.py
```

## O que acontece

1. Verifica se o token do Instagram está válido (`ig_state.json`)
2. Busca comentários novos nos últimos posts
3. Responde comentários com a frase configurada
4. Busca DMs novos e responde com o template configurado
5. Registra no rate limiter para evitar bloqueios
6. Dorme 30 minutos e repete

## Observacoes

- O LaunchAgent `com.zxlab.ig-responder` já inicia automaticamente no boot
- Para verificar se está rodando: `launchctl list | grep ig-responder`
- Para parar: `/ig-pausar`
- Logs em: `~/.operacao-ia/logs/week4/ig_responder.log`

## Status do LaunchAgent

```bash
launchctl list com.zxlab.ig-responder
```
