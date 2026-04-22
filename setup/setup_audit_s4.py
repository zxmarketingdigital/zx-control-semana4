#!/usr/bin/env python3
"""
Etapa 9 — Auditoria Tecnica
Verifica 15 componentes instalados nas Semanas 1-4 e corrige automaticamente.
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib import (
    CODEX_DIR,
    GRAPHS_DIR,
    PLATFORM,
    SESSION_LOGS_DIR,
    ensure_structure,
    load_checkpoint,
    load_config,
    mark_checkpoint,
    now_iso,
)

LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"
SYSTEMD_USER_DIR = Path.home() / ".config" / "systemd" / "user"
MISSION_DIR = Path.home() / ".zxlab-mission-control"


# ---------------------------------------------------------------------------
# Progress bar
# ---------------------------------------------------------------------------

def progress_bar():
    print("\n[█████████░] Etapa 9 de 10 — Auditoria Tecnica\n")


# ---------------------------------------------------------------------------
# Resultado formatado
# ---------------------------------------------------------------------------

def _fmt(idx, total, label, status, msg):
    """Formata linha de resultado: [N/15] Label   [STATUS] mensagem"""
    counter = f"[{idx}/{total}]"
    status_tag = f"[{status}]"
    return f"  {counter:<7} {label:<30} {status_tag:<9} {msg}"


# ---------------------------------------------------------------------------
# Checks individuais
# ---------------------------------------------------------------------------

def check_claude_cli():
    """Check 1: Claude Code CLI instalado."""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.strip().split("\n")[0]
            return ("OK", version or "instalado")
        return ("AVISO", "claude retornou codigo " + str(result.returncode))
    except FileNotFoundError:
        return ("ERRO", "claude nao encontrado no PATH")
    except Exception as e:
        return ("ERRO", str(e))


def check_codex_plugin():
    """Check 2: Plugin Codex instalado (via checkpoint ou claude plugin list)."""
    # Primeiro: checar checkpoint da etapa 2
    try:
        cp = load_checkpoint()
        step = cp.get("steps", {}).get("step_2_codex", {})
        if step.get("status") == "done":
            return ("OK", f"checkpoint: {step.get('detail', 'instalado')}")
    except Exception:
        pass

    # Fallback: tentar claude plugin list
    try:
        result = subprocess.run(
            ["claude", "plugin", "list"],
            capture_output=True, text=True, timeout=15
        )
        output = result.stdout + result.stderr
        if "codex-plugin-cc" in output.lower() or "codex" in output.lower():
            return ("OK", "encontrado via plugin list")
        return ("AVISO", "nao detectado via plugin list")
    except Exception:
        return ("AVISO", "nao foi possivel verificar (claude plugin list falhou)")


def check_memory_symlink():
    """Check 3: Memory symlink Desktop -> Terminal."""
    import getpass
    projects_base = Path.home() / ".claude" / "projects"
    if not projects_base.exists():
        return ("AVISO", "~/.claude/projects nao existe")

    try:
        candidates = [
            p for p in projects_base.iterdir()
            if p.is_dir() and "Documents-Claude" in p.name
        ]
    except Exception:
        return ("AVISO", "nao foi possivel listar projetos")

    if not candidates:
        return ("AVISO", "pasta Desktop nao encontrada (pode nao ter usado Claude Desktop)")

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    desktop_mem = candidates[0] / "memory"

    if desktop_mem.is_symlink():
        target = desktop_mem.resolve()
        username = getpass.getuser()
        terminal_mem = projects_base / f"-Users-{username}" / "memory"
        if target == terminal_mem.resolve():
            return ("OK", f"Desktop -> Terminal")
        return ("AVISO", f"symlink existe mas aponta para: {target}")

    if desktop_mem.exists():
        return ("AVISO", "Desktop memory existe como diretorio real (sem symlink)")

    return ("AVISO", "Desktop memory nao encontrada")


def check_skills_git():
    """Check 4: Skills sync git repo existe."""
    skills_git = Path.home() / ".claude" / "skills" / ".git"
    if skills_git.exists():
        return ("OK", str(skills_git.parent))
    return ("AVISO", "~/.claude/skills/.git nao encontrado")


def check_skills_launchagent():
    """Check 5: Skills LaunchAgent / systemd timer configurado."""
    if PLATFORM == "Darwin":
        plist = LAUNCH_AGENTS_DIR / "com.zxlab.skills-sync.plist"
        if plist.exists():
            return ("OK", str(plist))
        return ("AVISO", "com.zxlab.skills-sync.plist nao encontrado")
    elif PLATFORM == "Linux":
        timer = SYSTEMD_USER_DIR / "zxlab-skills-sync.timer"
        if timer.exists():
            return ("OK", str(timer))
        return ("AVISO", "systemd timer nao encontrado")
    else:
        return ("AVISO", f"Plataforma {PLATFORM} — verificacao manual necessaria")


def check_graphify_dir():
    """Check 6: Graphify dir existe com pelo menos 1 subdir. Auto-fix: criar dir."""
    graphs = GRAPHS_DIR
    if not graphs.exists():
        try:
            graphs.mkdir(parents=True, exist_ok=True)
            return ("AVISO", f"criado agora: {graphs} (ainda vazio)")
        except Exception as e:
            return ("ERRO", f"nao foi possivel criar: {e}")

    subdirs = [p for p in graphs.iterdir() if p.is_dir()]
    if subdirs:
        return ("OK", f"{len(subdirs)} graph(s) encontrado(s)")
    return ("AVISO", f"diretorio existe mas vazio: {graphs}")


def check_ig_token():
    """Check 7: ig_state.json com token_valid == true."""
    ig_state = Path.home() / ".openclaw" / "workspace" / "ig_state.json"
    if not ig_state.exists():
        return ("AVISO", "ig_state.json nao encontrado")
    try:
        data = json.loads(ig_state.read_text(encoding="utf-8"))
        if data.get("token_valid") is True:
            return ("OK", "token valido")
        return ("AVISO", f"token_valid={data.get('token_valid')} — executar etapa 5")
    except Exception as e:
        return ("ERRO", f"nao foi possivel ler ig_state.json: {e}")


def check_ig_responder_script():
    """Check 8: ig_auto_responder.py existe."""
    script = Path.home() / ".openclaw" / "workspace" / "scripts" / "ig_auto_responder.py"
    if script.exists():
        return ("OK", str(script))
    return ("AVISO", "ig_auto_responder.py nao encontrado — executar etapa 6")


def check_ig_cron():
    """Check 9: ig_auto_responder agendado (crontab Darwin/Linux ou schtasks Windows)."""
    if PLATFORM == "Windows":
        try:
            result = subprocess.run(
                ["schtasks", "/query", "/fo", "LIST"],
                capture_output=True, text=True, timeout=10
            )
            if "ig_auto_responder" in result.stdout:
                return ("OK", "schtasks encontrado")
            return ("AVISO", "nao encontrado em schtasks")
        except Exception:
            return ("AVISO", "nao foi possivel verificar schtasks")
    else:
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True, text=True, timeout=10
            )
            if "ig_auto_responder" in result.stdout:
                return ("OK", "entrada no crontab encontrada")
            # Checar tambem LaunchAgent (macOS)
            if PLATFORM == "Darwin":
                plist = LAUNCH_AGENTS_DIR / "com.zxlab.ig-auto-responder.plist"
                if plist.exists():
                    return ("OK", "LaunchAgent encontrado")
            return ("AVISO", "nao encontrado no crontab/LaunchAgent")
        except Exception:
            return ("AVISO", "nao foi possivel verificar crontab")


def check_codex_launchagent():
    """Check 10: Codex daily LaunchAgent existe (Darwin) ou timer (Linux)."""
    if PLATFORM == "Darwin":
        plist = LAUNCH_AGENTS_DIR / "com.zxlab.codex-review-daily.plist"
        if plist.exists():
            return ("OK", str(plist))
        return ("AVISO", "com.zxlab.codex-review-daily.plist nao encontrado — executar etapa 2")
    elif PLATFORM == "Linux":
        timer = SYSTEMD_USER_DIR / "zxlab-codex-review-daily.timer"
        if timer.exists():
            return ("OK", str(timer))
        return ("AVISO", "systemd timer nao encontrado — executar etapa 2")
    else:
        return ("AVISO", f"Plataforma {PLATFORM} — verificacao manual necessaria")


def check_codex_projects():
    """Check 11: Codex projects.json existe."""
    projects_json = CODEX_DIR / "automations" / "project-review" / "projects.json"
    if projects_json.exists():
        try:
            data = json.loads(projects_json.read_text(encoding="utf-8"))
            n = len(data) if isinstance(data, list) else len(data.get("projects", []))
            return ("OK", f"{n} projeto(s) configurado(s)")
        except Exception:
            return ("OK", "existe (conteudo invalido — verificar)")
    return ("AVISO", "projects.json nao encontrado — executar etapa 2")


def check_config_phase():
    """Check 12: config.json com phase >= 3."""
    try:
        config = load_config()
        phase = config.get("phase", config.get("semana", config.get("week", None)))
        if phase is None:
            return ("AVISO", "campo 'phase' nao encontrado no config.json")
        try:
            phase_num = int(str(phase).replace("semana", "").replace("week", "").strip())
        except Exception:
            return ("AVISO", f"phase={phase} (nao numerico)")
        if phase_num >= 3:
            return ("OK", f"phase={phase}")
        return ("AVISO", f"phase={phase} — executar etapas anteriores")
    except FileNotFoundError:
        return ("AVISO", "config.json nao encontrado — executar etapa 1")
    except Exception as e:
        return ("ERRO", str(e))


def check_s4_checkpoints():
    """Check 13: Checkpoints S4 etapas 1-8 com status done."""
    try:
        cp = load_checkpoint()
        steps = cp.get("steps", {})
        expected = [f"step_{i}" for i in range(1, 9)]
        done = []
        for key, val in steps.items():
            # Match qualquer step_N (ex: step_1_base, step_2_codex, etc.)
            for exp in expected:
                if key.startswith(exp) and val.get("status") == "done":
                    done.append(key)
                    break
        n = len(done)
        if n >= 7:
            return ("OK", f"{n}/8 etapas concluidas")
        return ("AVISO", f"{n}/8 etapas concluidas — completar etapas pendentes")
    except Exception as e:
        return ("AVISO", f"nao foi possivel ler checkpoint: {e}")


def check_mission_control():
    """Check 14: Mission Control dir existe."""
    if MISSION_DIR.exists():
        n_files = len(list(MISSION_DIR.iterdir()))
        return ("OK", f"{n_files} arquivos em {MISSION_DIR}")
    return ("AVISO", f"{MISSION_DIR} nao encontrado")


def check_session_logs_dir():
    """Check 15: Session logs dir existe. Auto-fix: criar se ausente."""
    logs = SESSION_LOGS_DIR
    if logs.exists():
        return ("OK", str(logs))
    try:
        logs.mkdir(parents=True, exist_ok=True)
        return ("OK", f"criado agora: {logs}")
    except Exception as e:
        return ("ERRO", f"nao foi possivel criar: {e}")


# ---------------------------------------------------------------------------
# Executor de checks
# ---------------------------------------------------------------------------

CHECKS = [
    ("Claude Code CLI",           check_claude_cli),
    ("Plugin Codex",              check_codex_plugin),
    ("Memory symlink",            check_memory_symlink),
    ("Skills sync git repo",      check_skills_git),
    ("Skills LaunchAgent",        check_skills_launchagent),
    ("Graphify dir",              check_graphify_dir),
    ("IG token valido",           check_ig_token),
    ("IG auto-responder script",  check_ig_responder_script),
    ("IG cron/agendador",         check_ig_cron),
    ("Codex LaunchAgent daily",   check_codex_launchagent),
    ("Codex projects.json",       check_codex_projects),
    ("Config.json phase >= 3",    check_config_phase),
    ("Checkpoints S4 etapas 1-8", check_s4_checkpoints),
    ("Mission Control dir",       check_mission_control),
    ("Session logs dir",          check_session_logs_dir),
]

TOTAL = len(CHECKS)


def run_all_checks():
    results = []
    for idx, (label, fn) in enumerate(CHECKS, start=1):
        try:
            status, msg = fn()
        except Exception as e:
            status, msg = "ERRO", f"excecao inesperada: {e}"
        line = _fmt(idx, TOTAL, label, status, msg)
        print(line)
        results.append((label, status, msg))
    return results


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

    print("  Etapa 9 — Auditoria Tecnica")
    print()
    print("  Verificando 15 componentes instalados nas Semanas 1-4.")
    print("  Fixes automaticos serao aplicados onde possivel.")
    print()

    ensure_structure()

    results = run_all_checks()

    # Contagem
    ok = sum(1 for _, status, _ in results if status == "OK")
    avisos = sum(1 for _, status, _ in results if status == "AVISO")
    erros = sum(1 for _, status, _ in results if status == "ERRO")

    print()
    print(f"  Resultado: {ok}/{TOTAL} checks passaram", end="")
    if avisos:
        print(f"  |  {avisos} aviso(s)", end="")
    if erros:
        print(f"  |  {erros} erro(s)", end="")
    print()
    print()

    # Mostrar itens com AVISO ou ERRO para facilitar acao
    pendentes = [(label, status, msg) for label, status, msg in results if status != "OK"]
    if pendentes:
        print("  Itens que precisam de atencao:")
        for label, status, msg in pendentes:
            print(f"    [{status}] {label}: {msg}")
        print()

    detail = f"{ok}/{TOTAL} checks passaram"
    mark_checkpoint("step_9_audit_s4", "done", detail)

    print("  [OK] Etapa 9 concluida — Auditoria Tecnica finalizada!\n")
    print("  Proximo passo: Etapa 10 — Finalizacao")
    print("  Execute: python3 setup/setup_base_s4.py --finalize (ou etapa 10)")
    print()


if __name__ == "__main__":
    main()
