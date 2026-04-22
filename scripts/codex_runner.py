#!/usr/bin/env python3
"""
Codex Runner — dispara revisao via plugin Codex do Claude Code.
"""

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib import WEEK4_LOGS_DIR, now_iso


def run_codex_review(effort: str = "medium", project: str = None) -> bool:
    """
    Roda revisao Codex via claude -p /codex:review.
    Retorna True se concluiu sem erro.
    """
    cmd = ["claude", "-p", f"/codex:review --effort {effort}"]
    if project:
        cmd = ["claude", "-p", f"/codex:review --effort {effort} --project {project}"]

    WEEK4_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = WEEK4_LOGS_DIR / f"codex_review_{now_iso().replace(':', '-')}.log"

    print(f"  Iniciando revisao Codex (effort: {effort})...")
    print(f"  Log: {log_path}")

    try:
        with open(log_path, "w", encoding="utf-8") as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                timeout=600,
            )
        if result.returncode == 0:
            print(f"  [OK] Revisao Codex concluida. Log: {log_path}")
            return True
        else:
            print(f"  [AVISO] Codex retornou codigo {result.returncode}. Verifique o log.")
            return False
    except subprocess.TimeoutExpired:
        print("  [AVISO] Revisao Codex excedeu timeout de 10 minutos.")
        return False
    except FileNotFoundError:
        print("  [ERRO] claude CLI nao encontrado. Instale o Claude Code.")
        return False
    except Exception as exc:
        print(f"  [ERRO] Falha ao rodar Codex: {exc}")
        return False


def run_rescue_review() -> bool:
    """Roda revisao de resgate via /codex:codex-rescue."""
    cmd = ["claude", "-p", "/codex:codex-rescue"]
    print("  Iniciando revisao de resgate Codex...")
    try:
        result = subprocess.run(cmd, timeout=300)
        return result.returncode == 0
    except Exception as exc:
        print(f"  [ERRO] Revisao de resgate falhou: {exc}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Dispara revisao Codex")
    parser.add_argument("--effort", default="medium", choices=["low", "medium", "high"])
    parser.add_argument("--project", default=None, help="Projeto especifico")
    parser.add_argument("--rescue", action="store_true", help="Revisao de resgate")
    args = parser.parse_args()

    if args.rescue:
        ok = run_rescue_review()
    else:
        ok = run_codex_review(effort=args.effort, project=args.project)

    sys.exit(0 if ok else 1)
