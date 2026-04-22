---
name: ig-pausar
description: "Para o auto-responder do Instagram. Trigger: /ig-pausar"
model: haiku
effort: low
---

# /ig-pausar

Para o auto-responder do Instagram (LaunchAgent ou processo em background).

## Execucao

```bash
launchctl unload ~/Library/LaunchAgents/com.zxlab.ig-responder.plist
```

Para parar processo manual (se rodando em foreground):

```bash
pkill -f instagram_responder.py
```

## Para retomar

```bash
launchctl load ~/Library/LaunchAgents/com.zxlab.ig-responder.plist
```

Ou use `/ig-responder` para verificar e reiniciar.

## Observacoes

- O LaunchAgent recarrega automaticamente no próximo boot
- Para desabilitar permanentemente (não recarregar no boot):
  `launchctl disable gui/$(id -u)/com.zxlab.ig-responder`
- Logs em: `~/.operacao-ia/logs/week4/ig_responder.log`
