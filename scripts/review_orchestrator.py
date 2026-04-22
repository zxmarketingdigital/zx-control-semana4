#!/usr/bin/env python3
"""
review_orchestrator.py — Decide qual ferramenta de revisao usar no encerramento.
Prioridade: /encerrar > Codex plugin > Claude Opus.
"""

import subprocess
import sys
from pathlib import Path

# Adiciona scripts/ ao path para importar lib
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# Caminho da skill /encerrar
_ENCERRAR_SKILL_PATH = Path.home() / ".claude" / "skills" / "encerrar" / "SKILL.md"

# Nome do plugin Codex esperado
_CODEX_PLUGIN_NAME = "codex-plugin-cc"


def detect_encerrar():
    """
    Verifica se a skill /encerrar esta instalada.

    Returns:
        bool: True se SKILL.md existe, False caso contrario
    """
    return _ENCERRAR_SKILL_PATH.exists()


def detect_codex_plugin():
    """
    Verifica se o codex-plugin-cc esta instalado via `claude plugin list`.

    Returns:
        bool: True se o plugin foi encontrado, False caso contrario
    """
    try:
        result = subprocess.run(
            ["claude", "plugin", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout + result.stderr
        return _CODEX_PLUGIN_NAME in output
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def choose():
    """
    Escolhe a ferramenta de revisao com base na disponibilidade.
    Prioridade: encerrar > codex > opus > none

    Returns:
        str: "encerrar" | "codex" | "opus" | "none"
    """
    if detect_encerrar():
        return "encerrar"
    if detect_codex_plugin():
        return "codex"
    # Opus sempre disponivel como fallback via instrucao manual
    return "opus"


def run_review(choice):
    """
    Executa a revisao conforme a escolha.

    Args:
        choice: str retornado por choose()
    """
    if choice == "encerrar":
        print()
        print("  Skill /encerrar detectada!")
        print()
        print("  Para rodar a revisao final, abra o Claude Code e execute:")
        print()
        print("    /encerrar")
        print()
        print("  O encerramento vai revisar sua configuracao e salvar o contexto da sessao.")

    elif choice == "codex":
        print()
        print("  Codex plugin detectado. Iniciando revisao...")
        print()
        try:
            subprocess.run(
                ["claude", "-p", "/codex:codex-rescue"],
                timeout=300,
            )
        except FileNotFoundError:
            print("  Erro: comando 'claude' nao encontrado no PATH.")
        except subprocess.TimeoutExpired:
            print("  Timeout na revisao Codex (300s). Verifique manualmente.")
        except KeyboardInterrupt:
            print("\n  Revisao Codex interrompida pelo usuario.")

    elif choice == "opus":
        print()
        print("  Abra o Claude e execute:")
        print()
        print('    "Reveja toda a configuracao da Semana 4 e liste o que precisa de atencao"')
        print("    (Use o modelo claude-opus-4-7 para analise mais profunda)")
        print()

    else:  # "none"
        print()
        print("  Nenhuma ferramenta de revisao detectada.")
        print("  Voce pode revisar manualmente os checkpoints em:")
        print("    ~/.operacao-ia/data/week4_checkpoint.json")
        print()
