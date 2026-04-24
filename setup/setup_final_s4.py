#!/usr/bin/env python3
"""
Etapa 10 — Finalizacao + Log de Sessao + ZX Control 2.0
Encerramento oficial da Semana 4.
"""

import sys
from pathlib import Path

# Adiciona scripts/ ao path antes de qualquer import local
ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib import (
    CHECKPOINT_PATH,
    now_iso,
    load_config,
    save_config,
    mark_checkpoint,
    open_in_browser,
)
import session_logger
import supabase_log_push
import review_orchestrator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_progress(step, total=8, label=""):
    filled = "█" * step
    empty = "░" * (total - step)
    print(f"\n  [{filled}{empty}] Etapa 8 de 8")
    if label:
        print(f"  {label}")


def _sep():
    print("  " + "─" * 52)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║  ZX Control — Semana 4                          ║")
    print("  ║  Etapa 8 — Finalizacao + Log + ZX Control 2.0   ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print()

    # Carrega config (necessario para Supabase push)
    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as exc:
        print(f"  Aviso: config.json indisponivel ({exc}). Continuando sem Supabase.")
        config = {}

    # ------------------------------------------------------------------ [1/8]
    _print_progress(1, label="[1/8] Coletar dados da sessao")
    _sep()

    session_data = session_logger.collect(CHECKPOINT_PATH)

    dur_min = session_data["duration_seconds"] // 60
    dur_sec = session_data["duration_seconds"] % 60
    done_count = sum(
        1 for v in session_data["checkpoints"].values()
        if isinstance(v, dict) and v.get("status") == "done"
    )
    total_steps = max(len(session_data["checkpoints"]), 10)

    print(f"  Plataforma  : {session_data['platform']}")
    print(f"  Iniciado em : {session_data['started_at']}")
    print(f"  Duracao     : {dur_min}min {dur_sec}s")
    print(f"  Concluidos  : {done_count}/{total_steps} etapas")

    if session_data["errors"]:
        print(f"  Pendencias  : {len(session_data['errors'])} etapa(s) incompleta(s)")
        for err in session_data["errors"]:
            print(f"    - {err['step']}: {err['detail']}")

    # ------------------------------------------------------------------ [2/8]
    _print_progress(2, label="[2/8] Coletar feedback do aluno")
    _sep()
    print()

    feedback = ""
    try:
        feedback = session_logger.ask_feedback()
    except Exception as e:
        print(f"  (Feedback ignorado: {e})")

    # ------------------------------------------------------------------ [3/8]
    _print_progress(3, label="[3/8] Salvar log (JSON + MD)")
    _sep()

    json_path, md_path = session_logger.write(session_data, feedback)

    print(f"  JSON: {json_path}")
    print(f"  MD  : {md_path}")

    # ------------------------------------------------------------------ [4/8]
    _print_progress(4, label="[4/8] Enviar log para Supabase")
    _sep()

    # Limpa pendentes primeiro
    if config.get("supabase_url") and config.get("supabase_anon_key"):
        pending_result = supabase_log_push.push_pending(config)
        if pending_result["sent"]:
            print(f"  Pendentes enviados: {len(pending_result['sent'])}")
    else:
        print("  Supabase nao configurado — pulando limpeza de pendentes.")

    # Envia log atual
    success, error = supabase_log_push.push_with_retry(json_path, config)
    if success:
        print("  Seu log foi enviado!")
    else:
        print(f"  Log salvo localmente. Sera enviado na proxima sessao.")
        if error:
            print(f"  Detalhe: {error}")

    # ------------------------------------------------------------------ [5/8]
    _print_progress(5, label="[5/8] Revisao opt-in")
    _sep()
    print()

    try:
        resp = input("  Rodar revisao final? [S/n]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        resp = "n"
        print("  [non-TTY] Revisao pulada automaticamente.")
    if resp not in ("n", "nao", "no"):
        choice = review_orchestrator.choose()
        review_orchestrator.run_review(choice)
    else:
        print("  Revisao pulada.")

    # ------------------------------------------------------------------ [6/8]
    _print_progress(6, label="[6/8] Atualizar config.json")
    _sep()

    config["phase_completed"] = 4
    config["week4"] = {
        "completed": True,
        "completed_at": now_iso(),
    }
    try:
        save_config(config)
        print("  config.json atualizado: phase_completed=4, week4.completed=True")
    except Exception as e:
        print(f"  Aviso: nao foi possivel salvar config.json: {e}")

    # ------------------------------------------------------------------ [7/8]
    _print_progress(7, label="[7/8] ZX Control 2.0")
    _sep()
    print()

    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║                                                      ║")
    print("  ║   PARABENS! Voce concluiu os 30 dias do ZX Control! ║")
    print("  ║                                                      ║")
    print("  ║   Proximo nivel: ZX Control 2.0 — Turma 2            ║")
    print("  ║   Primeira semana de maio/2026                       ║")
    print("  ║                                                      ║")
    print("  ║   Novidades:                                         ║")
    print("  ║   - Multi-agentes autonomos                          ║")
    print("  ║   - Admin Panel web                                  ║")
    print("  ║   - Novas integracoes                                ║")
    print("  ║                                                      ║")
    print("  ║   No formato ASSINATURA:                             ║")
    print("  ║   ✓ 50% OFF vitalicio enquanto ativo                 ║")
    print("  ║   ✓ Acesso as versoes futuras                        ║")
    print("  ║   ✓ Cancele quando quiser                            ║")
    print("  ║                                                      ║")
    print("  ║   GARANTA SUA VAGA:                                  ║")
    print("  ║   https://zx-control-renovacao.pages.dev/            ║")
    print("  ║                                                      ║")
    print("  ║   © 2026 ZX LAB — Rafael Castro                      ║")
    print("  ║                                                      ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print()
    try:
        import webbrowser
        webbrowser.open("https://zx-control-renovacao.pages.dev/")
    except Exception:
        pass

    # ------------------------------------------------------------------ [8/8]
    _print_progress(8, label="[8/8] Abrir area de membros")
    _sep()

    area_membros = (
        Path.home() / "projetos" / "zx-control-semana1" / "docs" / "area-membros.html"
    )
    if area_membros.exists():
        open_in_browser(area_membros)
        print(f"  Abrindo: {area_membros}")
    else:
        print("  Acesse sua area de membros em: https://zx-control.zxlab.com.br")

    # Marca checkpoint
    mark_checkpoint("step_8_final_s4", "done", "Semana 4 concluida")

    # Mensagem final
    print()
    print("  " + "═" * 52)
    print()
    print("  Semana 4 concluida!")
    print()
    print("  O que voce tem agora:")
    print("  - Skill /codex-review para revisar projetos sob demanda")
    print("  - Memoria unificada Desktop + Terminal")
    print("  - Skills e MCPs sincronizados")
    print("  - Graphify economizando 60-90% tokens em projetos")
    print("  - Mission Control 2.0 com dashboard das 4 semanas")
    print()
    print("  Nos vemos na Turma 2 do ZX Control!")
    print()


if __name__ == "__main__":
    main()
