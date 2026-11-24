import os
import sys

from dotenv import load_dotenv

load_dotenv()
# Añadir directorio 'src' al path de Python
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))


from src.dominio.controlador_lectura import ControladorLectura
from src.persistencia.repo_hibirido import RepositorioHibrido
from src.persistencia.repo_json import RepositorioJSON
from src.persistencia.repo_supabase import RepositorioSupabase
from src.presentacion.cliente import CLI


def main():
    print("Iniciando LeerJuntos con Repositorio Híbrido (Offline-First)...")

    # 1. Instanciar Repositorio JSON (crea data/libros.json y data/sesiones.json si no existen)
    repo_local = RepositorioJSON(ruta_base="data")

    # 2. Repositorio en la Nube
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

    repo_nube = None
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            repo_nube = RepositorioSupabase(SUPABASE_URL, SUPABASE_KEY)
            print("🟢 Conexión a Supabase configurada exitosamente.")
        except Exception as e:
            print(f"⚠️ No se pudo conectar a Supabase: {e}. Se operará en Modo Local.")

    # 3. Instanciar Repositorio Híbrido (combina ambos)
    repo_hibrido = RepositorioHibrido(repo_local=repo_local, repo_nube=repo_nube)

    # 3.5 Intento automático de vaciar la cola de pendientes al iniciar
    if repo_nube and repo_hibrido.pendientes_sync:
        print(
            f"🔄 Procesando {len(repo_hibrido.pendientes_sync)} elementos pendientes en cola_sync..."
        )
        resumen = repo_hibrido.sincronizar_pendientes()
        print(
            f"☁️ Sincronización completada: {resumen['exitosos']} subidos, {resumen['pendientes']} pendientes."
        )

    # 4. Instanciar Controlador de la Capa de Dominio
    controlador = ControladorLectura(repositorio=repo_hibrido)

    # 5. Lanzar Interfaz CLI
    app = CLI(
        controlador=controlador,
        usuario_id_defecto="00000000-0000-0000-0000-000000000001",
    )
    app.iniciar()


if __name__ == "__main__":
    main()
