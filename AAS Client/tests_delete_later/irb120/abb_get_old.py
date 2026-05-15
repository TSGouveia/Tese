import requests
from requests.auth import HTTPDigestAuth
import xml.etree.ElementTree as ET
import time

# Configurações baseadas no teu XML
ROBOT_IP = "192.168.1.1"  # Altera para o IP real se necessário
USER = "Default User"
PASS = "robotics"
URL = f"http://{ROBOT_IP}/rw/motionsystem/mechunits/ROB_1/jointtarget"


def get_abb_joints_xml():
    # Usamos Session para manter cookies, mas passamos Auth explicitamente
    session = requests.Session()
    auth = HTTPDigestAuth(USER, PASS)

    print(f"A ler juntas de {URL}...")

    try:
        while True:
            # Fazemos o request
            response = session.get(URL, auth=auth, timeout=5)

            if response.status_code == 200:
                # O RWS retorna XHTML. Vamos parsear o XML
                root = ET.fromstring(response.text)

                # Namespace do teu XML
                ns = {'ns': 'http://www.w3.org/1999/xhtml'}

                # Procura os spans rax_1 a rax_6
                joints = []
                for i in range(1, 7):
                    tag = f"rax_{i}"
                    value = root.find(f".//ns:span[@class='{tag}']", ns)
                    if value is not None:
                        joints.append(float(value.text))

                print(f"\rJoints (deg): {joints}", end="", flush=True)

            elif response.status_code == 503:
                print("\n[503] Servidor ocupado. A tentar recuperar...")
                time.sleep(1)
            else:
                print(f"\nErro {response.status_code}: {response.text}")
                break

            # Intervalo de 200ms para não sobrecarregar o controlador
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\nParado pelo utilizador.")
    except Exception as e:
        print(f"\nErro na execução: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    get_abb_joints_xml()