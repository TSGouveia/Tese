import rtde_receive
import time

ROBOT_IP = "192.168.2.2"


def monitor_ur3e():
    try:
        print(f"Conectando ao UR3e em {ROBOT_IP}...")
        rtde_r = rtde_receive.RTDEReceiveInterface(ROBOT_IP)
        print("Conectado! Pressione Ctrl+C para parar.")

        while True:
            # getActualQ() lê os radianos das 6 juntas
            joints = rtde_r.getActualQ()

            # Formatação para mostrar apenas 3 casas decimais
            formatted_joints = [round(j, 3) for j in joints]
            print(f"\rUR3e Joints (rad): {formatted_joints}", end="")

            time.sleep(0.1)  # Atualiza a cada 100ms

    except KeyboardInterrupt:
        print("\nMonitorização interrompida pelo utilizador.")
    except Exception as e:
        print(f"\nErro: {e}")


if __name__ == "__main__":
    monitor_ur3e()