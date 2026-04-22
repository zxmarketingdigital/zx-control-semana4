#!/usr/bin/env python3
"""
Graphify Integration — instala e executa skill /graphify nos projetos ativos.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib import GRAPHS_DIR, now_iso

GRAPHIFY_SKILL_URL = "https://github.com/zxmarketingdigital/graphify-skill"
GRAPHIFY_SKILL_PATH = Path.home() / ".claude" / "skills" / "graphify"

ACTIVE_PROJECTS = [
    {"name": "operacao-ia", "path": "~/.operacao-ia"},
    {"name": "zx-control-s4", "path": "~/zx-control-semana4"},
    {"name": "agencia-ia-connect", "path": "~/agencia-ia-connect"},
]


def _run(cmd, capture=True, timeout=120):
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            timeout=timeout,
        )
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        return result.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Timeout"
    except FileNotFoundError:
        return 1, "", f"Comando nao encontrado: {cmd[0]}"
    except Exception as e:
        return 1, "", str(e)


def is_graphify_installed() -> bool:
    """Verifica se skill /graphify esta instalada."""
    if GRAPHIFY_SKILL_PATH.exists():
        return True
    code, out, _ = _run(["claude", "skill", "list"])
    return "graphify" in out.lower()


def install_graphify() -> bool:
    """Instala skill /graphify via claude skill install."""
    print(f"  Instalando skill /graphify...")
    code, out, err = _run(
        ["claude", "skill", "install", GRAPHIFY_SKILL_URL],
        capture=False,
        timeout=60,
    )
    if code == 0:
        print("  [OK] Skill /graphify instalada.")
        return True
    print(f"  [AVISO] Instalacao automatica falhou: {err}")
    print(f"  Instale manualmente: /skill install {GRAPHIFY_SKILL_URL}")
    return False


def run_graphify(project_name: str, project_path: str) -> dict:
    """Roda /graphify em um projeto. Retorna resultado."""
    expanded_path = str(Path(project_path).expanduser())
    if not Path(expanded_path).exists():
        return {"project": project_name, "status": "skipped", "reason": "path nao existe"}

    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = GRAPHS_DIR / f"{project_name}.json"

    print(f"  Mapeando: {project_name} ({expanded_path})")
    code, out, err = _run(
        ["claude", "-p", f"/graphify {expanded_path} --output {output_path}"],
        timeout=300,
    )

    if code == 0:
        print(f"  [OK] Grafo salvo: {output_path}")
        return {"project": project_name, "status": "ok", "output": str(output_path)}
    else:
        print(f"  [AVISO] Graphify falhou para {project_name}: {err[:100]}")
        return {"project": project_name, "status": "failed", "error": err[:200]}


def run_all_projects() -> list:
    """Roda /graphify em todos os projetos ativos."""
    results = []
    for proj in ACTIVE_PROJECTS:
        result = run_graphify(proj["name"], proj["path"])
        results.append(result)
    return results


def save_graph_registry(results: list):
    """Salva registro dos grafos gerados."""
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
    registry_path = GRAPHS_DIR / "registry.json"
    registry = {
        "last_run": now_iso(),
        "projects": results,
    }
    registry_path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  Registro salvo: {registry_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Graphify nos projetos ativos")
    parser.add_argument("--install-only", action="store_true")
    parser.add_argument("--project", default=None, help="Projeto especifico pelo nome")
    args = parser.parse_args()

    if not is_graphify_installed():
        install_graphify()

    if args.install_only:
        sys.exit(0)

    if args.project:
        proj = next((p for p in ACTIVE_PROJECTS if p["name"] == args.project), None)
        if proj:
            result = run_graphify(proj["name"], proj["path"])
            save_graph_registry([result])
        else:
            print(f"  [ERRO] Projeto '{args.project}' nao encontrado.")
            sys.exit(1)
    else:
        results = run_all_projects()
        save_graph_registry(results)
        ok = sum(1 for r in results if r["status"] == "ok")
        print(f"\n  {ok}/{len(results)} grafos gerados com sucesso.")
