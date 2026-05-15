import socket
import struct
import time


def dump_all_floats(robot_ip, port=11002):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(2.0)

    print(f"A ligar a {robot_ip}:{port}...")
    try:
        client_socket.connect((robot_ip, port))
        print("Ligado! A extrair floats do stream...\n")

        while True:
            data = client_socket.recv(1024)
            if not data:
                break

            # Um float de 4 bytes precisa de blocos múltiplos de 4 para ser lido
            # Vamos alinhar o tamanho do pacote recebido
            tamanho_alinhado = (len(data) // 4) * 4
            if tamanho_alinhado < 16:
                continue

            bytes_para_ler = data[:tamanho_alinhado]

            # Desempacota TUDO o que for float de 4 bytes (Big-Endian)
            num_floats = len(bytes_para_ler) // 4
            todos_os_floats = struct.unpack(f'!{num_floats}f', bytes_para_ler)

            print(f"\n--- Novo Bloco Detetado ({len(data)} bytes) ---")

            # Vamos imprimir os floats e a sua posição (índice) no pacote
            # para saberes exatamente onde eles estão
            for i, f in enumerate(todos_os_floats):
                # Ignoramos valores absurdamente gigantes (Nan ou infinitos locais)
                if -100000 < f < 100000:
                    # Se o valor for muito pequeno (próximo de 0), limpamos o ruído visual
                    val = 0.0 if abs(f) < 0.0001 else round(f, 4)
                    print(f"  [Float Índice {i} (Byte {i * 4})]: {val}")

            time.sleep(0.5)  # Pausa para conseguires ler a consola

    except KeyboardInterrupt:
        print("\nParado pelo utilizador.")
    finally:
        client_socket.close()


if __name__ == "__main__":
    dump_all_floats("192.168.1.1")