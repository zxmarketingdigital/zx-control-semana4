#!/usr/bin/env python3
"""
Etapa 5 — Graphify Segundo Cerebro
Configura Graphify para mapear projetos como knowledge graphs.
ZX Control Semana 4
"""

import getpass
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib import (
    GRAPHS_DIR,
    ensure_structure,
    mark_checkpoint,
    now_iso,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def progress_bar():
    print("\n[████░░░░░░] Etapa 5 de 10 — Graphify: Segundo Cerebro\n")


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


def slugify(name):
    """Converte nome de projeto em slug seguro."""
    import re
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9\-_]", "-", name)
    name = re.sub(r"-{2,}", "-", name)
    return name.strip("-") or "projeto"


# ---------------------------------------------------------------------------
# Verificar skill /graphify
# ---------------------------------------------------------------------------

def check_graphify_skill():
    """Verifica se skill /graphify esta instalada."""
    skill_path = Path.home() / ".claude" / "skills" / "graphify" / "SKILL.md"
    if skill_path.exists():
        print(f"  Skill /graphify encontrada: {skill_path}")
        return True
    else:
        print(f"  AVISO: Skill /graphify nao encontrada em {skill_path}")
        print(f"  Instale via ZX LAB HUB antes de usar o /graphify.")
        print(f"  Continuando setup sem a skill...")
        return False


# ---------------------------------------------------------------------------
# Listar projetos disponíveis
# ---------------------------------------------------------------------------

def list_projects():
    """Lista projetos em ~/projetos/ que possuem CLAUDE.md."""
    projetos_dir = Path.home() / "projetos"
    if not projetos_dir.exists():
        return []

    projects = []
    for item in sorted(projetos_dir.iterdir()):
        if item.is_dir() and (item / "CLAUDE.md").exists():
            projects.append({"slug": item.name, "path": str(item)})

    return projects


def select_project(projects):
    """
    Permite ao aluno escolher um projeto para mapear.
    Default: ~/.operacao-ia/
    """
    default_path = Path.home() / ".operacao-ia"
    default_slug = "operacao-ia"

    if not projects:
        print("  Nenhum projeto com CLAUDE.md encontrado em ~/projetos/")
        print(f"  Usando default: {default_path}")
        return default_slug, str(default_path)

    print()
    print("  Projetos disponíveis em ~/projetos/ (com CLAUDE.md):")
    print()
    for i, proj in enumerate(projects[:20], 1):
        print(f"    {i:2}. {proj['slug']}")
    if len(projects) > 20:
        print(f"    ... e mais {len(projects) - 20} projetos.")
    print()
    print(f"    0. operacao-ia (default — ~/.operacao-ia/)")
    print()

    choice_raw = ask(
        f"  Numero do projeto para mapear (0-{min(len(projects), 20)}, Enter para default)",
        default="0",
    )

    try:
        choice = int(choice_raw)
        if choice == 0:
            return default_slug, str(default_path)
        if 1 <= choice <= len(projects):
            proj = projects[choice - 1]
            return proj["slug"], proj["path"]
    except (ValueError, TypeError):
        pass

    # Nao foi numero valido — tenta como slug direto
    slug_input = choice_raw.strip()
    if slug_input:
        # Verifica se existe em ~/projetos/
        candidate = Path.home() / "projetos" / slug_input
        if candidate.exists():
            return slug_input, str(candidate)
        # Usa como slug customizado com operacao-ia path
        return slugify(slug_input), str(default_path / slug_input)

    return default_slug, str(default_path)


# ---------------------------------------------------------------------------
# Criar estrutura Graphify
# ---------------------------------------------------------------------------

def create_graph_structure(slug, project_path):
    """Cria pasta e graph.json inicial para o projeto."""
    graph_dir = GRAPHS_DIR / slug
    graph_dir.mkdir(parents=True, exist_ok=True)

    graph_file = graph_dir / "graph.json"

    if graph_file.exists():
        print(f"  graph.json ja existe em {graph_dir} — mantendo.")
    else:
        graph_data = {
            "project": slug,
            "path": project_path,
            "created_at": now_iso(),
            "nodes": [],
            "edges": [],
            "status": "pending_graphify",
        }
        graph_file.write_text(
            json.dumps(graph_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  graph.json criado em {graph_dir}")

    return graph_dir, graph_file


# ---------------------------------------------------------------------------
# Configuracao global Graphify
# ---------------------------------------------------------------------------

def update_graphify_config(slug, project_path):
    """Cria ou atualiza ~/.operacao-ia/config/graphify_config.json."""
    config_dir = Path.home() / ".operacao-ia" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "graphify_config.json"

    if config_path.exists():
        try:
            existing = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            existing = {"graphs_dir": str(GRAPHS_DIR), "projects": [], "last_updated": ""}
    else:
        existing = {"graphs_dir": str(GRAPHS_DIR), "projects": [], "last_updated": ""}

    # Verificar se projeto ja esta na lista
    projects = existing.get("projects", [])
    slugs = [p.get("slug") for p in projects]
    if slug not in slugs:
        projects.append({
            "slug": slug,
            "path": project_path,
            "mapped": False,
        })
        existing["projects"] = projects

    existing["graphs_dir"] = str(GRAPHS_DIR)
    existing["last_updated"] = now_iso()

    config_path.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  graphify_config.json atualizado: {config_path}")


# ---------------------------------------------------------------------------
# Executar /graphify agora (opcional)
# ---------------------------------------------------------------------------

def run_graphify_now(project_path, skill_available):
    """Oferece executar /graphify imediatamente no projeto."""
    if not skill_available:
        return

    print()
    answer = ask("  Quer executar /graphify agora neste projeto? (s/n)", default="n").lower()
    if answer not in ("s", "sim", "y", "yes"):
        print("  Pulando execucao imediata. Voce pode executar depois com: /graphify")
        return

    print()
    print(f"  Executando /graphify em {project_path}...")
    print(f"  (timeout: 120s)")
    print()

    try:
        result = subprocess.run(
            ["claude", "-p", "/graphify"],
            cwd=str(project_path),
            timeout=120,
        )
        if result.returncode == 0:
            print()
            print("  /graphify concluido!")
        else:
            print()
            print(f"  AVISO: /graphify encerrou com codigo {result.returncode}")
    except subprocess.TimeoutExpired:
        print()
        print("  AVISO: /graphify excedeu timeout de 120s. Execute manualmente.")
    except FileNotFoundError:
        print()
        print("  AVISO: comando 'claude' nao encontrado no PATH.")
        print("  Execute manualmente no projeto: /graphify")


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

    print("  Etapa 5 — Graphify: Segundo Cerebro")
    print()
    print("  O Graphify transforma codigo e documentacao em knowledge graphs,")
    print("  criando um mapa visual de todo o seu projeto para o Claude.")
    print()

    ensure_structure()

    # 1. Verificar skill
    print("--- Verificando Skill /graphify ---")
    print()
    skill_available = check_graphify_skill()
    print()

    # 2. Garantir GRAPHS_DIR
    print("--- Diretorio de Grafos ---")
    print()
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  Diretorio de grafos: {GRAPHS_DIR}")
    print()

    # 3. Listar projetos
    print("--- Selecionar Projeto ---")
    projects = list_projects()
    slug, project_path = select_project(projects)

    print()
    print(f"  Projeto selecionado : {slug}")
    print(f"  Caminho             : {project_path}")
    print()

    # 4. Criar estrutura do grafo
    print("--- Criando Estrutura do Grafo ---")
    print()
    graph_dir, graph_file = create_graph_structure(slug, project_path)

    # 5. Atualizar config global
    update_graphify_config(slug, project_path)

    # 6. Instrucoes para o aluno
    print()
    print("--- Como usar o Graphify ---")
    print()
    print(f"  1. Abra o Claude no projeto:")
    print(f"       cd {project_path} && claude")
    print()
    print(f"  2. Execute a skill:")
    print(f"       /graphify")
    print()
    print(f"  3. O Claude vai mapear o projeto e salvar o grafo em:")
    print(f"       {graph_dir}")
    print()

    # 7. Oferecer executar agora
    run_graphify_now(project_path, skill_available)

    # Checkpoint
    mark_checkpoint(
        "step_5_graphify",
        "done",
        f"graphs dir: {GRAPHS_DIR} | projeto: {slug} | skill: {'ok' if skill_available else 'nao instalada'}",
    )

    print()
    print("  [OK] Etapa 5 concluida — Graphify configurado!\n")
    print("  Proximo passo: Etapa 6 — continue com o setup.")
    print("  Execute: python3 setup/setup_step6.py")
    print()


if __name__ == "__main__":
    main()
