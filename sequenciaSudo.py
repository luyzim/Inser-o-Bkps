import paramiko
import time
from typing import List
from pathlib import Path
import os
from dotenv import load_dotenv








def run_commands_with_sudo(ssh_client: paramiko.SSHClient,
                           senha_sudo: str,
                           comandos: List[str],
                           stop_on_error: bool = True,
                           timeout: int = 30) -> List[dict]:
    """
    Executa uma sequência de comandos usando sudo via SSH (Paramiko).
    Para cada comando:
      - usa `exec_command(..., get_pty=True)` para garantir um tty,
      - escreve a senha no stdin (sudo -S),
      - aguarda a saída e coleta stdout/stderr/rc.

    Retorna lista de dicionários com chaves: command, stdout, stderr, rc, ok (bool).

    Parâmetros:
      ssh_client: cliente Paramiko já conectado.
      senha_sudo: senha do usuário para sudo.
      comandos: lista de strings (comandos a executar).
      stop_on_error: se True, lança exceção no primeiro comando com rc != 0.
      timeout: tempo máximo (segundos) para leitura de cada comando.
    """
    resultados = []

    for cmd in comandos:
        try:
            # Prefixa com sudo -S (lê a senha do stdin) e -p '' para não imprimir prompt
            remote_cmd = f"sudo -S -p '' {cmd}"
            stdin, stdout, stderr = ssh_client.exec_command(remote_cmd, get_pty=True)

            # Envia a senha seguida de newline e força o flush
            stdin.write(senha_sudo + "\n")
            stdin.flush()

            # Ler a saída (com timeout simples)
            end_time = time.time() + timeout
            stdout_chunks = []
            stderr_chunks = []

            # Enquanto houver dados ou não ter estourado o timeout, leia em blocos
            while not stdout.channel.exit_status_ready():
                # Ler qualquer dado disponível sem bloquear indefinidamente
                if stdout.channel.recv_ready():
                    chunk = stdout.channel.recv(4096)
                    try:
                        stdout_chunks.append(chunk.decode("utf-8", errors="replace"))
                    except Exception:
                        stdout_chunks.append(chunk.decode("latin-1", errors="replace"))
                if stderr.channel.recv_stderr_ready():
                    echunk = stderr.channel.recv_stderr(4096)
                    try:
                        stderr_chunks.append(echunk.decode("utf-8", errors="replace"))
                    except Exception:
                        stderr_chunks.append(echunk.decode("latin-1", errors="replace"))

                if time.time() > end_time:
                    # timeout — tenta quebrar o loop
                    break
                time.sleep(0.1)

            # Pode haver dados finais após exit_status_ready()
            # Leia o que sobrou
            while stdout.channel.recv_ready():
                chunk = stdout.channel.recv(4096)
                try:
                    stdout_chunks.append(chunk.decode("utf-8", errors="replace"))
                except Exception:
                    stdout_chunks.append(chunk.decode("latin-1", errors="replace"))

            while stderr.channel.recv_stderr_ready():
                echunk = stderr.channel.recv_stderr(4096)
                try:
                    stderr_chunks.append(echunk.decode("utf-8", errors="replace"))
                except Exception:
                    stderr_chunks.append(echunk.decode("latin-1", errors="replace"))

            # Código de saída do comando
            try:
                rc = stdout.channel.recv_exit_status()
            except Exception:
                # Se por algum motivo não for possível obter, assume -1
                rc = -1

            saida_texto = "".join(stdout_chunks).strip()
            erro_texto = "".join(stderr_chunks).strip()

            resultado = {
                "command": cmd,
                "stdout": saida_texto,
                "stderr": erro_texto,
                "rc": rc,
                "ok": (rc == 0)
            }
            resultados.append(resultado)

            if rc != 0 and stop_on_error:
                raise RuntimeError(f"Comando falhou (rc={rc}): {cmd}\nstderr: {erro_texto}")

        except paramiko.SSHException as e:
            # Erros relacionados ao SSH/execução do canal
            raise RuntimeError(f"Erro SSH ao executar '{cmd}': {e}") from e
        except Exception as e:
            # Re-lança exceção depois de adicionar contexto
            raise RuntimeError(f"Erro ao executar '{cmd}': {e}") from e

    return resultados

# --------------------------
# Exemplo de uso:
# --------------------------
if __name__ == "__main__":
    
    
    
    DOTENV_PATH = Path(__file__).with_name('ini.env')
    load_dotenv(dotenv_path=DOTENV_PATH)

    # diagnóstico opcional
    if not DOTENV_PATH.exists():
        print(f"[AVISO] .env não encontrado em: {DOTENV_PATH}")
    else:
        print(f"[OK] .env carregado de: {DOTENV_PATH}")




    HOST = os.getenv("SSH_HOST")
    USER = os.getenv("SSH_USER")
    PASS = os.getenv("SSH_PASS")        # senha SSH (usuário remoto)
    SUDO_PASS = os.getenv("SSH_PASS") or PASS  # senha para sudo (pode ser igual à PASS)

    if not all([HOST, USER, PASS]):
        raise SystemExit("Defina SSH_HOST, SSH_USER e SSH_PASS no ambiente/.env")

    # conecta via Paramiko
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=100)

    comandos = [
        "cd",
        "ls",
        "vi .config/oxidized/router.db",       
        "e"    # exemplo
    ]

    try:
        resultados = run_commands_with_sudo(ssh, SUDO_PASS, comandos, stop_on_error=False, timeout=60)
        for r in resultados:
            print(">>> CMD:", r["command"])
            print("RC:", r["rc"])
            print("OK:", r["ok"])
            print("STDOUT:\n", r["stdout"])
            print("STDERR:\n", r["stderr"])
            print("-" * 40)
    finally:
        ssh.close()
