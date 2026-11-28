import os
import sys

import flet as ft
from dotenv import load_dotenv

load_dotenv()
# Añadir directorio 'src' al path de Python
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE, "src"))

from dominio.controlador_lectura import ControladorLectura
from dominio.servicio_autenticacion import ServicioAutenticacion
from dominio.servicio_gestor_grupo import GestorGrupos
from persistencia.repo_hibirido import RepositorioHibrido
from persistencia.repo_json import RepositorioJSON
from persistencia.repo_supabase import RepositorioSupabase
from presentacion.app_flet import ControladorUI


def main():
    print("Iniciando LeerJuntos Flet UI...")
    # 1. Instanciar Repositorio JSON (crea data/libros.json y data/sesiones.json si no existen)
    repo_local = RepositorioJSON(ruta_base=os.path.join(BASE, "data"))

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
    gestor_grupo = GestorGrupos(repositorio=repo_hibrido)
    controlador = ControladorLectura(repositorio=repo_hibrido)
    servicio_auth = ServicioAutenticacion(repositorio=repo_hibrido)

    # 5. arrancar con app Flet
    def startup(page: ft.Page):
        page.title = "Time Turner"

        app_flet = ControladorUI(
            controlador=controlador,
            servicio_auth=servicio_auth,
            gestor_grupos=gestor_grupo,
        )
        app_flet.main(page)

    ft.run(startup)


if __name__ == "__main__":
    main()
