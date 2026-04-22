#!/usr/bin/env python3
"""
Etapa 6 — Instagram Facebook App + Tokens
Configuracao do App Meta e obtencao do long-lived access token.
"""

import getpass
import json
import sys
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib import (
    CONFIG_PATH, PLATFORM, BASE_DIR, DATA_DIR, LOGS_DIR,
    IG_STATE_PATH, IG_ENV_PATH, now_iso, ensure_structure,
    load_config, save_config, mark_checkpoint, load_env_var,
    load_checkpoint,
)

STEP_KEY = "step_6_instagram_app"
ENV_DIR = Path.home() / ".openclaw" / "workspace"


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


def _read_env_file(path):
    """Le arquivo .env e retorna dict com as variaveis."""
    env_vars = {}
    p = Path(path)
    if not p.exists():
        return env_vars
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars


def _write_env_file(path, env_vars):
    """Grava dict como arquivo .env."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for k, v in env_vars.items():
        lines.append(f"{k}={v}")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _validate_token(token):
    """
    Valida token via Graph API do Instagram.
    Retorna (user_id, username) se valido, ou lanca Exception se invalido.
    """
    url = f"https://graph.instagram.com/me?fields=id,username&access_token={token}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
        if "error" in data:
            raise ValueError(data["error"].get("message", "Token invalido"))
        return data["id"], data["username"]
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            err_data = json.loads(body)
            msg = err_data.get("error", {}).get("message", str(exc))
        except Exception:
            msg = str(exc)
        raise ValueError(msg)


def _exchange_for_long_token(app_id, app_secret, short_token):
    """
    Troca token curto por long-lived token.
    Apps tipo Business usam o endpoint do Facebook Graph API (fb_exchange_token).
    Retorna (long_token, expires_in_seconds).
    """
    # Facebook Graph API — correto para apps Business/Meta
    params = urllib.parse.urlencode({
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_token,
    })
    url = f"https://graph.facebook.com/oauth/access_token?{params}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            err_data = json.loads(body)
            msg = err_data.get("error", {}).get("message", str(exc))
        except Exception:
            msg = str(exc)
        raise ValueError(f"Exchange Facebook falhou: {msg}")

    if "error" in data:
        raise ValueError(data["error"].get("message", "Exchange falhou"))

    long_token = data.get("access_token")
    expires_in = data.get("expires_in", 5184000)  # ~60 dias fallback
    if not long_token:
        raise ValueError("Resposta do exchange nao continha access_token")

    return long_token, expires_in


def _format_expiry_date(expires_in_seconds):
    """Retorna data de expiracao em ISO e legivel."""
    expiry = datetime.now() + timedelta(seconds=expires_in_seconds)
    return expiry.isoformat(timespec="seconds"), expiry.strftime("%d/%m/%Y")


# ---------------------------------------------------------------------------
# Passo 1 — Verificar token existente
# ---------------------------------------------------------------------------

def _check_existing_token():
    """
    Verifica se token existente eh valido.
    Retorna True se valido (e ja fez checkpoint), False para continuar o fluxo.
    """
    token = load_env_var(IG_ENV_PATH, "IG_ACCESS_TOKEN")
    user_id = load_env_var(IG_ENV_PATH, "IG_USER_ID")

    if not token or not user_id:
        return False

    print("\n  Token anterior encontrado. Validando...")
    try:
        uid, username = _validate_token(token)
        print(f"\n  [OK] Token existente valido para @{username}")
        print(f"  User ID: {uid}")
        mark_checkpoint(STEP_KEY, "done", f"@{username} (token existente valido)")
        return True
    except Exception as exc:
        print(f"  [AVISO] Token existente invalido ou expirado: {exc}")
        print("  Prosseguindo com novo exchange...\n")
        return False


# ---------------------------------------------------------------------------
# Passo 3 — Mostrar checklist + abrir browser
# ---------------------------------------------------------------------------

def _show_checklist():
    print()
    print("  ┌─────────────────────────────────────────────────────┐")
    print("  │  META DEVELOPERS — 6 PASSOS                         │")
    print("  │  (o browser abriu em developers.facebook.com/apps)  │")
    print("  └─────────────────────────────────────────────────────┘")
    print()
    print("  [ ] Passo 1: Clique em \"Create App\" → tipo \"Business\"")
    print("               Em \"App Name\": coloque \"ZX Control IG Bot\"")
    print()
    print("  [ ] Passo 2: Em \"Add products\" → escolha \"Instagram Graph API\"")
    print()
    print("  [ ] Passo 3: Va em \"Settings > Basic\"")
    print("               Copie o App ID e o App Secret")
    print()
    print("  [ ] Passo 4: Va em \"Roles > Instagram Testers\"")
    print("               Adicione seu usuario do Instagram como testador")
    print()
    print("  [ ] Passo 5: Abra o app do Instagram no celular")
    print("               Configuracoes > Aplicativos e Sites → aceite o convite")
    print()
    print("  [ ] Passo 6: Volte ao navegador → va em \"Tools > Graph API Explorer\"")
    print("               Em \"User or Page\", selecione seu usuario")
    print("               Em \"Permissions\": adicione instagram_basic,")
    print("               instagram_manage_comments, instagram_manage_messages")
    print("               Clique \"Generate Access Token\" e copie o token curto")
    print()
    try:
        input("  [Enter quando concluir os 6 passos]")
    except KeyboardInterrupt:
        print("\n  Operacao cancelada pelo usuario.")
        sys.exit(0)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print("=" * 58)
    print("  Etapa 6 — Instagram: Facebook App + Tokens")
    print("=" * 58)

    ensure_structure()

    # Passo 2 — Criar diretorio ~/.openclaw/workspace/
    ENV_DIR.mkdir(parents=True, exist_ok=True)

    # Passo 1 — Verificar token existente
    if _check_existing_token():
        return

    # Passo 3 — Abrir browser + checklist
    print("\n  Abrindo Meta Developers no browser...")
    try:
        webbrowser.open("https://developers.facebook.com/apps/?show_reminder=true")
    except Exception:
        print("  [AVISO] Nao foi possivel abrir o browser automaticamente.")
        print("  Acesse: https://developers.facebook.com/apps/")

    _show_checklist()

    # Passo 4 — Coletar credenciais
    print()
    print("  Agora cole os dados do seu App Meta:")
    print()
    app_id = ask("Cole seu App ID (numeros)")
    if not app_id.isdigit():
        print("  [ERRO] App ID deve conter apenas numeros.")
        sys.exit(1)

    app_secret = ask("Cole seu App Secret", secret=True)
    if len(app_secret) < 16:
        print("  [ERRO] App Secret parece invalido (muito curto).")
        sys.exit(1)

    short_token = ask("Cole o token curto do Graph API Explorer")
    if len(short_token) < 20:
        print("  [ERRO] Token parece invalido (muito curto).")
        sys.exit(1)

    # Passo 5 — Exchange para long-lived token
    print()
    print("  Trocando token curto por long-lived token...")
    try:
        long_token, expires_in = _exchange_for_long_token(app_id, app_secret, short_token)
    except ValueError as exc:
        print(f"  [ERRO] Exchange falhou: {exc}")
        print("  Verifique se o token curto foi gerado com as permissoes corretas.")
        sys.exit(1)

    # Passo 6 — Validar e obter user_id
    print("  Validando token longo e obtendo dados da conta...")
    try:
        user_id, username = _validate_token(long_token)
    except ValueError as exc:
        print(f"  [ERRO] Validacao do token longo falhou: {exc}")
        sys.exit(1)

    # Calcular expiracao
    token_expires_iso, token_expires_human = _format_expiry_date(expires_in)

    # Passo 7 — Salvar no .env
    print("  Salvando credenciais em ~/.openclaw/workspace/.env ...")
    env_vars = _read_env_file(IG_ENV_PATH)
    env_vars["IG_ACCESS_TOKEN"] = long_token
    env_vars["IG_USER_ID"] = user_id
    env_vars["IG_APP_ID"] = app_id
    env_vars["IG_APP_SECRET"] = app_secret
    env_vars["IG_TOKEN_EXPIRES"] = token_expires_iso
    env_vars["IG_USERNAME"] = username
    _write_env_file(IG_ENV_PATH, env_vars)

    # Passo 8 — Salvar ig_state.json
    print("  Salvando estado em ~/.openclaw/workspace/ig_state.json ...")
    ig_state = {
        "user_id": user_id,
        "username": username,
        "token_valid": True,
        "token_expires": token_expires_iso,
        "app_id": app_id,
        "configured_at": now_iso(),
    }
    IG_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    IG_STATE_PATH.write_text(
        json.dumps(ig_state, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Passo 9 — Mostrar sucesso
    print()
    print("  [OK] Instagram configurado!")
    print()
    print(f"  Conta: @{username}")
    print(f"  App ID: {app_id}")
    print(f"  Token: valido por ~60 dias (expira em {token_expires_human})")
    print()
    print("  O token sera renovado automaticamente antes de expirar.")
    print()

    mark_checkpoint(STEP_KEY, "done", f"@{username} app:{app_id}")
    print("  Checkpoint step_6_instagram_app salvo.")


if __name__ == "__main__":
    main()
