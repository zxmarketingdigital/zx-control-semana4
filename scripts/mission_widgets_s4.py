#!/usr/bin/env python3
"""
Mission Widgets S4 — widgets de telemetria para o dashboard Mission Control.
Adiciona blocos Codex, Graphify e Session Log ao dashboard diario.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib import GRAPHS_DIR, SESSION_LOGS_DIR

CODEX_LOGS_DIR = Path.home() / ".codex" / "logs"
CODEX_PROJECTS_PATH = Path.home() / ".codex" / "automations" / "project-review" / "projects.json"


def _codex_widget() -> dict:
    """Status do revisor Codex."""
    result = {"label": "Codex Revisor", "status": "desconhecido", "detail": ""}

    if not CODEX_LOGS_DIR.exists():
        result["status"] = "nao configurado"
        return result

    logs = sorted(
        [p for p in CODEX_LOGS_DIR.glob("*.log") if p.exists()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if logs:
        last = logs[0]
        mtime = datetime.fromtimestamp(last.stat().st_mtime)
        result["status"] = "ativo"
        result["detail"] = f"ultimo: {mtime.strftime('%d/%m %H:%M')} ({last.name})"
    else:
        result["status"] = "configurado (sem execucoes)"

    if CODEX_PROJECTS_PATH.exists():
        try:
            data = json.loads(CODEX_PROJECTS_PATH.read_text(encoding="utf-8"))
            n = len(data.get("projects", []))
            result["projects"] = n
        except Exception:
            pass

    return result


def _graphify_widget() -> dict:
    """Status do segundo cerebro Graphify."""
    result = {"label": "Graphify", "status": "desconhecido", "detail": ""}

    registry_path = GRAPHS_DIR / "registry.json"
    if not registry_path.exists():
        result["status"] = "sem grafos"
        return result

    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        last_run = data.get("last_run", "")
        projects = data.get("projects", [])
        ok = sum(1 for p in projects if p.get("status") == "ok")
        result["status"] = "ativo"
        result["detail"] = f"{ok}/{len(projects)} projetos | ultimo: {last_run[:16]}"
    except Exception as exc:
        result["status"] = "erro"
        result["detail"] = str(exc)[:80]

    return result


def _session_log_widget() -> dict:
    """Ultimo log de sessao registrado."""
    result = {"label": "Session Log", "status": "sem registros", "detail": ""}

    if not SESSION_LOGS_DIR.exists():
        return result

    logs = sorted(
        [p for p in SESSION_LOGS_DIR.glob("*.json") if p.exists()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not logs:
        return result

    try:
        data = json.loads(logs[0].read_text(encoding="utf-8"))
        date = data.get("date", "")[:10]
        etapas = data.get("etapas_concluidas", 0)
        result["status"] = "registrado"
        result["detail"] = f"data: {date} | etapas: {etapas}"
    except Exception:
        result["status"] = "arquivo invalido"

    return result


def collect_all() -> dict:
    """Coleta todos os widgets S4."""
    return {
        "s4_widgets": {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "codex": _codex_widget(),
            "graphify": _graphify_widget(),
            "session_log": _session_log_widget(),
        }
    }


def print_summary(widgets: dict):
    """Imprime resumo formatado para o dashboard."""
    w = widgets.get("s4_widgets", {})
    print()
    print("  ── ZX Control S4 ──────────────────────")
    for key in ("codex", "graphify", "session_log"):
        block = w.get(key, {})
        label = block.get("label", key)
        status = block.get("status", "?")
        detail = block.get("detail", "")
        line = f"  {label:<22} {status}"
        if detail:
            line += f" | {detail}"
        print(line)
    print("  ────────────────────────────────────────")
    print()


if __name__ == "__main__":
    widgets = collect_all()
    print_summary(widgets)
    out_path = Path.home() / ".operacao-ia" / "data" / "mission_widgets_s4.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(widgets, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Widgets salvos: {out_path}")
