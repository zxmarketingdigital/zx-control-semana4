#!/usr/bin/env python3
"""
Etapa 1 — Base Semana 4
Boas-vindas, diagnostico e criacao da estrutura para S4.
"""

import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib import (
    CODEX_AUTOMATIONS_DIR,
    CODEX_DIR,
    GRAPHS_DIR,
    PLATFORM,
    SESSION_LOGS_DIR,
    WEEK4_LOGS_DIR,
    ensure_structure,
    load_config,
    mark_checkpoint,
    now_iso,
    save_config,
)


def ask(prompt, secret=False):
    import getpass
    try:
        if secret:
            value = getpass.getpass(f"  {prompt}: ").strip()
        else:
            value = input(f"  {prompt}: ").strip()
        return value
    except (KeyboardInterrupt, EOFError):
        print()
        print("  Setup cancelado.")
        sys.exit(0)


def check_phase(config):
    """Verifica se Semanas 1, 2 e 3 foram concluidas."""
    phase = config.get("phase_completed", 0)
    if phase < 3:
        print()
        print("  ATENCAO: Semanas 1, 2 e 3 nao foram concluidas.")
        print(f"  phase_completed atual: {phase} (esperado: >= 3)")
        print()
        print("  Conclua as semanas anteriores antes de continuar:")
        print("    Semana 1: ~/zx-control-semana1/")
        print("    Semana 2: ~/zx-control-semana2/")
        print("    Semana 3: ~/zx-control-semana3/")
        print()
        sys.exit(1)


def detect_scheduler():
    """Detecta se launchctl (macOS), schtasks (Windows) ou cron (Linux) esta disponivel."""
    if PLATFORM == "Darwin":
        path = shutil.which("launchctl")
        if path:
            print(f"  [OK] launchctl encontrado: {path}")
        else:
            print("  [AVISO] launchctl nao encontrado (incomum no macOS).")
        return "launchctl"
    elif PLATFORM == "Windows":
        path = shutil.which("schtasks")
        if path:
            print(f"  [OK] schtasks encontrado: {path}")
        else:
            print("  [AVISO] schtasks nao encontrado no PATH.")
        return "schtasks"
    else:
        path = shutil.which("cron") or shutil.which("crontab")
        if path:
            print(f"  [OK] cron encontrado: {path}")
        else:
            print("  [AVISO] cron nao encontrado. Instale com: sudo apt install cron")
        return "cron"


def print_plan():
    steps = [
        ("Etapa 1", "Base S4              — Ambiente e estrutura de diretorios (este script)"),
        ("Etapa 2", "Codex CLI            — Instalacao do Codex e revisor diario agendado"),
        ("Etapa 3", "Instagram Agents     — Agentes IA para DM e comentarios"),
        ("Etapa 4", "Knowledge Graphs     — Graphify: base de conhecimento automatizada"),
        ("Etapa 5", "Multi-Channel Scale  — Escala simultânea WhatsApp + Email + Instagram"),
        ("Etapa 6", "Analytics Engine     — Dashboard de metricas consolidadas"),
        ("Etapa 7", "A/B Testing          — Teste automatico de copys e sequencias"),
        ("Etapa 8", "Autonomia Total      — Agente 24/7 sem intervencao manual"),
        ("Etapa 9", "Integracao CRM       — Sincronizacao bidirecional com CRM"),
        ("Etapa 10", "Finalizacao S4      — Auditoria final e proximos passos"),
    ]
    print()
    print("  Plano completo — 10 etapas:")
    print()
    for label, desc in steps:
        print(f"    {label}: {desc}")
    print()


def main():
    print()
    print("=" * 52)
    print("  ZX Control — Semana 4: Inteligencia & Escala")
    print("=" * 52)
    print()
    print("  [█░░░░░░░░░] Etapa 1 de 10")
    print()
    print("  Bem-vindo(a) ao setup da Semana 4!")
    print()
    print("  Nesta semana voce vai expandir sua operacao IA para")
    print("  escala real: Codex CLI, agentes Instagram, grafos de")
    print("  conhecimento, analytics e autonomia 24/7.")
    print()

    # --- Carrega config e valida fases anteriores ---
    print("  Verificando pre-requisitos...")
    try:
        config = load_config()
    except FileNotFoundError:
        print()
        print("  ERRO: config.json nao encontrado.")
        print("  Execute primeiro o setup das Semanas 1, 2 e 3.")
        sys.exit(1)

    check_phase(config)
    print("  [OK] Semanas 1, 2 e 3 concluidas.")
    print()

    # --- Detecta e salva plataforma ---
    print(f"  Sistema operacional: {PLATFORM}")
    config["platform"] = PLATFORM

    # --- Versao do Python ---
    pv = sys.version.split()[0]
    major, minor = sys.version_info.major, sys.version_info.minor
    print(f"  Python: {pv}")
    if major < 3 or (major == 3 and minor < 9):
        print()
        print(f"  ERRO: Python 3.9+ necessario. Versao atual: {pv}")
        print("  Atualize o Python em https://python.org/downloads")
        sys.exit(1)
    print("  [OK] Python >= 3.9 disponivel.")
    print()

    # --- Verifica Node.js ---
    print("  Verificando Node.js (necessario para Codex na Etapa 2)...")
    node_path = shutil.which("node")
    if node_path:
        print(f"  [OK] Node.js encontrado: {node_path}")
        node_ok = "sim"
    else:
        print("  [AVISO] Node.js nao encontrado.")
        print("  A Etapa 2 (Codex) vai precisar dele.")
        print("  Instale em: https://nodejs.org")
        node_ok = "nao"
    print()

    # --- Verifica agendador do sistema ---
    print("  Verificando agendador de tarefas...")
    scheduler = detect_scheduler()
    config["scheduler"] = scheduler
    print()

    # --- Cria estrutura de diretorios ---
    print("  Criando estrutura de diretorios...")
    ensure_structure()
    print("  [OK] Estrutura base criada em ~/.operacao-ia/")

    for dir_path, label in [
        (WEEK4_LOGS_DIR, "WEEK4_LOGS_DIR"),
        (SESSION_LOGS_DIR, "SESSION_LOGS_DIR"),
        (GRAPHS_DIR, "GRAPHS_DIR"),
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  [OK] {label}: {dir_path}")
    print()

    # --- Plano das 10 etapas ---
    print_plan()

    # --- PROMO ---
    print("  ╔═══════════════════════════════════════╗")
    print("  ║  ZX Control 2.0 — Turma 2            ║")
    print("  ║  Primeira semana de maio/2026         ║")
    print("  ║  50% OFF vitalicio no formato         ║")
    print("  ║  assinatura enquanto ativo            ║")
    print("  ╚═══════════════════════════════════════╝")
    print()

    # --- Salva config ---
    save_config(config)
    print("  [OK] config.json atualizado.")
    print()

    # --- Checkpoint ---
    detail = f"Platform:{PLATFORM} Python:{pv} Node:{node_ok}"
    mark_checkpoint("step_1_base_s4", "done", detail)

    print("  [OK] Etapa 1 concluida!")
    print()
    print("  Proximo passo: Etapa 2 — Codex CLI + Revisor Diario")
    print("  Execute: python3 setup/setup_codex.py")
    print()


if __name__ == "__main__":
    main()
