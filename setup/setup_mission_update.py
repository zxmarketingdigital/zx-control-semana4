#!/usr/bin/env python3
"""
Etapa 8 — Mission Control 2.0
Atualiza o ~/.zxlab-mission-control/ com widgets e monitoramento da Semana 4.
"""

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

MISSION_DIR = Path.home() / ".zxlab-mission-control"

# ---------------------------------------------------------------------------
# Progress bar
# ---------------------------------------------------------------------------

def progress_bar():
    print("\n[███████░░░] Etapa 8 de 10 — Mission Control 2.0\n")


# ---------------------------------------------------------------------------
# Patch helpers
# ---------------------------------------------------------------------------

def _read_file(path):
    """Le arquivo retornando texto ou None se nao existir."""
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  AVISO: nao foi possivel ler {path.name}: {e}")
        return None


def _write_file(path, content):
    """Escreve arquivo. Retorna True em sucesso."""
    try:
        path.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        print(f"  ERRO ao escrever {path.name}: {e}")
        return False


# ---------------------------------------------------------------------------
# Patch 1 — zx_daily_dashboard.py: adicionar _collect_week4_widgets()
# ---------------------------------------------------------------------------

WEEK4_WIDGETS_MARKER = "# ZX Control S4 Widgets"

WEEK4_WIDGETS_BLOCK = '''

# ZX Control S4 Widgets
def _collect_week4_widgets():
    """Coleta metricas da Semana 4 — Inteligencia & Escala."""
    import json
    from datetime import datetime
    widgets = {}
    # Codex reviews nas ultimas 24h
    codex_log = Path.home() / ".codex" / "logs" / "daily.log"
    if codex_log.exists():
        content = codex_log.read_text(errors="replace")
        today = datetime.now().strftime("%Y-%m-%d")
        widgets["codex_reviews_24h"] = content.count(today)
    else:
        widgets["codex_reviews_24h"] = 0
    # Graphify graphs
    graphs_dir = Path.home() / ".operacao-ia" / "graphs"
    if graphs_dir.exists():
        widgets["graphify_graphs"] = len(list(graphs_dir.glob("*/graph.json")))
    else:
        widgets["graphify_graphs"] = 0
    # Instagram auto replies
    ig_state = Path.home() / ".openclaw" / "workspace" / "ig_state.json"
    if ig_state.exists():
        try:
            data = json.loads(ig_state.read_text())
            widgets["ig_auto_replies_24h"] = data.get("replies_today", 0)
        except Exception:
            widgets["ig_auto_replies_24h"] = 0
    else:
        widgets["ig_auto_replies_24h"] = 0
    return widgets
'''


def patch_dashboard(n_aplicados):
    """Patch 1: adiciona _collect_week4_widgets() ao zx_daily_dashboard.py."""
    target = MISSION_DIR / "zx_daily_dashboard.py"
    content = _read_file(target)

    if content is None:
        print(f"  [SKIP] Arquivo nao encontrado: {target.name}")
        return n_aplicados

    if WEEK4_WIDGETS_MARKER in content:
        print(f"  [SKIP] Ja aplicado: {target.name}")
        return n_aplicados

    new_content = content + WEEK4_WIDGETS_BLOCK
    if _write_file(target, new_content):
        print(f"  [OK] Patch aplicado: {target.name}")
        return n_aplicados + 1
    return n_aplicados


# ---------------------------------------------------------------------------
# Patch 2 — heartbeat.py: adicionar agentes esperados da S4
# ---------------------------------------------------------------------------

S4_AGENTS = [
    "com.zxlab.codex-review-daily",
    "com.zxlab.codex-review-morning",
    "com.zxlab.codex-review-weekly",
    "com.zxlab.ig-auto-responder",
]

HEARTBEAT_S4_MARKER = "codex-review-daily"

HEARTBEAT_S4_BLOCK = '''
# ZX Control S4 — Agentes esperados
_S4_EXPECTED_AGENTS = [
    "com.zxlab.codex-review-daily",
    "com.zxlab.codex-review-morning",
    "com.zxlab.codex-review-weekly",
    "com.zxlab.ig-auto-responder",
]
'''


def patch_heartbeat(n_aplicados):
    """Patch 2: adiciona agentes S4 ao heartbeat.py."""
    target = MISSION_DIR / "heartbeat.py"
    content = _read_file(target)

    if content is None:
        print(f"  [SKIP] Arquivo nao encontrado: {target.name}")
        return n_aplicados

    if HEARTBEAT_S4_MARKER in content:
        print(f"  [SKIP] Ja aplicado: {target.name}")
        return n_aplicados

    new_content = content + HEARTBEAT_S4_BLOCK
    if _write_file(target, new_content):
        print(f"  [OK] Patch aplicado: {target.name}")
        return n_aplicados + 1
    return n_aplicados


# ---------------------------------------------------------------------------
# Patch 3 — health-checker.py: registrar novas skills da S4
# ---------------------------------------------------------------------------

HEALTH_S4_MARKER = "# ZX Control S4 Skills"

HEALTH_S4_BLOCK = '''
# ZX Control S4 Skills
_S4_SKILLS = [
    "/codex-review",
    "/graph-refresh",
    "/ig-status",
    "/ig-pausar",
    "/ig-retomar",
]
'''


def patch_health_checker(n_aplicados):
    """Patch 3: registra skills S4 no health-checker.py."""
    target = MISSION_DIR / "health-checker.py"
    content = _read_file(target)

    if content is None:
        print(f"  [SKIP] Arquivo nao encontrado: {target.name}")
        return n_aplicados

    if "# ZX Control S4 Skills" in content:
        print(f"  [SKIP] Ja aplicado: {target.name}")
        return n_aplicados

    new_content = content + HEALTH_S4_BLOCK
    if _write_file(target, new_content):
        print(f"  [OK] Patch aplicado: {target.name}")
        return n_aplicados + 1
    return n_aplicados


# ---------------------------------------------------------------------------
# Patch 4 — config-backup.py: adicionar paths de backup
# ---------------------------------------------------------------------------

BACKUP_S4_MARKER = "# ZX Control S4 Backup"

# Paths novos a adicionar
BACKUP_NEW_ENTRIES = [
    "    # ZX Control S4 Backup\n",
    "    '~/.codex/',\n",
    "    '~/.openclaw/workspace/.env',\n",
]

# Anchor: ultima linha da lista BACKUP_TARGETS (antes do fechamento '])
BACKUP_LIST_CLOSE = "]\n"


def patch_config_backup(n_aplicados):
    """Patch 4: adiciona ~/.codex/ e ~/.openclaw/workspace/.env ao config-backup.py."""
    target = MISSION_DIR / "config-backup.py"
    content = _read_file(target)

    if content is None:
        print(f"  [SKIP] Arquivo nao encontrado: {target.name}")
        return n_aplicados

    if BACKUP_S4_MARKER in content:
        print(f"  [SKIP] Ja aplicado: {target.name}")
        return n_aplicados

    # Estrategia: append do bloco ao final do arquivo
    s4_block = (
        "\n\n# ZX Control S4 Backup — paths adicionais\n"
        "_S4_BACKUP_PATHS = [\n"
        "    '~/.codex/',\n"
        "    '~/.openclaw/workspace/.env',\n"
        "]\n"
        "# Mesclar com BACKUP_TARGETS em runtime\n"
        "try:\n"
        "    BACKUP_TARGETS.extend(_S4_BACKUP_PATHS)\n"
        "except NameError:\n"
        "    pass\n"
    )

    new_content = content + s4_block
    if _write_file(target, new_content):
        print(f"  [OK] Patch aplicado: {target.name}")
        return n_aplicados + 1
    return n_aplicados


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

    print("  Etapa 8 — Mission Control 2.0")
    print()
    print("  Aplica 4 patches ao ~/.zxlab-mission-control/ para")
    print("  monitorar os sistemas instalados na Semana 4.")
    print()

    ensure_structure()

    # Verificar se MISSION_DIR existe
    if not MISSION_DIR.exists():
        print(f"  AVISO: Mission Control nao encontrado em {MISSION_DIR}")
        print("  Os patches serao no-op. Nenhum arquivo sera modificado.")
        print()
        print("  Para instalar o Mission Control, acesse:")
        print("  https://github.com/zxmarketingdigital/zxlab-mission-control")
        print()
        mark_checkpoint("step_8_mission_control", "done", "patches: 0/4 (MISSION_DIR ausente)")
        print("  [OK] Etapa 8 concluida — Mission Control nao encontrado (no-op).\n")
        return

    print(f"  Mission Control encontrado: {MISSION_DIR}")
    print()

    n_aplicados = 0

    # Patch 1 — zx_daily_dashboard.py
    print("  Patch 1 — Dashboard widgets S4...")
    try:
        n_aplicados = patch_dashboard(n_aplicados)
    except Exception as e:
        print(f"  ERRO no patch 1: {e}")

    # Patch 2 — heartbeat.py
    print("  Patch 2 — Heartbeat agentes S4...")
    try:
        n_aplicados = patch_heartbeat(n_aplicados)
    except Exception as e:
        print(f"  ERRO no patch 2: {e}")

    # Patch 3 — health-checker.py
    print("  Patch 3 — Health Checker skills S4...")
    try:
        n_aplicados = patch_health_checker(n_aplicados)
    except Exception as e:
        print(f"  ERRO no patch 3: {e}")

    # Patch 4 — config-backup.py
    print("  Patch 4 — Config Backup paths S4...")
    try:
        n_aplicados = patch_config_backup(n_aplicados)
    except Exception as e:
        print(f"  ERRO no patch 4: {e}")

    print()
    print(f"  Resultado: {n_aplicados}/4 patches aplicados")
    print()

    mark_checkpoint("step_8_mission_control", "done", f"patches: {n_aplicados}/4")

    print("  [OK] Etapa 8 concluida — Mission Control 2.0 atualizado!\n")
    print("  Proximo passo: Etapa 9 — Auditoria Tecnica")
    print("  Execute: python3 setup/setup_audit_s4.py")
    print()


if __name__ == "__main__":
    main()
