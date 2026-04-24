#!/usr/bin/env python3
"""
Etapa 3 — Memoria Desktop <-> Terminal
Cria symlink para unificar a memoria do Claude em uma unica fonte.
ZX Control Semana 4
"""

import getpass
import shutil
import subprocess
import sys
from datetime import datetime
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
    print("\n[██░░░░░░░░] Etapa 3 de 8 — Memoria Desktop <-> Terminal\n")


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


def now_iso_epoch():
    """Retorna timestamp Unix atual como inteiro."""
    return int(datetime.now().timestamp())


# ---------------------------------------------------------------------------
# Linux — sem suporte
# ---------------------------------------------------------------------------

def handle_linux():
    print("  Claude Desktop nao disponivel no Linux. Etapa ignorada.")
    mark_checkpoint("step_3_memory_symlink", "skipped", "Linux nao suportado")
    print()
    print("  [OK] Etapa 3 ignorada (Linux).\n")


# ---------------------------------------------------------------------------
# Windows — instrucoes manuais
# ---------------------------------------------------------------------------

def _detect_paths():
    """
    Detecta os paths de memoria do Terminal e do Desktop usando glob.
    Retorna (terminal_mem, desktop_mem). desktop_mem pode nao existir ainda.
    """
    projects_base = Path.home() / ".claude" / "projects"

    # Terminal path: diretorio que NAO tem "Documents-Claude" no nome
    # e corresponde ao home do usuario (~/ = -Users-{username})
    username = getpass.getuser()
    terminal_mem = projects_base / f"-Users-{username}" / "memory"

    # Desktop path: detectar via glob para nao depender do username exato
    desktop_mem = None
    if projects_base.exists():
        candidates = [
            p for p in projects_base.iterdir()
            if p.is_dir() and "Documents-Claude" in p.name
        ]
        if candidates:
            # Pegar o mais recente (mtime) se houver mais de um
            candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            desktop_mem = candidates[0] / "memory"

    # Fallback: construir path padrao se nao encontrado via glob
    if desktop_mem is None:
        desktop_mem = projects_base / f"-Users-{username}-Documents-Claude" / "memory"

    return terminal_mem, desktop_mem


def handle_windows():
    terminal_mem, desktop_mem = _detect_paths()

    print("  Windows requer permissao de administrador para criar symlinks.")
    print()
    print("  Execute os comandos abaixo em um PowerShell como Administrador:")
    print()
    print(f'  # 1. Criar pasta destino (se nao existir)')
    print(f'  New-Item -ItemType Directory -Force -Path "{terminal_mem}"')
    print()
    print(f'  # 2. Remover pasta Desktop existente (faca backup antes!)')
    print(f'  Remove-Item -Recurse -Force "{desktop_mem}"')
    print()
    print(f'  # 3. Criar o symlink')
    print(f'  cmd /c mklink /D "{desktop_mem}" "{terminal_mem}"')
    print()

    mark_checkpoint(
        "step_3_memory_symlink",
        "manual",
        f"Windows: executar mklink /D como admin — desktop: {desktop_mem} -> {terminal_mem}",
    )
    print("  [OK] Etapa 3 — instrucoes manuais exibidas (Windows).\n")


# ---------------------------------------------------------------------------
# macOS — executa o symlink
# ---------------------------------------------------------------------------

def handle_macos():
    TERMINAL_MEM, DESKTOP_MEM = _detect_paths()

    print(f"  Terminal memory : {TERMINAL_MEM}")
    print(f"  Desktop memory  : {DESKTOP_MEM}")
    print()

    # 1. Garantir que TERMINAL_MEM existe
    if not TERMINAL_MEM.exists():
        print("  AVISO: pasta de memoria do Terminal nao encontrada.")
        print(f"  Criando: {TERMINAL_MEM}")
        TERMINAL_MEM.mkdir(parents=True, exist_ok=True)
    else:
        print(f"  Terminal memory encontrada.")

    # 2. Verificar se DESKTOP_MEM ja e symlink correto (idempotente)
    if DESKTOP_MEM.is_symlink():
        resolved = DESKTOP_MEM.resolve()
        if resolved == TERMINAL_MEM.resolve():
            print(f"  Symlink ja configurado corretamente. Nada a fazer.")
            mark_checkpoint(
                "step_3_memory_symlink",
                "done",
                f"symlink ja existia: {DESKTOP_MEM} -> {TERMINAL_MEM}",
            )
            print()
            print("  [OK] Etapa 3 concluida — symlink ja estava configurado!\n")
            return
        else:
            print(f"  Symlink existente aponta para local diferente: {resolved}")
            confirm = ask("  Reconfigurar para apontar para o Terminal memory? (s/n)", default="s").lower()
            if confirm not in ("s", "sim", "y", "yes"):
                print("  Mantendo configuracao atual.")
                mark_checkpoint("step_3_memory_symlink", "skipped", "usuario cancelou reconfiguracao")
                return
            DESKTOP_MEM.unlink()

    # 3. Se DESKTOP_MEM existe como arquivo regular — remover (nao e um diretorio valido)
    if DESKTOP_MEM.exists() and not DESKTOP_MEM.is_dir() and not DESKTOP_MEM.is_symlink():
        print(f"  AVISO: {DESKTOP_MEM} existe como arquivo regular. Removendo...")
        DESKTOP_MEM.unlink()

    # 3. Se DESKTOP_MEM existe como diretorio real — fazer backup + merge
    if DESKTOP_MEM.exists() and DESKTOP_MEM.is_dir():
        print()
        print(f"  Pasta Desktop memory existe como diretorio real.")
        print(f"  Criando backup antes de continuar...")

        BACKUP = Path.home() / ".zxlab-backup" / f"desktop-memory-{now_iso_epoch()}"
        BACKUP.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(str(DESKTOP_MEM), str(BACKUP))
        print(f"  Backup criado em: {BACKUP}")

        # Copiar arquivos exclusivos do DESKTOP_MEM para TERMINAL_MEM
        desktop_files = set(p.name for p in DESKTOP_MEM.iterdir() if p.is_file())
        terminal_files = set(p.name for p in TERMINAL_MEM.iterdir() if TERMINAL_MEM.exists() and p.is_file())
        exclusive = desktop_files - terminal_files

        if exclusive:
            print(f"  Copiando {len(exclusive)} arquivo(s) exclusivo(s) para Terminal memory...")
            for fname in exclusive:
                src = DESKTOP_MEM / fname
                dst = TERMINAL_MEM / fname
                shutil.copy2(str(src), str(dst))
                print(f"    copiado: {fname}")
        else:
            print("  Nenhum arquivo exclusivo encontrado — sem necessidade de merge.")

        # Remover DESKTOP_MEM
        shutil.rmtree(str(DESKTOP_MEM))
        print(f"  Pasta Desktop memory removida.")

    # 4. Criar symlink
    DESKTOP_MEM.parent.mkdir(parents=True, exist_ok=True)
    DESKTOP_MEM.symlink_to(TERMINAL_MEM)
    print()

    # 5. Verificar symlink
    if DESKTOP_MEM.is_symlink() and DESKTOP_MEM.resolve() == TERMINAL_MEM.resolve():
        print(f"  Symlink criado e verificado com sucesso!")
        print(f"    {DESKTOP_MEM}")
        print(f"    -> {TERMINAL_MEM}")
    else:
        print("  ERRO: symlink nao foi criado corretamente. Verifique manualmente.")
        sys.exit(1)

    mark_checkpoint(
        "step_3_memory_symlink",
        "done",
        f"symlink: {DESKTOP_MEM} -> {TERMINAL_MEM}",
    )

    print()
    print("  [OK] Etapa 3 concluida — Memoria Desktop e Terminal unificadas!\n")


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

    print("  Etapa 3 — Memoria Desktop <-> Terminal")
    print()
    print("  Claude Desktop (~/Documents/Claude) e Claude Terminal (~/) usam")
    print("  caminhos de memoria diferentes. Vamos criar um symlink para que")
    print("  ambos compartilhem a mesma fonte de memoria.")
    print()

    ensure_structure()

    if PLATFORM == "Linux":
        handle_linux()
    elif PLATFORM == "Windows":
        handle_windows()
    else:
        handle_macos()

    print("  Proximo passo: Etapa 4 — Skills e MCPs em Sync")
    print("  Execute: python3 setup/setup_sync_skills_mcp.py")
    print()


if __name__ == "__main__":
    main()
