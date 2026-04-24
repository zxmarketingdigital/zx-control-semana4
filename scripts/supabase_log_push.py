#!/usr/bin/env python3
"""
supabase_log_push.py — Envia log de sessao para Supabase via Edge Function.
Sem dependencias externas (so stdlib).
"""

import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# Adiciona scripts/ ao path para importar lib
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib import DATA_DIR

# Arquivo de pendencias
PENDING_PATH = DATA_DIR / "logs" / "pending_push.json"


def _load_pending():
    """Carrega lista de arquivos pendentes de envio."""
    if PENDING_PATH.exists():
        try:
            data = json.loads(PENDING_PATH.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []
    return []


def _save_pending(pending_list):
    """Salva lista de arquivos pendentes."""
    PENDING_PATH.parent.mkdir(parents=True, exist_ok=True)
    PENDING_PATH.write_text(
        json.dumps(pending_list, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _add_to_pending(session_json_path):
    """Adiciona caminho ao arquivo de pendencias."""
    pending = _load_pending()
    path_str = str(session_json_path)
    if path_str not in pending:
        pending.append(path_str)
    _save_pending(pending)


def push(session_json_path, config):
    """
    Le JSON do arquivo e faz POST para Edge Function do Supabase.

    Args:
        session_json_path: Path ou str para o arquivo .json de sessao
        config: dict com supabase_url e supabase_anon_key

    Returns:
        dict com {"id": "...", "status": "ok"} ou raise Exception
    """
    supabase_url = config.get("supabase_url", "").rstrip("/")
    anon_key = config.get("supabase_anon_key", "")

    if not supabase_url or not anon_key:
        raise ValueError("Supabase nao configurado — supabase_url ou supabase_anon_key ausentes")

    session_json_path = Path(session_json_path)
    if not session_json_path.exists():
        raise FileNotFoundError(f"Arquivo de log nao encontrado: {session_json_path}")
    payload_bytes = session_json_path.read_bytes()

    url = f"{supabase_url}/functions/v1/session-log-s4"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {anon_key}",
    }

    req = urllib.request.Request(
        url,
        data=payload_bytes,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            try:
                return json.loads(body)
            except Exception:
                return {"status": "ok", "raw": body}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise Exception(f"HTTP {e.code}: {error_body}") from e
    except urllib.error.URLError as e:
        raise Exception(f"Erro de conexao: {e.reason}") from e


def push_with_retry(session_json_path, config, max_retries=3):
    """
    Tenta push com backoff exponencial (2s, 4s, 8s...).

    Args:
        session_json_path: Path ou str para o arquivo .json de sessao
        config: dict com configuracoes do Supabase
        max_retries: numero maximo de tentativas (default 3)

    Returns:
        tuple (success: bool, error: str ou None)
    """
    supabase_url = config.get("supabase_url", "")
    anon_key = config.get("supabase_anon_key", "")

    if not supabase_url or not anon_key:
        _add_to_pending(session_json_path)
        return False, "Supabase nao configurado — log salvo localmente"

    last_error = None
    for attempt in range(max_retries):
        try:
            result = push(session_json_path, config)
            return True, None
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)  # 2s, 4s, 8s
                time.sleep(wait)

    # Todas as tentativas falharam — adiciona ao pending
    _add_to_pending(session_json_path)
    return False, f"Falha apos {max_retries} tentativas: {last_error}"


def push_pending(config):
    """
    Le pending_push.json e tenta enviar cada arquivo pendente.
    Remove do pending os que tiveram sucesso.

    Args:
        config: dict com configuracoes do Supabase

    Returns:
        dict com {"sent": [...], "still_pending": [...]}
    """
    pending = _load_pending()
    if not pending:
        return {"sent": [], "still_pending": []}

    still_pending = []
    sent = []

    for path_str in pending:
        path = Path(path_str)
        if not path.exists():
            # Arquivo nao existe mais — remove do pending silenciosamente
            continue
        try:
            push(path, config)
            sent.append(path_str)
        except Exception:
            still_pending.append(path_str)

    _save_pending(still_pending)
    return {"sent": sent, "still_pending": still_pending}
