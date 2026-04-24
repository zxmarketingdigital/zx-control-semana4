#!/usr/bin/env python3
"""
Etapa 4 — Skills e MCPs em Sync
Sincroniza ~/.claude/skills/ e configuracoes de MCP via git.
ZX Control Semana 4
"""

import getpass
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib import (
    PLATFORM,
    ensure_structure,
    mark_checkpoint,
    now_iso,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def progress_bar():
    print("\n[███░░░░░░░] Etapa 4 de 8 — Skills e MCPs em Sync\n")


def ask(prompt, secret=False, default=None):
    """Pergunta ao usuario com suporte a valor padrao e modo secreto."""
    display = prompt
    if default is not None:
        display = f"{prompt} [default: {default}]"
    try:
        if secret:
            value = getpass.getpass(f"  {display}: ").strip()
        else:
            value = input(f"  {display}: ").strip()
        if not value and default is not None:
            return default
        return value
    except (KeyboardInterrupt, EOFError):
        print()
        print("  Setup cancelado.")
        sys.exit(0)


def run_cmd(args, cwd=None, capture=False):
    """Executa comando e retorna (returncode, stdout, stderr)."""
    result = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        capture_output=capture,
        text=True,
    )
    return result.returncode, result.stdout or "", result.stderr or ""


# ---------------------------------------------------------------------------
# Git setup
# ---------------------------------------------------------------------------

def check_git():
    """Verifica se git esta disponivel no PATH."""
    return shutil.which("git") is not None


def setup_git_repo(SKILLS_DIR):
    """Inicializa ou verifica repo git em SKILLS_DIR."""
    git_dir = SKILLS_DIR / ".git"

    if not SKILLS_DIR.exists():
        print(f"  Pasta ~/.claude/skills/ nao encontrada. Criando...")
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        rc, _, err = run_cmd(["git", "init"], cwd=SKILLS_DIR)
        if rc == 0:
            print(f"  Repo git inicializado em {SKILLS_DIR}")
        else:
            print(f"  ERRO ao inicializar git: {err.strip()}")
            return False
    elif not git_dir.exists():
        print(f"  Pasta exists mas nao e um repo git. Inicializando...")
        rc, _, err = run_cmd(["git", "init"], cwd=SKILLS_DIR)
        if rc == 0:
            print(f"  Repo git inicializado.")
        else:
            print(f"  ERRO ao inicializar git: {err.strip()}")
            return False
    else:
        print(f"  Repo git ja existe em {SKILLS_DIR}")

    return True


def setup_gitignore(SKILLS_DIR):
    """Cria .gitignore padrao se nao existir."""
    gitignore = SKILLS_DIR / ".gitignore"
    if gitignore.exists():
        print(f"  .gitignore ja existe.")
        return

    gitignore.write_text(
        "*.secret\n*.env\n.DS_Store\n",
        encoding="utf-8",
    )
    print(f"  .gitignore criado com entradas: *.secret, *.env, .DS_Store")


def commit_changes(SKILLS_DIR):
    """Faz git add + commit se houver mudancas pendentes."""
    # Verifica se ha mudancas
    rc, stdout, _ = run_cmd(["git", "status", "--porcelain"], cwd=SKILLS_DIR, capture=True)
    if rc != 0 or not stdout.strip():
        print(f"  Nenhuma mudanca pendente para commit.")
        return

    print(f"  Mudancas detectadas. Fazendo commit...")
    run_cmd(["git", "add", "-A"], cwd=SKILLS_DIR)
    msg = f"sync: {now_iso()}"
    rc, _, err = run_cmd(["git", "commit", "-m", msg], cwd=SKILLS_DIR)
    if rc == 0:
        print(f"  Commit criado: {msg}")
    else:
        print(f"  AVISO: commit falhou (pode nao ter user.email configurado): {err.strip()}")
        # Tenta configurar git identity minimal e refaz
        run_cmd(["git", "config", "user.email", "zxlab@local"], cwd=SKILLS_DIR)
        run_cmd(["git", "config", "user.name", "ZX LAB"], cwd=SKILLS_DIR)
        rc2, _, err2 = run_cmd(["git", "commit", "-m", msg], cwd=SKILLS_DIR)
        if rc2 == 0:
            print(f"  Commit criado (com identidade local).")
        else:
            print(f"  AVISO: commit falhou — {err2.strip()}")


def setup_remote(SKILLS_DIR):
    """Verifica/configura remote git."""
    rc, stdout, _ = run_cmd(["git", "remote", "-v"], cwd=SKILLS_DIR, capture=True)
    if stdout.strip():
        print(f"  Remote ja configurado:")
        for line in stdout.strip().splitlines()[:2]:
            print(f"    {line}")
        return

    print()
    print("  Nao ha remote configurado para o repo de skills.")
    answer = ask("  Quer sincronizar suas skills com um repositorio remoto (GitHub)? (s/n)", default="n").lower()
    if answer not in ("s", "sim", "y", "yes"):
        print("  Pulando configuracao de remote.")
        return

    remote_url = ask("  URL do repositorio remoto (ex: https://github.com/usuario/skills.git)")
    if not remote_url.strip():
        print("  URL vazia. Pulando configuracao de remote.")
        return

    rc, _, err = run_cmd(["git", "remote", "add", "origin", remote_url.strip()], cwd=SKILLS_DIR)
    if rc == 0:
        print(f"  Remote 'origin' configurado: {remote_url.strip()}")
    else:
        print(f"  ERRO ao configurar remote: {err.strip()}")


# ---------------------------------------------------------------------------
# Sync agent (LaunchAgent / systemd / schtasks)
# ---------------------------------------------------------------------------

SYNC_SCRIPT_CONTENT = """#!/bin/sh
# Auto-sync skills — gerado por ZX Control Semana 4
cd "$HOME/.claude/skills" || exit 0
git add -A
git commit -m "auto-sync $(date -Iseconds)" 2>/dev/null
git push 2>/dev/null
"""

LAUNCHAGENT_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.zxlab.skills-sync</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/sh</string>
    <string>__SYNC_SCRIPT__</string>
  </array>
  <key>StartInterval</key>
  <integer>900</integer>
  <key>RunAtLoad</key>
  <false/>
  <key>StandardOutPath</key>
  <string>__LOGS_DIR__/skills-sync.log</string>
  <key>StandardErrorPath</key>
  <string>__LOGS_DIR__/skills-sync-error.log</string>
</dict>
</plist>
"""

SYSTEMD_SERVICE = """[Unit]
Description=ZX LAB Skills Sync
After=network.target

[Service]
Type=oneshot
ExecStart=/bin/sh __SYNC_SCRIPT__
"""

SYSTEMD_TIMER = """[Unit]
Description=ZX LAB Skills Sync — timer 15 min

[Timer]
OnCalendar=*:0/15
Persistent=true

[Install]
WantedBy=timers.target
"""


def install_sync_agent_macos(sync_script_path, logs_dir):
    """Instala LaunchAgent no macOS."""
    logs_dir.mkdir(parents=True, exist_ok=True)

    plist_dir = Path.home() / "Library" / "LaunchAgents"
    plist_dir.mkdir(parents=True, exist_ok=True)
    plist_path = plist_dir / "com.zxlab.skills-sync.plist"

    content = LAUNCHAGENT_PLIST.replace(
        "__SYNC_SCRIPT__", str(sync_script_path)
    ).replace(
        "__LOGS_DIR__", str(logs_dir)
    )

    plist_path.write_text(content, encoding="utf-8")
    print(f"  LaunchAgent criado: {plist_path}")

    # Descarregar versao anterior se existir
    subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
    rc = subprocess.run(["launchctl", "load", str(plist_path)], capture_output=True).returncode
    if rc == 0:
        print(f"  LaunchAgent carregado (interval: 15 min).")
    else:
        print(f"  AVISO: launchctl load falhou. Execute manualmente:")
        print(f"    launchctl load {plist_path}")


def install_sync_agent_linux(sync_script_path):
    """Instala systemd timer no Linux."""
    systemd_dir = Path.home() / ".config" / "systemd" / "user"
    systemd_dir.mkdir(parents=True, exist_ok=True)

    service_path = systemd_dir / "zxlab-skills-sync.service"
    timer_path = systemd_dir / "zxlab-skills-sync.timer"

    service_path.write_text(
        SYSTEMD_SERVICE.replace("__SYNC_SCRIPT__", str(sync_script_path)),
        encoding="utf-8",
    )
    timer_path.write_text(SYSTEMD_TIMER, encoding="utf-8")

    print(f"  systemd service criado: {service_path}")
    print(f"  systemd timer criado: {timer_path}")

    # Habilitar e iniciar
    cmds = [
        ["systemctl", "--user", "daemon-reload"],
        ["systemctl", "--user", "enable", "--now", "zxlab-skills-sync.timer"],
    ]
    for cmd in cmds:
        rc = subprocess.run(cmd, capture_output=True).returncode
        if rc != 0:
            print(f"  AVISO: '{' '.join(cmd)}' falhou. Execute manualmente.")

    print(f"  Timer ativado (OnCalendar=*:0/15).")


def install_sync_agent_windows(sync_script_path):
    """Mostra instrucao para schtasks no Windows (requer Git Bash ou WSL)."""
    # Cotas o path para lidar com espacos no caminho do usuario
    quoted_path = f'"{sync_script_path}"'
    # Detecta sh via Git Bash ou WSL
    sh_bin = shutil.which("sh") or r"C:\Program Files\Git\bin\sh.exe"
    print()
    print("  Windows: requer Git Bash (https://git-scm.com) ou WSL com 'sh' no PATH.")
    print()
    print("  Execute como Administrador no PowerShell:")
    print(f'  schtasks /create /tn "ZXLAB-Skills-Sync" /sc minute /mo 15 /tr "{sh_bin} {sync_script_path}" /f')
    print()
    print("  Ou via PowerShell como Administrador:")
    print(f'  Register-ScheduledTask -TaskName "ZXLAB-Skills-Sync" \\')
    print(f'    -Action (New-ScheduledTaskAction -Execute "{sh_bin}" -Argument {quoted_path}) \\')
    print(f'    -Trigger (New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 15) -Once -At (Get-Date))')


def setup_sync_agent(SKILLS_DIR):
    """Instala agente de sync automatico de acordo com a plataforma."""
    print()
    print("--- Agente de Sync Automatico (15 min) ---")
    print()

    # Criar script de sync
    sync_dir = Path.home() / ".operacao-ia" / "scripts"
    sync_dir.mkdir(parents=True, exist_ok=True)
    sync_script_path = sync_dir / "skills_sync.sh"
    sync_script_path.write_text(SYNC_SCRIPT_CONTENT, encoding="utf-8")
    if PLATFORM != "Windows":
        sync_script_path.chmod(0o755)
    print(f"  Script de sync criado: {sync_script_path}")

    logs_dir = Path.home() / ".operacao-ia" / "logs" / "week4"

    if PLATFORM == "Darwin":
        install_sync_agent_macos(sync_script_path, logs_dir)
    elif PLATFORM == "Linux":
        install_sync_agent_linux(sync_script_path)
    else:
        install_sync_agent_windows(sync_script_path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print("=" * 52)
    print("  ZX Control — Semana 4: Inteligencia & Escala")
    print("=" * 52)
    print()
    progress_bar()

    print("  Etapa 4 — Skills e MCPs em Sync")
    print()
    print("  Vamos versionar sua pasta ~/.claude/skills/ com git")
    print("  e instalar sync automatico a cada 15 minutos.")
    print()

    ensure_structure()

    # Verificar git
    if not check_git():
        print("  ERRO: git nao encontrado no PATH.")
        print("  Instale git em https://git-scm.com e execute novamente.")
        sys.exit(1)

    print("  git encontrado.")
    print()

    SKILLS_DIR = Path.home() / ".claude" / "skills"

    # 1. Inicializar repo
    print("--- Repositorio Git ---")
    print()
    ok = setup_git_repo(SKILLS_DIR)
    if not ok:
        print("  ERRO: falha ao inicializar repositorio. Abortando.")
        sys.exit(1)

    # 2. Criar .gitignore
    setup_gitignore(SKILLS_DIR)

    # 3. Commit inicial
    commit_changes(SKILLS_DIR)

    print()

    # 4. Configurar remote (opcional)
    print("--- Remote (opcional) ---")
    print()
    setup_remote(SKILLS_DIR)

    # 5. Instalar agente de sync
    setup_sync_agent(SKILLS_DIR)

    # Checkpoint
    mark_checkpoint(
        "step_4_sync_skills_mcp",
        "done",
        f"git repo: {SKILLS_DIR} | plataforma: {PLATFORM}",
    )

    print()
    print("  [OK] Etapa 4 concluida — Skills versionadas e sync configurado!\n")
    print("  Proximo passo: Etapa 5 — Graphify Segundo Cerebro")
    print("  Execute: python3 setup/setup_graphify.py")
    print()


if __name__ == "__main__":
    main()
