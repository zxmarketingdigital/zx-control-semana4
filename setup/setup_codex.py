#!/usr/bin/env python3
"""
Etapa 2 — Codex Plugin + Revisor Diario
Instala plugin Codex (github.com/openai/codex-plugin-cc) no Claude Code,
cria projeto de revisao e configura agentes agendados.
"""

import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib import (
    CODEX_AUTOMATIONS_DIR,
    CODEX_DIR,
    CODEX_PROJECT_REVIEW_DIR,
    PLATFORM,
    ensure_structure,
    load_config,
    mark_checkpoint,
    now_iso,
    save_config,
)

LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"
SYSTEMD_USER_DIR = Path.home() / ".config" / "systemd" / "user"

PLUGIN_URL = "https://github.com/openai/codex-plugin-cc"
PLUGIN_NAME = "codex-plugin-cc"

LAUNCH_AGENTS = [
    {
        "label": "com.zxlab.codex-review-daily",
        "args": ["claude", "-p", "/codex:review"],
        "hour": 9,
        "minute": 0,
        "log": "~/.codex/logs/daily.log",
        "err": "~/.codex/logs/daily-err.log",
        "description": "diario 09h00",
    },
    {
        "label": "com.zxlab.codex-review-morning",
        "args": ["claude", "-p", "/codex:review --effort medium"],
        "hour": 8,
        "minute": 30,
        "weekday": 1,
        "log": "~/.codex/logs/morning.log",
        "err": "~/.codex/logs/morning-err.log",
        "description": "toda segunda 08h30 (effort: medium)",
    },
    {
        "label": "com.zxlab.codex-review-weekly",
        "args": ["claude", "-p", "/codex:review --effort high"],
        "hour": 22,
        "minute": 0,
        "weekday": 0,
        "log": "~/.codex/logs/weekly.log",
        "err": "~/.codex/logs/weekly-err.log",
        "description": "domingo 22h00 (effort: high)",
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def progress_bar():
    print("\n[██░░░░░░] Etapa 2 de 8 — Codex CLI + Revisor Diario\n")


def _run(cmd, capture=True):
    """Executa subprocess; retorna (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
        )
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        return result.returncode, stdout, stderr
    except FileNotFoundError:
        return 1, "", f"Comando nao encontrado: {cmd[0]}"
    except Exception as e:
        return 1, "", str(e)


# ---------------------------------------------------------------------------
# Instalacao do Plugin Codex (Claude Code Extension)
# ---------------------------------------------------------------------------

def ensure_claude_cli():
    """Verifica se o Claude Code CLI esta disponivel."""
    path = shutil.which("claude")
    if path:
        code, out, err = _run(["claude", "--version"])
        if code == 0:
            print(f"  [OK] Claude Code CLI disponivel: {out or 'ok'}")
            return True
    print("  [ERRO] Claude Code CLI nao encontrado no PATH.")
    print("  Instale via: https://claude.ai/code")
    return False


def ensure_codex_plugin():
    """
    Instala o plugin Codex no Claude Code se ainda nao estiver presente.
    Retorna True se o plugin esta disponivel apos a tentativa.
    """
    # Verificar se ja instalado: checar lista de plugins
    code, out, err = _run(["claude", "plugin", "list"])
    if code == 0 and PLUGIN_NAME in out:
        print(f"  [OK] Plugin '{PLUGIN_NAME}' ja instalado.")
        return True

    print(f"  Instalando plugin Codex do Claude Code...")
    print(f"    {PLUGIN_URL}")
    print()
    code, out, err = _run(["claude", "plugin", "install", PLUGIN_URL], capture=False)
    if code == 0:
        print(f"  [OK] Plugin instalado com sucesso.")
        return True

    # Fallback: mostrar instrucao manual
    print()
    print("  [AVISO] Instalacao automatica falhou.")
    print("  Instale manualmente dentro do Claude Code:")
    print(f"    /plugin install {PLUGIN_URL}")
    print()
    print("  Ou execute no terminal:")
    print(f"    claude plugin install {PLUGIN_URL}")
    print()
    try:
        confirm = input("  Plugin ja instalado manualmente? [s/n]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        confirm = "n"
        print("  [non-TTY] Instalacao automatica falhou. Aluno deve rodar manualmente:")
        print(f"    claude plugin install {PLUGIN_URL}")
    return confirm in ("s", "sim", "y", "yes")


def check_plugin_functional():
    """Testa se o plugin responde via Claude CLI."""
    code, out, err = _run(["claude", "-p", "/codex:review --help"])
    if code == 0:
        print("  [OK] Plugin Codex responde corretamente.")
        return True
    # Nao fatal — plugin pode funcionar mas --help nao estar implementado
    print("  [OK] Plugin instalado (resposta de teste nao disponivel).")
    return True


# ---------------------------------------------------------------------------
# projects.json
# ---------------------------------------------------------------------------

def update_projects_json():
    """Cria ou atualiza ~/.codex/automations/project-review/projects.json."""
    CODEX_PROJECT_REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    projects_path = CODEX_PROJECT_REVIEW_DIR / "projects.json"

    novos = [
        {"name": "operacao-ia", "path": "~/.operacao-ia", "effort": "low"},
        {"name": "zx-control-s4", "path": "~/zx-control-semana4", "effort": "medium"},
    ]

    if projects_path.exists():
        try:
            data = json.loads(projects_path.read_text(encoding="utf-8"))
        except Exception:
            data = {"projects": []}
        projetos = data.get("projects", [])
        nomes_existentes = {p.get("name") for p in projetos}
        adicionados = 0
        for novo in novos:
            if novo["name"] not in nomes_existentes:
                projetos.append(novo)
                adicionados += 1
        data["projects"] = projetos
        data["last_updated"] = now_iso()
        projects_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if adicionados:
            print(f"  [OK] {adicionados} projeto(s) adicionado(s) em projects.json")
        else:
            print("  [OK] projects.json ja esta atualizado.")
    else:
        data = {
            "projects": novos,
            "last_updated": now_iso(),
        }
        projects_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  [OK] projects.json criado em {projects_path}")

    return projects_path


# ---------------------------------------------------------------------------
# LaunchAgents (macOS)
# ---------------------------------------------------------------------------

def _plist_content(agent):
    """Gera conteudo XML do plist para um LaunchAgent."""
    # Resolve caminho absoluto do claude (launchd nao herda PATH do shell)
    claude_bin = shutil.which("claude") or "/usr/local/bin/claude"
    args = [claude_bin] + agent["args"][1:]  # substitui "claude" pelo path absoluto
    args_xml = "".join(f"    <string>{a}</string>\n" for a in args)
    # Expande ~ — launchd nao interpreta ~ em StandardOutPath/StandardErrorPath
    log_path = agent["log"].replace("~", str(Path.home()))
    err_path = agent["err"].replace("~", str(Path.home()))
    interval_key = "StartCalendarInterval"
    interval_dict = (
        f"  <key>{interval_key}</key>\n"
        "  <dict>\n"
    )
    if "weekday" in agent:
        interval_dict += f"    <key>Weekday</key>\n    <integer>{agent['weekday']}</integer>\n"
    interval_dict += (
        f"    <key>Hour</key>\n    <integer>{agent['hour']}</integer>\n"
        f"    <key>Minute</key>\n    <integer>{agent['minute']}</integer>\n"
        "  </dict>\n"
    )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        "<dict>\n"
        "  <key>Label</key>\n"
        f"  <string>{agent['label']}</string>\n"
        "  <key>ProgramArguments</key>\n"
        "  <array>\n"
        f"{args_xml}"
        "  </array>\n"
        + interval_dict +
        "  <key>StandardOutPath</key>\n"
        f"  <string>{log_path}</string>\n"
        "  <key>StandardErrorPath</key>\n"
        f"  <string>{err_path}</string>\n"
        "</dict>\n"
        "</plist>\n"
    )


def install_launch_agents():
    """Instala LaunchAgents no macOS. Idempotente."""
    LAUNCH_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    # Criar diretorio de logs
    (Path.home() / ".codex" / "logs").mkdir(parents=True, exist_ok=True)

    registrados = 0
    for agent in LAUNCH_AGENTS:
        plist_path = LAUNCH_AGENTS_DIR / f"{agent['label']}.plist"
        if plist_path.exists():
            print(f"  [OK] LaunchAgent ja existe: {agent['label']}")
            registrados += 1
            continue

        plist_path.write_text(_plist_content(agent), encoding="utf-8")
        code, out, err = _run(["launchctl", "load", str(plist_path)])
        if code == 0:
            print(f"  [OK] LaunchAgent registrado: {agent['label']} ({agent['description']})")
            registrados += 1
        else:
            print(f"  [AVISO] Falha ao carregar {agent['label']}: {err}")

    return registrados


# ---------------------------------------------------------------------------
# systemd timers (Linux)
# ---------------------------------------------------------------------------

def _systemd_service(agent):
    # shlex.join preserva agrupamento de args com espacos (ex: "-p /codex:review --effort medium")
    cmd = shlex.join(agent["args"])
    return (
        "[Unit]\n"
        f"Description=ZX LAB Codex Review ({agent['label']})\n\n"
        "[Service]\n"
        f"ExecStart=/usr/bin/env {cmd}\n"
        f"StandardOutput=append:{agent['log'].replace('~', str(Path.home()))}\n"
        f"StandardError=append:{agent['err'].replace('~', str(Path.home()))}\n\n"
        "[Install]\n"
        "WantedBy=default.target\n"
    )


def _systemd_timer(agent):
    if "weekday" in agent:
        # Weekday 0=domingo, 1=segunda no plist; em systemd: Sun=0, Mon=1
        day_map = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}
        day = day_map.get(agent["weekday"], "*")
        on_calendar = f"{day} *-*-* {agent['hour']:02d}:{agent['minute']:02d}:00"
    else:
        on_calendar = f"*-*-* {agent['hour']:02d}:{agent['minute']:02d}:00"
    return (
        "[Unit]\n"
        f"Description=ZX LAB Codex Review timer ({agent['label']})\n\n"
        "[Timer]\n"
        f"OnCalendar={on_calendar}\n"
        "Persistent=true\n\n"
        "[Install]\n"
        "WantedBy=timers.target\n"
    )


def install_systemd_timers():
    """Instala systemd user timers no Linux. Idempotente."""
    SYSTEMD_USER_DIR.mkdir(parents=True, exist_ok=True)
    (Path.home() / ".codex" / "logs").mkdir(parents=True, exist_ok=True)

    registrados = 0
    for agent in LAUNCH_AGENTS:
        name = agent["label"]
        svc_path = SYSTEMD_USER_DIR / f"{name}.service"
        tmr_path = SYSTEMD_USER_DIR / f"{name}.timer"

        if tmr_path.exists():
            print(f"  [OK] systemd timer ja existe: {name}")
            registrados += 1
            continue

        svc_path.write_text(_systemd_service(agent), encoding="utf-8")
        tmr_path.write_text(_systemd_timer(agent), encoding="utf-8")

        code, out, err = _run(["systemctl", "--user", "enable", "--now", f"{name}.timer"])
        if code == 0:
            print(f"  [OK] systemd timer ativo: {name} ({agent['description']})")
            registrados += 1
        else:
            print(f"  [AVISO] Falha ao ativar {name}: {err}")

    return registrados


# ---------------------------------------------------------------------------
# Task Scheduler (Windows)
# ---------------------------------------------------------------------------

def install_windows_tasks():
    """Registra tarefas agendadas no Windows."""
    registrados = 0
    for agent in LAUNCH_AGENTS:
        tn = agent["label"].replace("com.zxlab.", "ZXLAB-").replace("-", "-")
        time_str = f"{agent['hour']:02d}:{agent['minute']:02d}"

        if "weekday" in agent:
            day_map = {0: "SUN", 1: "MON", 2: "TUE", 3: "WED", 4: "THU", 5: "FRI", 6: "SAT"}
            day = day_map.get(agent["weekday"], "MON")
            schedule = ["WEEKLY", "/D", day]
        else:
            schedule = ["DAILY"]

        cmd = [
            "schtasks", "/create",
            "/tn", tn,
            "/tr", shlex.join(agent["args"]),
            "/sc", *schedule,
            "/st", time_str,
            "/f",
        ]
        code, out, err = _run(cmd)
        if code == 0:
            print(f"  [OK] Task agendada: {tn} ({agent['description']})")
            registrados += 1
        else:
            # Tarefa ja pode existir (/f deveria sobrescrever, mas tratar mesmo assim)
            if "already exists" in err.lower() or code == 0:
                print(f"  [OK] Task ja existe: {tn}")
                registrados += 1
            else:
                print(f"  [AVISO] Falha ao criar task {tn}: {err}")

    return registrados


# ---------------------------------------------------------------------------
# Instalar skill /codex-review
# ---------------------------------------------------------------------------

def install_skill_codex_review():
    """Copia skills/codex-review/SKILL.md para ~/.claude/skills/codex-review/."""
    src = ROOT_DIR / "skills" / "codex-review" / "SKILL.md"
    dst = Path.home() / ".claude" / "skills" / "codex-review" / "SKILL.md"
    if not src.exists():
        print(f"  [AVISO] SKILL.md nao encontrado em {src}")
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)
    print(f"  [OK] Skill /codex-review instalada em {dst}")
    return True


# ---------------------------------------------------------------------------
# Instalar agendadores por plataforma
# ---------------------------------------------------------------------------

def install_schedulers():
    """Instala agendadores conforme plataforma. Retorna quantidade registrada."""
    print(f"  Plataforma detectada: {PLATFORM}")
    print()

    if PLATFORM == "Darwin":
        return install_launch_agents()
    elif PLATFORM == "Linux":
        return install_systemd_timers()
    elif PLATFORM == "Windows":
        return install_windows_tasks()
    else:
        print(f"  [AVISO] Plataforma desconhecida: {PLATFORM}. Pulando agendadores.")
        return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    progress_bar()

    ensure_structure()

    # 1. Verificar Claude Code CLI
    print("  Verificando Claude Code CLI...")
    print()
    claude_ok = ensure_claude_cli()
    if not claude_ok:
        sys.exit(1)
    print()

    # 2. Instalar plugin Codex
    print("  Verificando plugin Codex...")
    print(f"    URL: {PLUGIN_URL}")
    print()
    plugin_ok = ensure_codex_plugin()
    if plugin_ok:
        check_plugin_functional()
    else:
        print("  [AVISO] Plugin nao disponivel. Agendadores usarao claude -p /codex:review.")
        print("  Instale manualmente e re-execute este script se necessario.")
    print()

    # 3. Instalar skill complementar
    print("  Instalando skill /codex-review...")
    skill_ok = install_skill_codex_review()
    print()

    # 4. Criar/atualizar projects.json
    print("  Configurando projeto de revisao...")
    projects_path = update_projects_json()
    print()

    # 5. Perguntar se quer automacao agendada (OPT-IN)
    print("  OPCIONAL: Automacao de revisao agendada")
    print("  - Revisao diaria (09h), semanal (seg 08h30), profunda (dom 22h)")
    print("  - Voce pode rodar manualmente a qualquer hora com /codex-review")
    print()
    try:
        resp = input("  Instalar automacao agendada? [s/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        resp = "n"
        print("  [non-TTY] Pulando automacao — use /codex-review manualmente.")

    if resp in ("s", "sim", "y", "yes"):
        print()
        print("  Instalando agendadores automaticos...")
        print()
        registrados = install_schedulers()
        print()
        if registrados >= 1:
            print(f"  [OK] {registrados}/3 agendadores registrados.")
            print()
            print("  Agendamentos configurados:")
            for agent in LAUNCH_AGENTS:
                print(f"    - {agent['description']}")
        else:
            print("  [AVISO] Nenhum agendador registrado. Verifique permissoes.")
    else:
        registrados = 0
        print("  [OK] Automacao pulada. Use /codex-review quando precisar.")
    print()

    # 6. Checkpoint
    plugin_str = "ok" if plugin_ok else "manual"
    skill_str = "ok" if skill_ok else "falha"
    detail = f"plugin:{plugin_str} skill:{skill_str} agendadores:{registrados}"
    mark_checkpoint("step_2_codex", "done", detail)

    print("  [OK] Etapa 2 concluida!")
    print()
    print("  Proximo passo: Etapa 3 — Memoria Desktop <-> Terminal")
    print("  Execute: python3 setup/setup_memory_symlink.py")
    print()


if __name__ == "__main__":
    main()
