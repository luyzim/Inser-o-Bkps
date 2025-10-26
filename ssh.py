
import os
from dotenv import load_dotenv
import paramiko
from getpass import getpass
import re

from main import generate_commands, get_template_paths, get_interactive_placeholder_data

load_dotenv()

def conectar_ssh(host: str = None, usuario: str = None, senha: str = None):
 
    # Prioriza argumentos passados; se ausentes, usa variáveis do ambiente
    host = host or os.getenv("SSH_HOST")
    usuario = usuario or os.getenv("SSH_USER")
    senha = senha or os.getenv("SSH_PASS")

    if not all([host, usuario, senha]):
        raise ValueError("Host, usuário e senha devem ser fornecidos ou definidos no .env")

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(host, username=usuario, password=senha)
        sftp = client.open_sftp()
        return client, sftp
    except paramiko.BadHostKeyException:
        raise Exception("Chave do servidor não é confiável ou não pôde ser verificada.")
    except paramiko.AuthenticationException:
        raise Exception("Falha de autenticação. Verifique usuário e senha.")
    except paramiko.SSHException as ssh_err:
        raise Exception(f"Erro na conexão SSH: {ssh_err}")
    except Exception as err:
        raise Exception(f"Erro ao conectar no host {host}: {err}")

def execute_sudo_command(ssh_client, command, sudo_password):
    """
    Executes a command with sudo privileges on the remote server.
    The sudo password is sent via stdin.
    """
    try:
        chan = ssh_client.get_transport().open_session()
        chan.exec_command(f"sudo -S {command}")

        # Send sudo password
        chan.sendall(sudo_password + "\n")

        stdout = chan.makefile("rb", -1).read().decode().strip()
        stderr = chan.makefile_stderr("rb", -1).read().decode().strip()
        exit_status = chan.recv_exit_status()

        if exit_status == 0:
            print(f"Comando SUDO '{command}' executado com sucesso.")
            print(f"Saída:\n{stdout}")
        else:
            print(f"Comando SUDO '{command}' falhou com código {exit_status}.")
            print(f"Erro:\n{stderr}")
        return stdout, stderr, exit_status
    except Exception as e:
        print(f"Erro ao executar comando SUDO: {e}")
        return "", str(e), 1

def ler_arquivo_remoto(sftp, caminho_remoto: str) -> str:
    """Lê o conteúdo de um arquivo de texto no servidor remoto via SFTP."""
    try:
        # Abre o arquivo remoto em modo de leitura
        with sftp.open(caminho_remoto, 'r') as arquivo_remoto:
            conteudo = arquivo_remoto.read()
            # Garante que o conteúdo seja string (decodifica bytes para UTF-8)
            if isinstance(conteudo, bytes):
                conteudo = conteudo.decode('utf-8')
            return conteudo
    except FileNotFoundError:
        raise Exception(f"Arquivo de configuração não encontrado: {caminho_remoto}")
    except Exception as err:
        # Qualquer outro erro ao ler o arquivo (permissão negada, etc.)
        raise Exception(f"Erro ao ler o arquivo remoto: {err}")

def inserir_entrada_em_grupo(conteudo: str, nome_grupo: str, nova_entrada: str) -> str:
    """Insere a nova_entrada dentro da seção/grupo especificado pelo nome_grupo no conteúdo fornecido."""
    linhas = conteudo.splitlines()
    inicio_grupo = None
    # Localiza a linha de início da seção (por exemplo, "[BKP]")
    for i, linha in enumerate(linhas):
        # Verifica se a linha define uma seção (formato [NOME]) e se é a seção desejada
        if linha.strip().startswith("[") and linha.strip().endswith("]"):
            secao = linha.strip()[1:-1].strip()  # extrai o nome da seção entre colchetes
            if secao.lower() == nome_grupo.lower():
                inicio_grupo = i
                break
    if inicio_grupo is None:
        # Se o grupo não for encontrado, levanta exceção
        raise Exception(f"Grupo '{nome_grupo}' não encontrado no arquivo de configuração.")
    # Determina o fim da seção (ou seja, antes da próxima seção ou fim do arquivo)
    fim_grupo = len(linhas)
    for j in range(inicio_grupo + 1, len(linhas)):
        if linhas[j].strip().startswith("[") and linhas[j].strip().endswith("]"):
            fim_grupo = j
            break
    # Extrai apenas as linhas pertencentes ao grupo BKP para verificação
    linhas_grupo = linhas[inicio_grupo+1 : fim_grupo]
    # Evita inserir duplicatas: verifica se a nova entrada já existe no grupo
    if any(linha.strip() == nova_entrada.strip() for linha in linhas_grupo):
        raise Exception(f"A entrada fornecida já existe no grupo {nome_grupo}.")
    # Insere a nova entrada na posição correta (antes do fim do grupo)
    linhas.insert(fim_grupo, nova_entrada)
    # Recompõe o conteúdo como uma única string com quebras de linha
    conteudo_modificado = "\n".join(linhas) + "\n"
    return conteudo_modificado

def salvar_arquivo_remoto(sftp, caminho_remoto: str, conteudo: str):
    """Escreve o conteúdo (texto) no arquivo remoto especificado, via SFTP."""
    try:
        # Abre o arquivo remoto em modo de escrita (isso trunca/ sobrescreve o arquivo existente)
        with sftp.open(caminho_remoto, 'w') as arquivo_remoto:
            arquivo_remoto.write(conteudo)
            arquivo_remoto.flush()  # Garante que os dados sejam enviados imediatamente
        # Permissões de arquivo e propriedade permanecem as mesmas do arquivo original por padrão
    except Exception as err:
        # Possíveis erros: falta de permissão de escrita, espaço insuficiente, etc.
        raise Exception(f"Erro ao salvar o arquivo remoto: {err}")

# Exemplo de uso do script:
if __name__ == "__main__":
    print("\n--- Configurações de Conexão SSH ---")
    host = input("Host do servidor: ").strip()
    usuario = input("Usuário SSH: ").strip()
    senha = getpass("Senha SSH: ")

    ssh_client = None
    sftp_client = None
    try:
        ssh_client, sftp_client = conectar_ssh(host, usuario, senha)
        print(f"Conectado com sucesso a {host}.\n")

        while True:
            print("\n--- Escolha uma opção ---")
            print("1) Gerar e inserir entradas em arquivo de configuração (via main.py)")
            print("2) Executar comando com SUDO")
            print("3) Inserir linha em arquivo remoto (programaticamente)")
            print("4) Sair")
            choice = input("Sua escolha: ").strip()

            if choice == '1':
                caminho_config = input("Caminho do arquivo de configuração remoto (ex: /etc/config/bkps.txt): ").strip()
                nome_grupo = input("Nome do grupo/seção no arquivo de configuração (ex: BKP): ").strip() or "BKP"

                print("\n--- Geração de Comandos/Entradas ---")
                templates = get_template_paths()
                print("Templates disponíveis:")
                for i, p in enumerate(templates, 1):
                    print(f"{i}) {p.name}")

                try:
                    main_template_idx = int(input("Nº do template principal: ").strip()) - 1
                    if not (0 <= main_template_idx < len(templates)):
                        raise ValueError("Índice inválido.")
                except ValueError:
                    print("Escolha de template principal inválida. Retornando ao menu.")
                    continue

                mass_gen_resp = input("Deseja gerar em massa (com template agregado)? [S/N]: ").strip().lower()
                aggregated_template_idx = None
                if mass_gen_resp == 's':
                    print("Templates agregados disponíveis (ENTER para pular):")
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
                            else:
                                print("Escolha de template agregado inválida. Ignorando.")
                        except ValueError:
                            print("Entrada inválida para template agregado. Ignorando.")

                templates_for_data = [templates[main_template_idx]]
                if aggregated_template_idx is not None:
                    templates_for_data.append(templates[aggregated_template_idx])

                placeholder_data = get_interactive_placeholder_data(templates_for_data)

                generated_entries = generate_commands(
                    main_template_idx=main_template_idx,
                    mass_gen_response=mass_gen_resp,
                    aggregated_template_idx=aggregated_template_idx,
                    placeholder_data=placeholder_data
                )

                if not generated_entries:
                    print("Nenhuma entrada gerada. Retornando ao menu.")
                    continue

                nova_entrada = "\n".join(generated_entries)

                print("\n--- Entradas Geradas para Inserção ---")
                print(nova_entrada)

                confirm = input("\nConfirmar inserção destas entradas no servidor? [S/N]: ").strip().lower()
                if confirm == 's':
                    conteudo_original = ler_arquivo_remoto(sftp_client, caminho_config)
                    conteudo_modificado = inserir_entrada_em_grupo(conteudo_original, nome_grupo, nova_entrada)
                    salvar_arquivo_remoto(sftp_client, caminho_config, conteudo_modificado)
                    print(f"Novas entradas inseridas no grupo '{nome_grupo}' e arquivo salvo com sucesso.")
                else:
                    print("Inserção cancelada.")

            elif choice == '2':
                command_to_execute = input("Comando SUDO a executar: ").strip()
                if command_to_execute:
                    confirm_sudo = input(f"Confirmar execução de '{command_to_execute}' com sudo? [S/N]: ").strip().lower()
                    if confirm_sudo == 's':
                        execute_sudo_command(ssh_client, command_to_execute, senha)
                    else:
                        print("Execução de comando SUDO cancelada.")
                else:
                    print("Comando vazio. Retornando ao menu.")

            elif choice == '3':
                remote_file = input("Caminho do arquivo remoto para modificar: ").strip()
                line_to_insert_str = input("Linha a inserir: ").strip()
                insert_after_pattern = input("Inserir após padrão (regex, ENTER para pular): ").strip()
                insert_after_num_str = input("Inserir após linha número (1-based, ENTER para pular): ").strip() # Changed to 1-based for sed

                if not remote_file or not line_to_insert_str:
                    print("Caminho do arquivo e linha a inserir são obrigatórios. Retornando ao menu.")
                    continue

                sed_command = ""
                # Escape single quotes in the line to insert for sed
                escaped_line_to_insert = line_to_insert_str.replace("'", "'\\''")

                if insert_after_pattern:
                    # sed -i '/PATTERN/a\NEW_LINE' file
                    sed_command = f"sed -i '/{(insert_after_pattern)}/a\\{escaped_line_to_insert}' '{remote_file}'"
                elif insert_after_num_str:
                    try:
                        after_line_num = int(insert_after_num_str)
                        # sed -i 'LINE_NUMBERa\NEW_LINE' file
                        sed_command = f"sed -i '{after_line_num}a\\{escaped_line_to_insert}' '{remote_file}'"
                    except ValueError:
                        print("Número de linha inválido. Retornando ao menu.")
                        continue
                else:
                    # Default to appending if no specific location is given
                    # sed -i '$a\NEW_LINE' file
                    sed_command = f"sed -i '$a\\{escaped_line_to_insert}' '{remote_file}'"
                    print("Nenhum padrão ou número de linha fornecido. Anexando ao final do arquivo.")

                if sed_command:
                    confirm_insert = input(f"Confirmar execução do comando SED: '{sed_command}'? [S/N]: ").strip().lower()
                    if confirm_insert == 's':
                        execute_sudo_command(ssh_client, sed_command, senha)
                        print("Operação de inserção de linha concluída (via SED).")
                    else:
                        print("Inserção de linha cancelada.")
                else:
                    print("Não foi possível construir o comando SED. Retornando ao menu.")

            elif choice == '4':
                print("Saindo...")
                break
            else:
                print("Opção inválida. Tente novamente.")

    except Exception as e:
        print(f"Erro geral: {e}")
    finally:
        if sftp_client:
            sftp_client.close()
        if ssh_client:
            ssh_client.close()
