from pathlib import Path
import sys
import re

BASE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
TEMPLATES_DIR = BASE / "data"

class SafeDict(dict):
    def __missing__(self, k):
        return "{" + k + "}"

def listar_templates():
    print("--- Templates Disponíveis ---")
    arquivos = sorted(TEMPLATES_DIR.glob("*.txt"))
    if not arquivos:
        raise SystemExit(f"Nenhum template .txt encontrado em {TEMPLATES_DIR}/")
    for i, p in enumerate(arquivos, 1):
        print(f"{i}) {p.name}")
    return arquivos

def escolher_template(templates):
    try:
        escolha = int(input("Nº do template: ").strip()) - 1
        if not (0 <= escolha < len(templates)):
            raise IndexError
        return templates[escolha], escolha
    except (ValueError, IndexError):
        print("Escolha inválida."); sys.exit(1)

def templates_ccs():
    print("\n--- Instruções Especiais ---")
    # Coloque instruções específicas aqui

def extrair_placeholders(txt: str):
    return sorted(set(re.findall(r"{([^}]+)}", txt)))

def preencher_dados(tpl: Path) -> dict:
    print("\n--- Preenchimento de Dados ---")
    template_content = tpl.read_text(encoding="utf-8")
    placeholders = extrair_placeholders(template_content)

    dados = {}
    for placeholder in placeholders:
        valor = input(f"{placeholder}: ")
        dados[placeholder] = valor.replace(" ", "").upper()  # seu padrão atual
    return dados

def render_template(path: Path, data: dict) -> str:
    txt = path.read_text(encoding="utf-8")
    return txt.format_map(SafeDict(data))

def main():
    templates = listar_templates()
    tpl, escolha = escolher_template(templates)

    if escolha in {0, 1}:  # 1ª e 2ª opções (1-based)
        templates_ccs()

    dados = preencher_dados(tpl)
    saida = render_template(tpl, dados)

    print("\n--- Resultado Final ---")
    print(saida)

if __name__ == "__main__":
    main()
