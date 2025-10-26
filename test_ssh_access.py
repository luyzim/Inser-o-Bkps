import paramiko
from getpass import getpass
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_ssh_connection(hostname, username, password, test_command="echo 'Conexão SSH bem-sucedida!'"):
    """
    Attempts to connect to a remote server via SSH and execute a test command.

    Args:
        hostname (str): The hostname or IP address of the remote server.
        username (str): The username for SSH authentication.
        password (str): The password for SSH authentication.
        test_command (str): A simple command to execute to verify connection.
    """
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    logging.info(f"Tentando conectar a {hostname} como {username}...")

    try:
        client.connect(hostname=hostname, username=username, password=password, timeout=10)
        logging.info(f"Conexão SSH estabelecida com sucesso a {hostname}.")

        logging.info(f"Executando comando de teste: '{test_command}'")
        stdin, stdout, stderr = client.exec_command(test_command)
        exit_status = stdout.channel.recv_exit_status()

        if exit_status == 0:
            logging.info(f"Comando de teste executado com sucesso. Saída:\n{stdout.read().decode().strip()}")
            print("\n✅ Teste de acesso SSH CONCLUÍDO com SUCESSO!\n")
        else:
            logging.error(f"Comando de teste falhou com código {exit_status}. Erro:\n{stderr.read().decode().strip()}")
            print("\n❌ Teste de acesso SSH FALHOU na execução do comando!\n")

    except paramiko.AuthenticationException:
        logging.error("Falha na autenticação. Verifique usuário e senha.")
        print("\n❌ Teste de acesso SSH FALHOU: Credenciais inválidas!\n")
    except paramiko.SSHException as e:
        logging.error(f"Erro de SSH: {e}")
        print(f"\n❌ Teste de acesso SSH FALHOU: Erro de conexão SSH ({e})!\n")
    except Exception as e:
        logging.error(f"Ocorreu um erro inesperado: {e}")
        print(f"\n❌ Teste de acesso SSH FALHOU: Erro inesperado ({e})!\n")
    finally:
        if client:
            client.close()
            logging.info(f"Conexão com {hostname} encerrada.")

if __name__ == "__main__":
    print("\n--- Teste de Acesso SSH ---")
    HOSTNAME = input("Hostname/IP do servidor: ").strip()
    USERNAME = input("Usuário SSH: ").strip()
    PASSWORD = getpass("Senha SSH: ")

    if not all([HOSTNAME, USERNAME, PASSWORD]):
        print("Hostname, usuário e senha são obrigatórios.")
        sys.exit(1)

    test_ssh_connection(HOSTNAME, USERNAME, PASSWORD)
