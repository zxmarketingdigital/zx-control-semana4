#!/usr/bin/env python3
"""
Etapa 7 — Instagram Auto-Responder + DM
Configura respostas automaticas para comentarios e DMs do Instagram.
"""

import getpass
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib import (
    CONFIG_PATH, PLATFORM, BASE_DIR, DATA_DIR, LOGS_DIR,
    IG_STATE_PATH, IG_ENV_PATH, now_iso, ensure_structure,
    load_config, save_config, mark_checkpoint, load_env_var,
    load_checkpoint,
)

STEP_KEY = "step_7_instagram_responder"
WORKSPACE_DIR = Path.home() / ".openclaw" / "workspace"
SCRIPTS_DIR_WS = WORKSPACE_DIR / "scripts"
IG_CONFIG_PATH = WORKSPACE_DIR / "ig_auto_config.json"
IG_RESPONDER_PATH = SCRIPTS_DIR_WS / "ig_auto_responder.py"
IG_TOKEN_MGR_PATH = SCRIPTS_DIR_WS / "ig_token_manager.py"
IG_CRON_LOG = WORKSPACE_DIR / "ig_cron.log"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ask(prompt, secret=False):
    """Lê entrada do usuario, com suporte a campos secretos."""
    full_prompt = f"  {prompt}: "
    if secret:
        value = getpass.getpass(full_prompt)
    else:
        try:
            value = input(full_prompt)
        except KeyboardInterrupt:
            print("\n  Operacao cancelada pelo usuario.")
            sys.exit(0)
    return value.strip()


def _step6_is_done():
    """Verifica se etapa 6 foi concluida."""
    cp = load_checkpoint()
    steps = cp.get("steps", {})
    entry = steps.get("step_6_instagram_app", {})
    return entry.get("status") == "done"


def _ig_state_is_valid():
    """Verifica se ig_state.json existe e token_valid == True."""
    if not IG_STATE_PATH.exists():
        return False
    try:
        state = json.loads(IG_STATE_PATH.read_text(encoding="utf-8"))
        return state.get("token_valid", False)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Passo 1 — Verificar Etapa 6
# ---------------------------------------------------------------------------

def _check_step6():
    if not _step6_is_done():
        print()
        print("  ATENCAO: Complete a Etapa 6 primeiro.")
        print("  Execute: python3 setup/setup_instagram_app.py")
        sys.exit(1)

    if not _ig_state_is_valid():
        print()
        print("  ATENCAO: ig_state.json nao encontrado ou token invalido.")
        print("  Execute novamente a Etapa 6: python3 setup/setup_instagram_app.py")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Passo 2 — Configurar respostas automaticas
# ---------------------------------------------------------------------------

def _build_default_config(keywords_str, reply_template):
    return {
        "comments": {
            "enabled": True,
            "keywords": [k.strip() for k in keywords_str.split(",") if k.strip()],
            "reply_template": reply_template,
            "delay_seconds": 30,
        },
        "dms": {
            "enabled": True,
            "welcome_message": (
                "Oi! Aqui eh o assistente automatico. Em breve um humano vai te atender. "
                "Pode me contar o que voce precisa?"
            ),
            "keywords_handoff": ["urgente", "ajuda", "problema", "nao funciona"],
        },
        "rate_limit": {
            "max_replies_per_hour": 20,
            "max_dms_per_hour": 10,
        },
    }


def _setup_ig_config():
    print()
    print("  --- Configurando respostas automaticas ---")
    print()

    default_keywords = "info,como funciona,preco,valor,quero,link"
    keywords_input = ask(
        f"Palavras-chave que ativam resposta [padrao: {default_keywords}]"
    )
    if not keywords_input:
        keywords_input = default_keywords

    default_reply = "Oi {name}! Manda uma DM que te explico tudo sobre {topic}"
    print(f"  Mensagem de resposta automatica padrao:")
    print(f"  \"{default_reply}\"")
    reply_input = ask("Cole sua mensagem ou pressione Enter para manter o padrao")
    if not reply_input:
        reply_input = default_reply

    config = _build_default_config(keywords_input, reply_input)

    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    IG_CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"  [OK] Configuracao salva em {IG_CONFIG_PATH}")
    return config


# ---------------------------------------------------------------------------
# Passo 3 — Criar script de auto-resposta
# ---------------------------------------------------------------------------

def _create_ig_auto_responder():
    SCRIPTS_DIR_WS.mkdir(parents=True, exist_ok=True)

    script_content = '''#!/usr/bin/env python3
"""
IG Auto-Responder — Engine de producao.
Verifica comentarios e DMs a cada 30 minutos.

Uso:
    python3 ig_auto_responder.py
"""

import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

WORKSPACE_DIR = Path.home() / ".openclaw" / "workspace"
ENV_PATH = WORKSPACE_DIR / ".env"
CONFIG_PATH = WORKSPACE_DIR / "ig_auto_config.json"
STATE_PATH = WORKSPACE_DIR / "ig_state.json"

GRAPH_API = "https://graph.instagram.com/v18.0"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_env():
    """Carrega variaveis do arquivo .env."""
    env = {}
    if not ENV_PATH.exists():
        return env
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("\'")
    return env


def load_config():
    """Carrega configuracao do auto-responder."""
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def log(msg):
    """Loga mensagem com timestamp."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def _load_seen_ids():
    """Carrega IDs ja processados do ig_state.json para evitar duplicatas."""
    if not STATE_PATH.exists():
        return {"comment_ids": [], "thread_ids": []}
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return {
            "comment_ids": data.get("seen_comment_ids", []),
            "thread_ids": data.get("seen_thread_ids", []),
        }
    except Exception:
        return {"comment_ids": [], "thread_ids": []}


def _save_seen_ids(seen_ids):
    """Persiste IDs processados no ig_state.json, mantendo campos existentes."""
    data = {}
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Limitar historico a 1000 IDs por tipo para nao crescer indefinidamente
    data["seen_comment_ids"] = seen_ids["comment_ids"][-1000:]
    data["seen_thread_ids"] = seen_ids["thread_ids"][-1000:]
    STATE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _api_get(endpoint, token, params=None):
    """GET na Graph API. Retorna dict ou None em caso de erro."""
    p = {"access_token": token}
    if params:
        p.update(params)
    url = f"{GRAPH_API}/{endpoint}?{urllib.parse.urlencode(p)}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        log(f"[ERRO] GET /{endpoint} falhou: {exc.code} — {body[:200]}")
        return None
    except Exception as exc:
        log(f"[ERRO] GET /{endpoint}: {exc}")
        return None


def _api_post(endpoint, token, payload):
    """POST na Graph API. Retorna dict ou None em caso de erro."""
    payload["access_token"] = token
    data = urllib.parse.urlencode(payload).encode("utf-8")
    url = f"{GRAPH_API}/{endpoint}"
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        log(f"[ERRO] POST /{endpoint} falhou: {exc.code} — {body[:200]}")
        return None
    except Exception as exc:
        log(f"[ERRO] POST /{endpoint}: {exc}")
        return None


# ---------------------------------------------------------------------------
# Comentarios
# ---------------------------------------------------------------------------

def get_recent_comments(media_id, token):
    """Retorna lista de comentarios recentes de uma midia."""
    data = _api_get(f"{media_id}/comments", token, {"fields": "id,text,username,timestamp"})
    if not data:
        return []
    return data.get("data", [])


def reply_to_comment(comment_id, message, token):
    """Responde a um comentario especifico."""
    result = _api_post(f"{comment_id}/replies", token, {"message": message})
    return result is not None


def _contains_keyword(text, keywords):
    """Verifica se o texto contem alguma das palavras-chave (case insensitive)."""
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            return True
    return False


def _build_reply(template, username, keyword):
    """Monta mensagem de resposta substituindo placeholders."""
    name = username or "voce"
    topic = keyword or "isso"
    return template.replace("{name}", name).replace("{topic}", topic)


def process_comments(user_id, config, token, rate_tracker, seen_ids):
    """Processa comentarios recentes e responde os que tem keywords."""
    comments_cfg = config.get("comments", {})
    if not comments_cfg.get("enabled", False):
        return

    keywords = comments_cfg.get("keywords", [])
    template = comments_cfg.get("reply_template", "Oi! Manda uma DM.")
    max_per_hour = config.get("rate_limit", {}).get("max_replies_per_hour", 20)

    # Buscar midias recentes do usuario
    media_data = _api_get(f"{user_id}/media", token, {"fields": "id,timestamp"})
    if not media_data:
        return

    medias = media_data.get("data", [])[:5]  # ultimas 5 midias
    for media in medias:
        media_id = media["id"]
        comments = get_recent_comments(media_id, token)

        for comment in comments:
            comment_id = comment.get("id")
            text = comment.get("text", "")
            username = comment.get("username", "")

            if not comment_id or not text:
                continue

            # Pular comentarios ja respondidos
            if comment_id in seen_ids["comment_ids"]:
                continue

            # Rate limit check
            if rate_tracker["replies_this_hour"] >= max_per_hour:
                log(f"[AVISO] Rate limit de replies atingido ({max_per_hour}/hora)")
                return

            # Verificar keyword
            matched_kw = None
            for kw in keywords:
                if kw.lower() in text.lower():
                    matched_kw = kw
                    break

            if not matched_kw:
                continue

            reply_msg = _build_reply(template, username, matched_kw)
            if reply_to_comment(comment_id, reply_msg, token):
                log(f"[OK] Resposta enviada para comentario de @{username} (kw: {matched_kw})")
                seen_ids["comment_ids"].append(comment_id)
                rate_tracker["replies_this_hour"] += 1
                time.sleep(comments_cfg.get("delay_seconds", 30))


# ---------------------------------------------------------------------------
# DMs
# ---------------------------------------------------------------------------

def get_recent_dms(user_id, token):
    """Retorna lista de conversas DM recentes."""
    data = _api_get(f"{user_id}/conversations", token, {
        "fields": "id,participants,updated_time",
        "platform": "instagram",
    })
    if not data:
        return []
    return data.get("data", [])


def send_dm(thread_id, message, token):
    """Envia DM para uma conversa existente."""
    result = _api_post(f"{thread_id}/messages", token, {"message": message})
    return result is not None


def process_dms(user_id, config, token, rate_tracker, seen_ids):
    """Processa DMs novos e envia welcome_message."""
    dms_cfg = config.get("dms", {})
    if not dms_cfg.get("enabled", False):
        return

    welcome_msg = dms_cfg.get(
        "welcome_message",
        "Oi! Aqui eh o assistente automatico. Em breve um humano vai te atender."
    )
    max_per_hour = config.get("rate_limit", {}).get("max_dms_per_hour", 10)

    conversations = get_recent_dms(user_id, token)
    for conv in conversations:
        thread_id = conv.get("id")
        if not thread_id:
            continue

        # Pular conversas ja saudadas
        if thread_id in seen_ids["thread_ids"]:
            continue

        # Rate limit check
        if rate_tracker["dms_this_hour"] >= max_per_hour:
            log(f"[AVISO] Rate limit de DMs atingido ({max_per_hour}/hora)")
            return

        if send_dm(thread_id, welcome_msg, token):
            log(f"[OK] Welcome DM enviada para conversa {thread_id}")
            seen_ids["thread_ids"].append(thread_id)
            rate_tracker["dms_this_hour"] += 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    log("IG Auto-Responder iniciado")

    env = load_env()
    token = env.get("IG_ACCESS_TOKEN")
    user_id = env.get("IG_USER_ID")

    if not token or not user_id:
        log("[ERRO] IG_ACCESS_TOKEN ou IG_USER_ID nao encontrados em .env")
        log("Execute a Etapa 6: python3 setup/setup_instagram_app.py")
        sys.exit(1)

    config = load_config()
    if not config:
        log("[AVISO] ig_auto_config.json nao encontrado. Usando config padrao vazia.")
        config = {"comments": {"enabled": False}, "dms": {"enabled": False}}

    rate_tracker = {"replies_this_hour": 0, "dms_this_hour": 0}
    seen_ids = _load_seen_ids()

    log(f"Processando comentarios e DMs do usuario {user_id}...")

    try:
        process_comments(user_id, config, token, rate_tracker, seen_ids)
        process_dms(user_id, config, token, rate_tracker, seen_ids)
        _save_seen_ids(seen_ids)
    except Exception as exc:
        log(f"[ERRO] Execucao falhou: {exc}")
        _save_seen_ids(seen_ids)
        sys.exit(1)

    log(f"Concluido. Replies: {rate_tracker['replies_this_hour']} | DMs: {rate_tracker['dms_this_hour']}")


if __name__ == "__main__":
    main()
'''

    IG_RESPONDER_PATH.write_text(script_content, encoding="utf-8")
    IG_RESPONDER_PATH.chmod(0o755)
    print(f"  [OK] Script criado: {IG_RESPONDER_PATH}")


# ---------------------------------------------------------------------------
# Passo 4 — Instalar cron/agendador
# ---------------------------------------------------------------------------

def _install_cron():
    cron_line = (
        f"*/30 * * * * python3 {IG_RESPONDER_PATH} >> {IG_CRON_LOG} 2>&1"
    )

    if PLATFORM in ("Darwin", "Linux"):
        print()
        print("  Instalando cron job (a cada 30 minutos)...")

        # Ler crontab atual
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
            )
            current_crontab = result.stdout if result.returncode == 0 else ""
        except Exception:
            current_crontab = ""

        # Verificar se ja existe
        responder_str = str(IG_RESPONDER_PATH)
        if responder_str in current_crontab:
            print("  [INFO] Cron job ja existe. Pulando instalacao.")
            return

        # Adicionar linha
        new_crontab = current_crontab.rstrip("\n") + "\n" + cron_line + "\n"
        try:
            proc = subprocess.run(
                ["crontab", "-"],
                input=new_crontab,
                text=True,
                capture_output=True,
            )
            if proc.returncode == 0:
                print("  [OK] Cron job instalado com sucesso.")
                print(f"  Linha: {cron_line}")
            else:
                print(f"  [AVISO] crontab retornou erro: {proc.stderr.strip()}")
                print(f"  Adicione manualmente: {cron_line}")
        except Exception as exc:
            print(f"  [AVISO] Nao foi possivel instalar cron: {exc}")
            print(f"  Adicione manualmente ao crontab: {cron_line}")

    elif PLATFORM == "Windows":
        task_cmd = (
            f'schtasks /create /tn "ZXLAB-IG-Responder" /sc minute /mo 30 '
            f'/tr "python3 {IG_RESPONDER_PATH}" /f'
        )
        print()
        print("  Instalando tarefa agendada no Windows...")
        try:
            result = subprocess.run(task_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print("  [OK] Tarefa agendada criada.")
            else:
                print(f"  [AVISO] schtasks retornou erro: {result.stderr.strip()}")
                print(f"  Execute manualmente: {task_cmd}")
        except Exception as exc:
            print(f"  [AVISO] Nao foi possivel criar tarefa: {exc}")
            print(f"  Execute manualmente: {task_cmd}")


# ---------------------------------------------------------------------------
# Passo 5 — Criar token manager
# ---------------------------------------------------------------------------

def _create_token_manager():
    token_mgr_content = '''#!/usr/bin/env python3
"""
IG Token Manager — Renova o token do Instagram antes de expirar.
Executa diariamente via LaunchAgent: com.zxlab.ig-auto-responder
"""

import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE_DIR = Path.home() / ".openclaw" / "workspace"
ENV_PATH = WORKSPACE_DIR / ".env"
STATE_PATH = WORKSPACE_DIR / "ig_state.json"
GRAPH_API = "https://graph.instagram.com"

DAYS_BEFORE_EXPIRY_REFRESH = 7


def load_env():
    env = {}
    if not ENV_PATH.exists():
        return env
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip(\'"\').strip("\'")
    return env


def write_env_var(key, value):
    """Atualiza uma variavel no arquivo .env, preservando as demais."""
    env_vars = load_env()
    env_vars[key] = value
    lines = [f"{k}={v}" for k, v in env_vars.items()]
    ENV_PATH.write_text("\\n".join(lines) + "\\n", encoding="utf-8")


def _refresh_token(current_token):
    """Renova o token via endpoint de refresh da Instagram API."""
    params = urllib.parse.urlencode({
        "grant_type": "ig_refresh_token",
        "access_token": current_token,
    })
    url = f"{GRAPH_API}/refresh_access_token?{params}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"Refresh falhou: {exc.code} — {body[:200]}")
    except Exception as exc:
        raise ValueError(f"Refresh falhou: {exc}")

    if "error" in data:
        raise ValueError(data["error"].get("message", "Refresh invalido"))

    new_token = data.get("access_token")
    expires_in = data.get("expires_in", 5184000)
    if not new_token:
        raise ValueError("Resposta de refresh nao continha access_token")

    return new_token, expires_in


def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] IG Token Manager iniciado", flush=True)

    env = load_env()
    token = env.get("IG_ACCESS_TOKEN")
    expires_str = env.get("IG_TOKEN_EXPIRES")

    if not token:
        print(f"[{ts}] [ERRO] IG_ACCESS_TOKEN nao encontrado. Execute a Etapa 6.")
        sys.exit(1)

    if not expires_str:
        print(f"[{ts}] [AVISO] IG_TOKEN_EXPIRES nao encontrado. Forcando refresh.")
        needs_refresh = True
    else:
        try:
            expiry = datetime.fromisoformat(expires_str)
            days_left = (expiry - datetime.now()).days
            print(f"[{ts}] Token expira em {days_left} dias ({expires_str})")
            needs_refresh = days_left <= DAYS_BEFORE_EXPIRY_REFRESH
        except Exception:
            print(f"[{ts}] [AVISO] Formato de IG_TOKEN_EXPIRES invalido. Forcando refresh.")
            needs_refresh = True

    if not needs_refresh:
        print(f"[{ts}] Token ainda valido. Nenhuma acao necessaria.")
        return

    print(f"[{ts}] Renovando token...")
    try:
        new_token, expires_in = _refresh_token(token)
    except ValueError as exc:
        print(f"[{ts}] [ERRO] {exc}")
        sys.exit(1)

    new_expiry = datetime.now() + timedelta(seconds=expires_in)
    new_expiry_iso = new_expiry.isoformat(timespec="seconds")

    write_env_var("IG_ACCESS_TOKEN", new_token)
    write_env_var("IG_TOKEN_EXPIRES", new_expiry_iso)

    # Atualizar ig_state.json
    if STATE_PATH.exists():
        try:
            state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            state["token_expires"] = new_expiry_iso
            state["token_valid"] = True
            STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            print(f"[{ts}] [AVISO] Nao foi possivel atualizar ig_state.json: {exc}")

    print(f"[{ts}] [OK] Token renovado. Novo expiry: {new_expiry_iso}")


if __name__ == "__main__":
    main()
'''

    IG_TOKEN_MGR_PATH.write_text(token_mgr_content, encoding="utf-8")
    IG_TOKEN_MGR_PATH.chmod(0o755)
    print(f"  [OK] Token manager criado: {IG_TOKEN_MGR_PATH}")

    # LaunchAgent (macOS)
    if PLATFORM == "Darwin":
        _install_launch_agent()


def _install_launch_agent():
    """Cria LaunchAgent diario para o token manager (macOS)."""
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    launch_agents_dir.mkdir(parents=True, exist_ok=True)

    plist_path = launch_agents_dir / "com.zxlab.ig-auto-responder.plist"
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.zxlab.ig-auto-responder</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{IG_TOKEN_MGR_PATH}</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{WORKSPACE_DIR}/ig_token_manager.log</string>
    <key>StandardErrorPath</key>
    <string>{WORKSPACE_DIR}/ig_token_manager.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
"""
    plist_path.write_text(plist_content, encoding="utf-8")

    # Tentar carregar o LaunchAgent
    try:
        subprocess.run(
            ["launchctl", "load", str(plist_path)],
            capture_output=True,
            text=True,
        )
        print(f"  [OK] LaunchAgent instalado: com.zxlab.ig-auto-responder")
    except Exception as exc:
        print(f"  [AVISO] Nao foi possivel carregar LaunchAgent: {exc}")
        print(f"  Execute manualmente: launchctl load {plist_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print("=" * 58)
    print("  Etapa 7 — Instagram: Auto-Responder + DM")
    print("=" * 58)

    ensure_structure()

    # Passo 1 — Verificar Etapa 6
    _check_step6()
    print()
    print("  [OK] Etapa 6 verificada. Continuando...")

    # Criar diretorios necessarios
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    SCRIPTS_DIR_WS.mkdir(parents=True, exist_ok=True)

    # Passo 2 — Configurar respostas automaticas
    config = _setup_ig_config()
    keywords = config.get("comments", {}).get("keywords", [])

    # Passo 3 — Criar script de auto-resposta
    print()
    print("  Criando script de auto-resposta...")
    _create_ig_auto_responder()

    # Passo 4 — Instalar cron/agendador
    _install_cron()

    # Passo 5 — Criar token manager
    print()
    print("  Criando token manager...")
    _create_token_manager()

    # Passo 6 — Checkpoint
    mark_checkpoint(STEP_KEY, "done", "auto-responder configurado")

    # Resultado final
    print()
    print("  [OK] Instagram Auto-Responder ativo!")
    print()
    print("  O bot vai verificar comentarios e DMs a cada 30 minutos.")
    print()
    keywords_str = ", ".join(keywords) if keywords else "(nenhuma)"
    print(f"  Keywords que ativam resposta: {keywords_str}")
    print("  Limite: 20 respostas/hora, 10 DMs/hora")
    print()
    print("  Para pausar: /ig-pausar")
    print("  Para retomar: /ig-retomar")
    print()
    print("  Checkpoint step_7_instagram_responder salvo.")


if __name__ == "__main__":
    main()
