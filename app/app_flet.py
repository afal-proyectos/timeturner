"""
LeerJuntos - Controlador de la IU (Flet).

Ejecutar desde la carpeta app/:   python app_flet.py

Responsabilidades:
  * Montar el layout (contenido + barra inferior permanente).
  * Navegar entre vistas estáticas (01-04) y abrir diálogos flotantes (10-13).
  * Mantener el estado de la UI: usuario, libro activo y sesión de lectura en curso.
"""

import hashlib
import hmac
import importlib
import json
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import flet as ft

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE, "src"))

from dominio.controlador_lectura import ControladorLectura  # noqa: E402
from dominio.models_sesion import EstadoSesion  # noqa: E402
from persistencia.repo_json import RepositorioJSON  # noqa: E402

from presentacion.ui_comun import BLANCO, boton  # noqa: E402

MAX_CARACTERES = 8


# --------------------------------------------------------------------------
# Cuentas (provisional: almacenamiento local en data/usuarios.json)
# --------------------------------------------------------------------------
class GestorCuentaLocal:
    """
    Cuentas de usuario en JSON local. La contraseña se guarda con hash (PBKDF2).
    Provisional: IRepositorioDatos aún no tiene crear_usuario/obtener_usuario,
    cuando existan, esta clase se reemplaza por GestorCuentaUsuario.
    """

    def __init__(self, ruta: str):
        self.ruta = ruta
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        if not os.path.exists(ruta):
            self._guardar([])

    def _leer(self) -> list:
        try:
            with open(self.ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _guardar(self, usuarios: list) -> None:
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump(usuarios, f, indent=4, ensure_ascii=False)

    @staticmethod
    def _hash(clave: str, sal_hex: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256", clave.encode("utf-8"), bytes.fromhex(sal_hex), 100_000
        ).hex()

    @staticmethod
    def _publico(u: dict) -> dict:
        return {k: u[k] for k in ("id_usuario", "email", "apodo", "rol")}

    def crear(self, email: str, apodo: str, clave: str) -> dict:
        email, apodo = email.strip(), apodo.strip()
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValueError("Correo no válido.")
        if not 1 <= len(apodo) <= MAX_CARACTERES:
            raise ValueError(
                f"El apodo debe tener entre 1 y {MAX_CARACTERES} caracteres."
            )
        if not 1 <= len(clave) <= MAX_CARACTERES:
            raise ValueError(
                f"La contraseña debe tener entre 1 y {MAX_CARACTERES} caracteres."
            )

        usuarios = self._leer()
        if any(u["apodo"].lower() == apodo.lower() for u in usuarios):
            raise ValueError("Ese apodo ya está en uso.")
        if any(u["email"].lower() == email.lower() for u in usuarios):
            raise ValueError("Ese correo ya está registrado.")

        sal = os.urandom(16).hex()
        usuario = {
            "id_usuario": str(uuid.uuid4()),
            "email": email,
            "apodo": apodo,
            "clave_hash": self._hash(clave, sal),
            "sal": sal,
            "rol": "lector",
            "fecha_registro": datetime.now(timezone.utc).isoformat(),
        }
        usuarios.append(usuario)
        self._guardar(usuarios)
        return self._publico(usuario)

    def autenticar(self, apodo: str, clave: str) -> Optional[dict]:
        for u in self._leer():
            if u["apodo"].lower() == apodo.strip().lower():
                if hmac.compare_digest(u["clave_hash"], self._hash(clave, u["sal"])):
                    return self._publico(u)
                return None
        return None


# --------------------------------------------------------------------------
# Controlador de la IU
# --------------------------------------------------------------------------
class ControladorUI:
    def __init__(self, page: ft.Page, controlador: ControladorLectura, cuentas):
        self.page = page
        self.controlador = controlador
        self.repo = controlador.repo
        self.cuentas = cuentas

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
    def iniciar(self) -> None:
        page = self.page
        page.title = "LeerJuntos"
        page.bgcolor = BLANCO
        page.padding = 0
        page.theme_mode = ft.ThemeMode.LIGHT
        try:
            page.window.width, page.window.height = 440, 820
        except AttributeError:  # Flet < 0.27
            page.window_width, page.window_height = 440, 820

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
            except Exception:
                pass
        else:
            dialogo.open = False
            self.page.update()

    # ---------------- Usuario ----------------
    def iniciar_sesion_usuario(self, usuario: dict) -> None:
        self.usuario = usuario
        self.libro_activo = self._libro_por_defecto()
        self.cerrar_dialogo()
        self._actualizar_barra()
        self.navegar("01_inicio")

    # ---------------- Datos de biblioteca ----------------
    def resumen_libros(self) -> list[dict]:
        """Libros del usuario ordenados del último leído al más antiguo."""
        minimo = datetime.min.replace(tzinfo=timezone.utc)
        resumen = []
        for libro in self.controlador.obtener_biblioteca(self.usuario["id_usuario"]):
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
        ahora = datetime.now(timezone.utc)
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


# --------------------------------------------------------------------------
def main(page: ft.Page) -> None:
    ruta_datos = os.path.join(BASE, "data")
    repositorio = RepositorioJSON(ruta_base=ruta_datos)
    controlador = ControladorLectura(repositorio=repositorio)
    cuentas = GestorCuentaLocal(os.path.join(ruta_datos, "usuarios.json"))
    ControladorUI(page, controlador, cuentas).iniciar()


if __name__ == "__main__":
    if hasattr(ft, "run"):  # Flet 1.x
        ft.run(main)
    else:
        ft.app(target=main)
