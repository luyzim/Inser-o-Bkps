from pathlib import Path
import sys
import re

BASE = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE / "data"

class SafeDict(dict):
    def __missing__(self, k):
        return "{" + k + "}"

def listar_templates():
    print("--- Templates Disponíveis ---")
    if not TEMPLATES_DIR.exists():
        raise SystemExit(f"Diretório não existe: {TEMPLATES_DIR}")
    arquivos = sorted(TEMPLATES_DIR.glob("*.txt"))
    if not arquivos:
        raise SystemExit(f"Nenhum template .txt encontrado em {TEMPLATES_DIR}/")
    for i, p in enumerate(arquivos, 1):
        print(f"{i}) {p.name}")
    return arquivos

def render_template(path: Path, data: dict) -> str:
    txt = path.read_text(encoding="utf-8")
    return txt.format_map(SafeDict(data))

# --- NOVO: utilitário simples para extrair placeholders de 1 arquivo
def _placeholders_de(path: Path) -> list[str]:
    txt = path.read_text(encoding="utf-8")
    return sorted(set(re.findall(r"{([^}]+)}", txt)))

# --- NOVO: pergunta apenas uma vez para o conjunto (união) de placeholders
def coletar_dados_uma_vez(arquivos: list[Path]) -> dict:
    todos = set()
    for arq in arquivos:
        todos.update(_placeholders_de(arq))
    placeholders = sorted(todos)

    print("\n--- Preenchimento de Dados (aplicado a todos) ---")
    dados = {}
    for ph in placeholders:
        val = input(f"{ph}: ")
        dados[ph] = val.replace(" ", "").upper()
    return dados

# --- NOVO: escolha interativa do segundo template (sem mapeamentos)
def escolher_pareado(templates: list[Path], idx_principal: int) -> Path | None:
    
    print("\nDeseja gerar em massa? [S/N]: ", end="")
    resp = input().strip().lower()
    if resp not in {"s", "sim"}:
        return None

    print("\n--- Escolha o template agregado (ENTER para pular) ---")
    for i, p in enumerate(templates, 1):
        if i - 1 == idx_principal:
            continue
        print(f"{i}) {p.name}")
    escolha = input("Nº do template agregado: ").strip()
    if not escolha:
        return None
    try:
        idx = int(escolha) - 1
        if idx == idx_principal or not (0 <= idx < len(templates)):
            print("Escolha inválida. Ignorando agregado.")
            return None
        return templates[idx]
    except ValueError:
        print("Entrada inválida. Ignorando agregado.")
        return None

def main():
    # 1) Escolha do template principal
    templates = listar_templates()
    try:
        idx = int(input("Nº do template: ").strip()) - 1
        tpl_principal = templates[idx]
    except (ValueError, IndexError):
        print("Escolha inválida.")
        sys.exit(1)

    # 2) (Opcional) Escolher um segundo template sem mapeamento
    try:
        if idx == 1 or idx == 0:  # 1ª e 2ª opções (1-based)
            tpl_sec = escolher_pareado(templates, idx)
        else:
            tpl_sec = None
    except Exception as e:
        print(f"Erro ao escolher template agregado: {e}")
        tpl_sec = None

    # 3) Perguntar UMA vez (união dos placeholders dos selecionados)
    alvos = [tpl_principal] + ([tpl_sec] if tpl_sec else [])
    dados = coletar_dados_uma_vez(alvos)

    # 4) Renderizar principal
    saida_principal = render_template(tpl_principal, dados)

    print(saida_principal)

    # 5) Renderizar secundário (se houver)
    if tpl_sec:
        saida_sec = render_template(tpl_sec, dados)

        print(saida_sec)


if __name__ == "__main__":
    main()
