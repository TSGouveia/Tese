import rtde_control
import time

ROBOT_IP = "192.168.2.2"

# Parâmetros de movimento seguros (velocidade baixa para testes)
SPEED = 0.2  # rad/s
ACCELERATION = 0.2  # rad/s²


def move_to_dummy_joints():
    try:
        print("\n--- UR3e Dummy Joint Command ---")
        print(f"A conectar ao UR3e em {ROBOT_IP}...")

        # Inicializa a interface de controlo
        rtde_c = rtde_control.RTDEControlInterface(ROBOT_IP)
        print("Conectado com sucesso!")

        # -------------------------------------------------------------
        # DEFINIÇÃO DAS JUNTAS DUMMY (em radianos)
        # Ordem: [Base, Shoulder, Elbow, Wrist 1, Wrist 2, Wrist 3]
        # -------------------------------------------------------------
        # Exemplo: Posição "Home" vertical aproximada
        dummy_joints = [0.0, -1.57, 1.57, -1.57, -1.57, 0.0]

        print(f"\nA enviar robô para as juntas dummy: {dummy_joints}")
        print("A mover... Por favor, aguarde.")

        # O script vai bloquear aqui até o robô chegar ao destino
        rtde_c.moveJ(dummy_joints, SPEED, ACCELERATION, asynchronous=False)

        print("\nMovimento concluído com sucesso!")

    except KeyboardInterrupt:
        print("\nProcesso interrompido pelo utilizador.")
    except Exception as e:
        print(f"\nErro Crítico: {e}")
    finally:
        # Garante o fecho limpo da ligação
        if 'rtde_c' in locals():
            rtde_c.disconnect()
            print("Conexão RTDE fechada.")


if __name__ == "__main__":
    move_to_dummy_joints()