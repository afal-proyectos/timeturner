"""
Responsabilidades:
  * Montar el layout (contenido + barra inferior permanente).
  * Navegar entre vistas estáticas (01-04) y abrir diálogos flotantes (10-13).
  * Mantener el estado de la UI: usuario, libro activo y sesión de lectura en curso.
"""

import importlib
import threading
import time
from datetime import UTC, datetime

import flet as ft
from dominio.controlador_lectura import ControladorLectura  # noqa: E402
from dominio.models_sesion import EstadoSesion  # noqa: E402
from dominio.servicio_gestor_grupo import GestorGrupos

from presentacion.ui_comun import BLANCO, boton  # noqa: E402

MAX_CARACTERES = 8


# --------------------------------------------------------------------------
# Controlador de la IU
# --------------------------------------------------------------------------
class ControladorUI:
    def __init__(
        self,
        controlador: ControladorLectura,
        servicio_auth,
        gestor_grupos: GestorGrupos,
    ):

        self.controlador = controlador
        self.repo = controlador.repo
        self.servicio_auth = servicio_auth
        self.gestor_grupos = gestor_grupos  # GestorGrupos (dominio); None = sin grupos

        # Estado
        self.usuario: dict | None = None
        self.libro_activo = None
        self.sesion = None
        self.mensaje = ""
        self.vista_actual = "01_inicio"
        self.vista_kw: dict = {}

        # Cronómetro / diálogos
        self.tick_cb = None
        self._parar = threading.Event()
        self._dialogo = None

    # ---------------- Arranque y layout ----------------
    def main(self, page):
        self.page = page
        self.iniciar()

    def iniciar(self) -> None:
        page = self.page
        page.title = "LeerJuntos"
        page.bgcolor = BLANCO
        page.padding = 0
        page.theme_mode = ft.ThemeMode.LIGHT
        try:
            page.window.width, page.window.height = 440, 620
        except AttributeError:  # Flet < 0.27
            page.window_width, page.window_height = 440, 620

        self.contenedor = ft.Container(expand=True, padding=16)
        self.btn_stats = boton(
            "Estadísticas",
            lambda e: self.navegar("04_estadistica_usuario"),
            icono=ft.Icons.BAR_CHART,
            expand=True,
            tam=12,
        )
        self.btn_nuevo = boton(
            "Nuevo libro",
            lambda e: self.abrir_dialogo("13_nuevo_libro"),
            rojo=True,
            icono=ft.Icons.ADD,
            expand=True,
            tam=12,
        )
        self.btn_biblio = boton(
            "Biblioteca",
            lambda e: self.navegar("02_biblioteca_completa"),
            icono=ft.Icons.MENU_BOOK,
            expand=True,
            tam=12,
        )
        barra = ft.Container(
            content=ft.Row(
                [self.btn_stats, self.btn_nuevo, self.btn_biblio], spacing=8
            ),
            padding=10,
            bgcolor=BLANCO,
        )
        self._actualizar_barra()
        page.add(ft.Column([self.contenedor, barra], expand=True, spacing=0))

        # Siempre se pide usuario al arrancar
        self.abrir_dialogo("10_cuenta")

    def _actualizar_barra(self) -> None:
        bloqueada = self.usuario is None
        for b in (self.btn_stats, self.btn_nuevo, self.btn_biblio):
            b.disabled = bloqueada

    # ---------------- Navegación y diálogos ----------------
    def navegar(self, nombre: str, **kw) -> None:
        self.tick_cb = None
        self.vista_actual, self.vista_kw = nombre, kw
        modulo = importlib.import_module(f"presentacion.{nombre}")
        self.contenedor.content = ft.Column(
            [modulo.construir(self, **kw)], scroll=ft.ScrollMode.AUTO, expand=True
        )
        self.page.update()

    def refrescar_vista(self) -> None:
        self.navegar(self.vista_actual, **self.vista_kw)

    def abrir_dialogo(self, nombre: str, **kw) -> None:
        modulo = importlib.import_module(f"presentacion.{nombre}")
        self.mostrar_dialogo(modulo.crear_dialogo(self, **kw))

    def mostrar_dialogo(self, dialogo) -> None:
        self.cerrar_dialogo()
        self._dialogo = dialogo
        if hasattr(self.page, "show_dialog"):  # Flet 1.x
            self.page.show_dialog(dialogo)
        else:
            self.page.dialog = dialogo
            dialogo.open = True
            self.page.update()

    def cerrar_dialogo(self) -> None:
        dialogo, self._dialogo = self._dialogo, None
        if dialogo is None:
            return
        if hasattr(self.page, "pop_dialog"):  # Flet 1.x
            try:
                self.page.pop_dialog()
            except Exception as e:
                print(f"No se a cerrado el dialogo{e}")
        else:
            dialogo.open = False
            self.page.update()

    # ---------------- Usuario ----------------
    def iniciar_sesion_usuario(self, usuario) -> None:
        """Recibe la entidad Usuario; la UI guarda solo lo necesario (sin la clave)."""
        self.usuario = {
            "id_usuario": usuario.id_usuario,
            "apodo": usuario.apodo,
            "email": usuario.email,
        }
        self.libro_activo = self._libro_por_defecto()
        self.cerrar_dialogo()
        self._actualizar_barra()
        self.navegar("01_inicio")

    def cerrar_sesion_usuario(self) -> None:
        if self.sesion_activa:
            self.mensaje = "Termina la sesión de lectura antes de cerrar sesión."
            self.refrescar_vista()
            return
        self._parar.set()
        self.usuario = None
        self.libro_activo = None
        self.sesion = None
        self.mensaje = ""
        self.contenedor.content = None
        self._actualizar_barra()  # vuelve a bloquear la barra inferior
        self.abrir_dialogo("10_cuenta")

    # ---------------- Datos de biblioteca ----------------
    def resumen_libros(self, usuario_id: str | None = None) -> list[dict]:
        """Libros de un usuario (por defecto el actual), del último leído al más antiguo."""
        usuario_id = usuario_id or self.usuario["id_usuario"]
        minimo = datetime.min.replace(tzinfo=UTC)
        resumen = []
        for libro in self.controlador.obtener_biblioteca(usuario_id):
            sesiones = self.repo.obtener_sesiones(libro.id_libro)
            marcas = [s.fin_utc or s.inicio_utc for s in sesiones]
            marcas = [m for m in marcas if m]
            pagina_actual = max(
                (s.pagina_fin for s in sesiones if s.pagina_fin is not None), default=0
            )
            resumen.append(
                {
                    "libro": libro,
                    "sesiones": sesiones,
                    "ultima": max(marcas, default=None),
                    "pagina_actual": pagina_actual,
                    "porcentaje": libro.calcular_porcentaje_avance(pagina_actual),
                }
            )
        resumen.sort(key=lambda r: r["ultima"] or minimo, reverse=True)
        return resumen

    def _libro_por_defecto(self):
        resumen = self.resumen_libros()
        return resumen[0]["libro"] if resumen else None

    def seleccionar_libro(self, libro) -> bool:
        if self.sesion_activa:
            self.mensaje = "Termina la sesión en curso antes de cambiar de libro."
            return False
        self.libro_activo = libro
        self.mensaje = ""
        return True

    def pagina_sugerida(self) -> int:
        if not self.libro_activo:
            return 0
        sesiones = self.repo.obtener_sesiones(self.libro_activo.id_libro)
        return max(
            (s.pagina_fin for s in sesiones if s.pagina_fin is not None), default=0
        )

    # ---------------- Grupos ----------------
    def apodo_de(self, id_usuario: str) -> str:
        if self.usuario and id_usuario == self.usuario["id_usuario"]:
            return self.usuario["apodo"]
        usuario = self.repo.obtener_usuario_por_id(id_usuario)
        return usuario.apodo if usuario else id_usuario[:8]

    def miembros_grupo(self, grupo) -> list[dict]:
        """Miembros del grupo como [{'id_usuario', 'apodo'}], ordenados por apodo."""
        ids = self.gestor_grupos.repo.obtener_miembros_grupo(grupo.id_grupo)
        miembros = [{"id_usuario": i, "apodo": self.apodo_de(i)} for i in ids]
        return sorted(miembros, key=lambda m: m["apodo"].lower())

    # ---------------- Sesión de lectura / cronómetro ----------------
    @property
    def sesion_activa(self) -> bool:
        return self.sesion is not None and self.sesion.estado in (
            EstadoSesion.LEYENDO,
            EstadoSesion.PAUSADA,
        )

    @property
    def sesion_pausada(self) -> bool:
        return self.sesion is not None and self.sesion.estado == EstadoSesion.PAUSADA

    def comenzar_sesion(self, pagina_inicio: int) -> None:
        self.mensaje = ""
        self.sesion = self.controlador.iniciar_sesion_lectura(
            libro_id=self.libro_activo.id_libro,
            usuario_id=self.usuario["id_usuario"],
            pagina_inicio=pagina_inicio,
        )
        self._parar.clear()
        threading.Thread(target=self._bucle_cronometro, daemon=True).start()

    def alternar_pausa(self) -> None:
        if not self.sesion:
            return
        if self.sesion.estado == EstadoSesion.LEYENDO:
            self.sesion.pausar()
        elif self.sesion.estado == EstadoSesion.PAUSADA:
            self.sesion.reanudar()

    def finalizar_sesion(self, pagina_fin: int) -> None:
        resultado = self.controlador.finalizar_y_guardar_sesion(self.sesion, pagina_fin)
        met = resultado["metricas_sesion"]
        self.mensaje = (
            f"Sesión guardada: {met['paginas_leidas']} págs en "
            f"{met['minutos_netos']} min ({met['velocidad_ppm']} págs/min)."
        )
        self.sesion = None
        self._parar.set()

    def segundos_transcurridos(self) -> float:
        s = self.sesion
        if not s or not s.inicio_utc:
            return 0.0
        ahora = datetime.now(UTC)
        pausa = s.minutos_pausa * 60.0
        if s.estado == EstadoSesion.PAUSADA and s._inicio_pausa_temp:
            pausa += (ahora - s._inicio_pausa_temp).total_seconds()
        return max((ahora - s.inicio_utc).total_seconds() - pausa, 0.0)

    def cronometro_texto(self) -> str:
        total = int(self.segundos_transcurridos())
        h, resto = divmod(total, 3600)
        m, s = divmod(resto, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _bucle_cronometro(self) -> None:
        while not self._parar.is_set():
            cb = self.tick_cb
            if cb:
                try:
                    cb()
                except Exception:
                    self.tick_cb = None  # el control ya no está en pantalla
            time.sleep(0.5)
