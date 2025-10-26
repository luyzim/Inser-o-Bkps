from pathlib import Path
import sys
import re

BASE = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE / "data"

class SafeDict(dict):
    def __missing__(self, k):
        return "{" + k + "}"

def get_template_paths():
    """Returns a sorted list of available template paths."""
    if not TEMPLATES_DIR.exists():
        raise SystemExit(f"Diretório não existe: {TEMPLATES_DIR}")
    arquivos = sorted(TEMPLATES_DIR.glob("*.txt"))
    if not arquivos:
        raise SystemExit(f"Nenhum template .txt encontrado em {TEMPLATES_DIR}/")
    return arquivos

def render_template(path: Path, data: dict) -> str:
    txt = path.read_text(encoding="utf-8")
    return txt.format_map(SafeDict(data))

def get_placeholder_names(template_paths: list[Path]) -> list[str]:
    """Extracts and returns a sorted list of unique placeholder names from given templates."""
    all_placeholders = set()
    for arq in template_paths:
        txt = arq.read_text(encoding="utf-8")
        all_placeholders.update(re.findall(r"{([^}]+)}", txt))
    return sorted(all_placeholders)

def get_interactive_placeholder_data(template_paths: list[Path]) -> dict:
    """Interactively collects data for all unique placeholders across given templates."""
    placeholders = get_placeholder_names(template_paths)
    print("--- Preenchimento de Dados (aplicado a todos) ---")
    dados = {}
    for ph in placeholders:
        val = input(f"{ph}: ")
        dados[ph] = val.replace(" ", "").upper()
    return dados

def choose_aggregated_template_interactively(templates: list[Path], principal_idx: int) -> Path | None:
    """Interactively allows the user to choose an aggregated template."""
    print("Deseja gerar em massa? [S/N]: ", end="")
    resp = input().strip().lower()
    if resp not in {"s", "sim"}:
        return None

    print("--- Escolha o template agregado (ENTER para pular) ---")
    for i, p in enumerate(templates, 1):
        if i - 1 == principal_idx:
            continue
        print(f"{i}) {p.name}")
    escolha = input("Nº do template agregado: ").strip()
    if not escolha:
        return None
    try:
        idx = int(escolha) - 1
        if idx == principal_idx or not (0 <= idx < len(templates)):
            print("Escolha inválida. Ignorando agregado.")
            return None
        return templates[idx]
    except ValueError:
        print("Entrada inválida. Ignorando agregado.")
        return None

def generate_commands(
    main_template_idx: int,
    mass_gen_response: str, # 's' or 'n'
    aggregated_template_idx: int | None, # 0-based index or None
    placeholder_data: dict
) -> list[str]:
    """
    Generates commands from templates based on provided choices and data.
    Returns a list of command strings.
    """
    templates = get_template_paths()

    try:
        tpl_principal = templates[main_template_idx]
    except IndexError:
        raise ValueError("Índice de template principal inválido.")

    tpl_sec = None
    if mass_gen_response.lower() == 's' and aggregated_template_idx is not None:
        try:
            tpl_sec = templates[aggregated_template_idx]
            if aggregated_template_idx == main_template_idx:
                tpl_sec = None # Should not be the same
        except IndexError:
            pass # Invalid index, just ignore aggregated template

    rendered_outputs = []
    saida_principal = render_template(tpl_principal, placeholder_data)
    rendered_outputs.append(saida_principal)

    if tpl_sec:
        saida_sec = render_template(tpl_sec, placeholder_data)
        rendered_outputs.append(saida_sec)

    # Split each rendered output by newline and filter empty lines
    all_commands = []
    for output_block in rendered_outputs:
        all_commands.extend([cmd.strip() for cmd in output_block.splitlines() if cmd.strip()])
    return all_commands

def _interactive_main():
    """Interactive entry point for main.py."""
    templates = get_template_paths()
    print("--- Templates Disponíveis ---")
    for i, p in enumerate(templates, 1):
        print(f"{i}) {p.name}")

    try:
        main_template_idx = int(input("Nº do template: ").strip()) - 1
        tpl_principal = templates[main_template_idx]
    except (ValueError, IndexError):
        print("Escolha inválida.")
        sys.exit(1)

    mass_gen_resp = input("Deseja gerar em massa? [S/N]: ").strip().lower()
    aggregated_template_idx = None
    if mass_gen_resp == 's':
        print("--- Escolha o template agregado (ENTER para pular) ---")
        for i, p in enumerate(templates, 1):
            if i - 1 == main_template_idx:
                continue
            print(f"{i}) {p.name}")
        escolha_agg = input("Nº do template agregado: ").strip()
        if escolha_agg:
            try:
                agg_idx = int(escolha_agg) - 1
                if agg_idx != main_template_idx and (0 <= agg_idx < len(templates)):
                    aggregated_template_idx = agg_idx
            except ValueError:
                pass # Invalid input, ignore aggregated

    # Collect data for all relevant placeholders
    alvos = [tpl_principal]
    if aggregated_template_idx is not None:
        alvos.append(templates[aggregated_template_idx])
    placeholder_data = get_interactive_placeholder_data(alvos)

    # Generate and print commands
    commands = generate_commands(
        main_template_idx,
        mass_gen_resp,
        aggregated_template_idx,
        placeholder_data
    )
    for cmd in commands:
        print(cmd)


if __name__ == "__main__":
    _interactive_main()
