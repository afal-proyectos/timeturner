import flet as ft
import flet_charts as fch  # pip install flet-charts
from dominio.calcular_proyecciones import CalculadorProyecciones
from dominio.controlador_lectura import ControladorLectura
from dominio.models_sesion import EstadoSesion
from dominio.servicio_autenticacion import ServicioAutenticacion
from dominio.servicio_gestor_grupo import GestorGrupos


def _boton(texto, color_fondo, on_click, **kwargs):
    """Botón estándar de la demo (azul o rojo, texto blanco)."""
    return ft.Button(
        content=texto,
        bgcolor=color_fondo,
        color=ft.Colors.WHITE,
        on_click=on_click,
        **kwargs,
    )


class AppFlet:
    """Interfaz Móvil en Flet para Time Tuerner (Simulación Smartphone FHD 1080x2400)."""

    def __init__(
        self,
        controlador: ControladorLectura,
        servicio_auth: ServicioAutenticacion,
        gestor_grupos: GestorGrupos,
    ):
        self.controlador = controlador
        self.servicio_auth = servicio_auth
        self.gestor_grupos = gestor_grupos
        self.usuario_actual = None
        self.sesion_activa = None
        self.libro_seleccionado = None

    def main(self, page: ft.Page):
        self.page = page
        self.page.title = "Time Turner - FHD Mobile Prototype"

        # Proporción de aspecto 1080 x 2400 px (Píxeles lógicos Flet)
        self.page.window.width = 360
        self.page.window.height = 780
        self.page.window.resizable = False
        self.page.update()
        print("Prueba ventana", self.page.window.width, self.page.window.height)
        self.page.bgcolor = ft.Colors.WHITE
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 16

        # Mostrar Modal de Autenticación al Iniciar
        self._abrir_modal_login()

    # ========================================================
    # Helpers de diálogos
    # ========================================================

    def _mostrar_dialog(self, dlg: ft.AlertDialog):
        self.page.show_dialog(dlg)

    def _cerrar_dialog(self, e=None):
        self.page.pop_dialog()

    # ========================================================
    # 1. MODALES FLOTANTES DE AUTENTICACIÓN (LOGIN / REGISTRO)
    # ========================================================

    def _abrir_modal_login(self, e=None):
        txt_alias = ft.TextField(
            label="Alias (máx 8 chars)",
            max_length=8,
            color=ft.Colors.BLACK,
            border_color=ft.Colors.GREY_400,
        )
        txt_pass = ft.TextField(
            label="Contraseña",
            password=True,
            can_reveal_password=True,
            color=ft.Colors.BLACK,
            border_color=ft.Colors.GREY_400,
        )
        lbl_error = ft.Text("", color=ft.Colors.RED_600, size=12)

        def ejecutar_login(e):
            exito, msj, usr = self.servicio_auth.iniciar_sesion(
                txt_alias.value or "", txt_pass.value or ""
            )
            if exito and usr:
                self.usuario_actual = usr
                self._cerrar_dialog()
                self._renderizar_vista_principal()
            else:
                lbl_error.value = msj
                self.page.update()

        dlg_login = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "📚 TimeTurner - Iniciar Sesión",
                color=ft.Colors.BLACK,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Column(
                [txt_alias, txt_pass, lbl_error],
                tight=True,
                spacing=10,
            ),
            actions=[
                _boton(
                    "Crear Cuenta",
                    ft.Colors.BLUE_600,
                    lambda _: self._abrir_modal_registro(),
                ),
                _boton("Entrar", ft.Colors.BLUE_600, ejecutar_login),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=ft.Colors.WHITE,
        )

        self._mostrar_dialog(dlg_login)

    def _abrir_modal_registro(self):
        # Cierra el diálogo de login que está debajo
        self._cerrar_dialog()

        txt_email = ft.TextField(label="Correo Electrónico", color=ft.Colors.BLACK)
        txt_alias = ft.TextField(
            label="Alias (máx 8 chars)", max_length=8, color=ft.Colors.BLACK
        )
        txt_pass = ft.TextField(
            label="Contraseña (4-8 chars)", password=True, color=ft.Colors.BLACK
        )
        lbl_error = ft.Text("", color=ft.Colors.RED_600, size=12)

        def ejecutar_registro(e):
            exito, msj, usr = self.servicio_auth.registrar_usuario(
                txt_email.value or "", txt_alias.value or "", txt_pass.value or ""
            )
            if exito and usr:
                self.usuario_actual = usr
                self._cerrar_dialog()
                self._renderizar_vista_principal()
            else:
                lbl_error.value = msj
                self.page.update()

        def cancelar(e):
            self._cerrar_dialog()
            self._abrir_modal_login()

        dlg_reg = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "📝 Registro de Usuario",
                color=ft.Colors.BLACK,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Column(
                [txt_email, txt_alias, txt_pass, lbl_error],
                tight=True,
                spacing=10,
            ),
            actions=[
                _boton("Cancelar", ft.Colors.RED_600, cancelar),
                _boton("Guardar Usuario", ft.Colors.BLUE_600, ejecutar_registro),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            bgcolor=ft.Colors.WHITE,
        )

        self._mostrar_dialog(dlg_reg)

    # ========================================================
    # 2. VISTA PRINCIPAL (BIBLIOTECA Y CONTROLES)
    # ========================================================

    def _renderizar_vista_principal(self):
        self.page.clean()

        # Encabezado Móvil
        header = ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(
                            f"Hola, {self.usuario_actual.apodo} 👋",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLACK,
                        ),
                        ft.Text(
                            "Mi Biblioteca de Lectura",
                            size=14,
                            color=ft.Colors.GREY_700,
                        ),
                    ],
                    spacing=2,
                ),
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.GROUP,
                            icon_color=ft.Colors.RED_600,
                            tooltip="Mis Grupos",
                            on_click=lambda _: self._abrir_modal_mis_grupos(),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.LOGOUT,
                            icon_color=ft.Colors.RED_600,
                            tooltip="Cerrar Sesión",
                            on_click=self._abrir_modal_login,
                        ),
                    ],
                    spacing=0,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Botón Azul para Añadir Libro
        btn_nuevo_libro = _boton(
            "+ Agregar Nuevo Libro",
            ft.Colors.BLUE_600,
            lambda _: self._abrir_modal_crear_libro(),
            width=380,
            height=45,
        )

        # Lista de Libros
        self.list_view_libros = ft.ListView(expand=True, spacing=10)
        self._cargar_lista_libros()

        self.page.add(
            ft.Column(
                [
                    header,
                    ft.Divider(color=ft.Colors.GREY_300),
                    btn_nuevo_libro,
                    self.list_view_libros,
                ],
                expand=True,
                spacing=15,
            )
        )
        self.page.update()

    def _cargar_lista_libros(self):
        self.list_view_libros.controls.clear()
        libros = self.controlador.obtener_biblioteca(self.usuario_actual.id_usuario)

        if not libros:
            self.list_view_libros.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No tienes libros registrados aún.",
                        color=ft.Colors.GREY_600,
                        italic=True,
                    ),
                    alignment=ft.Alignment.CENTER,
                    padding=20,
                )
            )
        else:
            for libro in libros:
                sesiones = self.controlador.repo.obtener_sesiones(libro.id_libro)
                pag_actual = max(
                    [s.pagina_fin for s in sesiones if s.pagina_fin] or [0]
                )
                pct = libro.calcular_porcentaje_avance(pag_actual)

                card = ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.BOOK, color=ft.Colors.BLUE_600),
                                    ft.Text(
                                        libro.titulo,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.BLACK,
                                        size=16,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.START,
                            ),
                            ft.Text(
                                f"Autor: {libro.autor} | {libro.total_paginas} págs",
                                color=ft.Colors.BLACK,
                            ),
                            ft.ProgressBar(
                                value=pct / 100.0,
                                color=ft.Colors.BLUE_600,
                                bgcolor=ft.Colors.GREY_200,
                            ),
                            ft.Row(
                                [
                                    ft.Text(
                                        f"Avance: {pct}% (Pág {pag_actual})",
                                        color=ft.Colors.GREY_800,
                                        size=12,
                                    ),
                                    ft.Row(
                                        [
                                            _boton(
                                                "📊 Métricas",
                                                ft.Colors.BLUE_600,
                                                lambda _, l=libro: (
                                                    self._abrir_modal_metricas(l)
                                                ),
                                            ),
                                            _boton(
                                                "⏱️ Leer",
                                                ft.Colors.BLUE_600,
                                                lambda _, l=libro, p=pag_actual: (
                                                    self._abrir_modal_cronometro(l, p)
                                                ),
                                            ),
                                        ],
                                        spacing=5,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=12,
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    bgcolor=ft.Colors.WHITE,
                )
                self.list_view_libros.controls.append(card)

    # ========================================================
    # 3. MODAL FLOTANTE DE REGISTRO DE LIBRO
    # ========================================================

    def _abrir_modal_crear_libro(self):
        txt_titulo = ft.TextField(label="Título del libro", color=ft.Colors.BLACK)
        txt_autor = ft.TextField(label="Autor", color=ft.Colors.BLACK)
        txt_genero = ft.TextField(label="Género", color=ft.Colors.BLACK)
        txt_paginas = ft.TextField(
            label="Total de Páginas",
            keyboard_type=ft.KeyboardType.NUMBER,
            color=ft.Colors.BLACK,
        )
        lbl_err = ft.Text("", color=ft.Colors.RED_600, size=12)

        def guardar_libro(e):
            try:
                tot = int(txt_paginas.value or "0")
                if tot <= 0:
                    raise ValueError("Páginas debe ser mayor a 0.")
                self.controlador.registrar_libro(
                    usuario_id=self.usuario_actual.id_usuario,
                    titulo=txt_titulo.value or "",
                    autor=txt_autor.value or "",
                    genero=txt_genero.value or "",
                    total_paginas=tot,
                )
                self._cerrar_dialog()
                self._cargar_lista_libros()
                self.page.update()
            except Exception as ex:
                lbl_err.value = str(ex)
                self.page.update()

        dlg_libro = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "📖 Nuevo Libro", color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD
            ),
            content=ft.Column(
                [txt_titulo, txt_autor, txt_genero, txt_paginas, lbl_err],
                tight=True,
                spacing=8,
            ),
            actions=[
                _boton("Cancelar", ft.Colors.RED_600, self._cerrar_dialog),
                _boton("Guardar Libro", ft.Colors.BLUE_600, guardar_libro),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            bgcolor=ft.Colors.WHITE,
        )
        self._mostrar_dialog(dlg_libro)

    # ========================================================
    # 4. MODAL FLOTANTE DE CRONÓMETRO DE LECTURA (SESIÓN ACTIVA)
    # ========================================================

    def _abrir_modal_cronometro(self, libro, pagina_sugerida: int):
        self.libro_seleccionado = libro
        self.sesion_activa = self.controlador.iniciar_sesion_lectura(
            libro_id=libro.id_libro,
            usuario_id=self.usuario_actual.id_usuario,
            pagina_inicio=pagina_sugerida,
        )

        lbl_estado = ft.Text(
            "Estado: LEYENDO 📖", color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD
        )
        txt_pag_fin = ft.TextField(
            label=f"Página final (Total: {libro.total_paginas})",
            keyboard_type=ft.KeyboardType.NUMBER,
            color=ft.Colors.BLACK,
        )
        lbl_err = ft.Text("", color=ft.Colors.RED_600, size=12)

        def alternar_pausa(e):
            if self.sesion_activa.estado == EstadoSesion.LEYENDO:
                self.sesion_activa.pausar()
                lbl_estado.value = "Estado: PAUSADA ⏸️"
                btn_pausa.content = "Reanudar"
            else:
                self.sesion_activa.reanudar()
                lbl_estado.value = "Estado: LEYENDO 📖"
                btn_pausa.content = "Pausar"
            self.page.update()

        def finalizar_sesion(e):
            try:
                p_fin = int(txt_pag_fin.value or "0")
                self.controlador.finalizar_y_guardar_sesion(self.sesion_activa, p_fin)
                self._cerrar_dialog()
                self._cargar_lista_libros()
                self.page.update()
            except Exception as ex:
                lbl_err.value = str(ex)
                self.page.update()

        btn_pausa = _boton("Pausar", ft.Colors.BLUE_600, alternar_pausa)

        dlg_crono = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                f"⏱️ Leyendo: {libro.titulo}",
                color=ft.Colors.BLACK,
                size=16,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Column(
                [
                    ft.Text(
                        f"Página inicial: {pagina_sugerida}", color=ft.Colors.BLACK
                    ),
                    lbl_estado,
                    txt_pag_fin,
                    lbl_err,
                ],
                tight=True,
                spacing=10,
            ),
            actions=[
                _boton("Cancelar", ft.Colors.RED_600, self._cerrar_dialog),
                btn_pausa,
                _boton("Detener y Guardar", ft.Colors.RED_600, finalizar_sesion),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            bgcolor=ft.Colors.WHITE,
        )
        self._mostrar_dialog(dlg_crono)

    # ========================================================
    # 5. MODAL FLOTANTE DE MÉTRICAS Y GRÁFICAS MATEMÁTICAS
    # ========================================================

    def _abrir_modal_metricas(self, libro):
        sesiones = self.controlador.repo.obtener_sesiones(libro.id_libro)
        pares = CalculadorProyecciones.obtener_pares_ordenados(sesiones)

        # Gráfico de líneas para los pares ordenados (Tiempo, Página)
        data_points = (
            [fch.LineChartDataPoint(x, y) for x, y in pares]
            if pares
            else [fch.LineChartDataPoint(0, 0)]
        )

        chart = fch.LineChart(
            data_series=[
                fch.LineChartData(
                    points=data_points,
                    stroke_width=3,
                    color=ft.Colors.BLUE_600,
                    curved=True,
                )
            ],
            border=ft.Border.all(1, ft.Colors.GREY_300),
            height=150,
            expand=True,
        )

        pag_actual = pares[-1][1] if pares else 0
        proy = CalculadorProyecciones.estimar_tiempo_restante(
            libro, sesiones, pag_actual
        )

        info_proy = (
            (
                f"• Horas restantes estimadas: {proy.get('horas_estimadas_restantes', 'N/A')} hrs\n"
                f"• Fecha proyectada de fin: {proy.get('fecha_estimada_fin', 'N/A')}"
            )
            if not proy.get("completado")
            else "🏆 ¡Libro completado al 100%!"
        )

        dlg_met = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                f"📊 Estadísticas: {libro.titulo}",
                color=ft.Colors.BLACK,
                size=16,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Column(
                [
                    ft.Text(
                        "Función de Lectura (Tiempo min vs Página):",
                        color=ft.Colors.BLACK,
                        size=12,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Container(content=chart, padding=5),
                    ft.Text(
                        f"• Sesiones registradas: {len(sesiones)}",
                        color=ft.Colors.BLACK,
                        size=12,
                    ),
                    ft.Text(info_proy, color=ft.Colors.BLACK, size=12),
                ],
                tight=True,
                spacing=8,
            ),
            actions=[_boton("Cerrar", ft.Colors.RED_600, self._cerrar_dialog)],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=ft.Colors.WHITE,
        )
        self._mostrar_dialog(dlg_met)

    # ========================================================
    # 6. GRUPOS DE LECTURA (LISTA, CREAR, UNIRSE, TABLERO, CHAT)
    # ========================================================
    # Navegación entre diálogos: cada paso cierra el diálogo actual
    # (pop_dialog) y abre el siguiente (show_dialog).

    def _ir_a_mis_grupos(self, e=None):
        """Cierra el diálogo actual y vuelve a la lista de grupos."""
        self._cerrar_dialog()
        self._abrir_modal_mis_grupos()

    def _abrir_modal_mis_grupos(self):
        """Muestra los grupos del usuario y permite crear o unirse."""
        grupos = self.gestor_grupos.repo.obtener_grupos_usuario(
            self.usuario_actual.id_usuario
        )
        list_grupos = ft.ListView(expand=True, spacing=10, height=250)

        if not grupos:
            list_grupos.controls.append(
                ft.Text(
                    "No perteneces a ningún grupo aún.",
                    color=ft.Colors.GREY_600,
                    italic=True,
                )
            )
        else:
            for g in grupos:
                es_admin = g.admin_id == self.usuario_actual.id_usuario
                rol_txt = " (Admin)" if es_admin else " (Miembro)"

                def ir_tablero(e, grp=g):
                    self._cerrar_dialog()
                    self._abrir_modal_tablero_cruzado(grp)

                def ir_chat(e, grp=g):
                    self._cerrar_dialog()
                    self._abrir_modal_chat(grp)

                card_g = ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                f"{g.nombre}{rol_txt}",
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLACK,
                            ),
                            ft.Text(
                                f"Código de acceso: {g.codigo_acceso}",
                                size=12,
                                color=ft.Colors.GREY_700,
                            ),
                            ft.Row(
                                [
                                    _boton(
                                        "📊 Tablero", ft.Colors.BLUE_600, ir_tablero
                                    ),
                                    _boton("💬 Chat", ft.Colors.BLUE_600, ir_chat),
                                ],
                                alignment=ft.MainAxisAlignment.END,
                                spacing=5,
                            ),
                        ],
                        spacing=5,
                    ),
                    padding=10,
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    bgcolor=ft.Colors.WHITE,
                )
                list_grupos.controls.append(card_g)

        def ir_crear(e):
            self._cerrar_dialog()
            self._abrir_modal_crear_grupo()

        def ir_unirse(e):
            self._cerrar_dialog()
            self._abrir_modal_unirse_grupo()

        dlg_grupos = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "👥 Mis Grupos de Lectura",
                color=ft.Colors.BLACK,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            _boton("+ Crear Grupo", ft.Colors.BLUE_600, ir_crear),
                            _boton("🔑 Unirse", ft.Colors.BLUE_600, ir_unirse),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    ),
                    ft.Divider(color=ft.Colors.GREY_300),
                    list_grupos,
                ],
                tight=True,
                spacing=10,
            ),
            actions=[_boton("Cerrar", ft.Colors.RED_600, self._cerrar_dialog)],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=ft.Colors.WHITE,
        )
        self._mostrar_dialog(dlg_grupos)

    def _abrir_modal_crear_grupo(self):
        txt_nombre = ft.TextField(label="Nombre del Grupo", color=ft.Colors.BLACK)
        lbl_err = ft.Text("", color=ft.Colors.RED_600, size=12)

        def ejecutar_creacion(e):
            exito, msj, g = self.gestor_grupos.crear_grupo(
                txt_nombre.value or "", self.usuario_actual.id_usuario
            )
            if exito:
                self._ir_a_mis_grupos()
            else:
                lbl_err.value = msj
                self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "➕ Crear Grupo Cerrado",
                color=ft.Colors.BLACK,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Column([txt_nombre, lbl_err], tight=True, spacing=10),
            actions=[
                _boton("Cancelar", ft.Colors.RED_600, self._ir_a_mis_grupos),
                _boton("Crear", ft.Colors.BLUE_600, ejecutar_creacion),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            bgcolor=ft.Colors.WHITE,
        )
        self._mostrar_dialog(dlg)

    def _abrir_modal_unirse_grupo(self):
        txt_codigo = ft.TextField(
            label="Código de 6 dígitos", max_length=6, color=ft.Colors.BLACK
        )
        lbl_err = ft.Text("", color=ft.Colors.RED_600, size=12)

        def ejecutar_union(e):
            exito, msj, g = self.gestor_grupos.unirse_a_grupo(
                txt_codigo.value or "", self.usuario_actual.id_usuario
            )
            if exito:
                self._ir_a_mis_grupos()
            else:
                lbl_err.value = msj
                self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "🔑 Unirse a un Grupo",
                color=ft.Colors.BLACK,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Column([txt_codigo, lbl_err], tight=True, spacing=10),
            actions=[
                _boton("Cancelar", ft.Colors.RED_600, self._ir_a_mis_grupos),
                _boton("Unirse", ft.Colors.BLUE_600, ejecutar_union),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            bgcolor=ft.Colors.WHITE,
        )
        self._mostrar_dialog(dlg)

    def _abrir_modal_tablero_cruzado(self, grupo):
        """Progreso cruzado transparente de los miembros, sin rankings competitivos."""
        tablero_data = self.gestor_grupos.obtener_tablero_cruzado(grupo.id_grupo)
        list_tablero = ft.ListView(expand=True, spacing=10, height=300)

        for item in tablero_data:
            card_usr = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            f"👤 Miembro ID: {item['usuario_id'][:8]}...",
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLACK,
                        ),
                        ft.Text(
                            f"📚 Libros: {item['total_libros']} | "
                            f"⏱️ Horas leídas: {item['total_horas_leidas']} hrs",
                            size=12,
                            color=ft.Colors.BLACK,
                        ),
                        ft.Text(
                            "Lecturas activas:",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_800,
                        ),
                        *[
                            ft.Text(
                                f"  • {l['titulo']}: {l['porcentaje']}% "
                                f"(Pág {l['pagina_actual']}/{l['total_paginas']})",
                                size=11,
                                color=ft.Colors.GREY_700,
                            )
                            for l in item["lecturas_activas"]
                        ],
                    ],
                    spacing=3,
                ),
                padding=8,
                border=ft.Border.all(1, ft.Colors.GREY_300),
                border_radius=6,
                bgcolor=ft.Colors.WHITE,
            )
            list_tablero.controls.append(card_usr)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                f"📊 Tablero Cruzado: {grupo.nombre}",
                color=ft.Colors.BLACK,
                size=16,
                weight=ft.FontWeight.BOLD,
            ),
            content=list_tablero,
            actions=[_boton("Volver", ft.Colors.RED_600, self._ir_a_mis_grupos)],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=ft.Colors.WHITE,
        )
        self._mostrar_dialog(dlg)

    def _abrir_modal_chat(self, grupo):
        """Chat grupal con envío de mensajes, stickers de ánimo y moderación."""
        es_admin = grupo.admin_id == self.usuario_actual.id_usuario
        txt_mensaje = ft.TextField(
            label="Escribe un mensaje...", color=ft.Colors.BLACK, expand=True
        )
        list_chat = ft.ListView(expand=True, spacing=8, height=250)

        def cargar_mensajes():
            list_chat.controls.clear()
            mensajes = self.gestor_grupos.obtener_chat_grupo(grupo.id_grupo)
            for m in mensajes:
                btn_borrar = []
                if es_admin:
                    btn_borrar.append(
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=ft.Colors.RED_600,
                            tooltip="Moderar / Eliminar",
                            on_click=lambda _, msg_id=m.id_mensaje: borrar_msg(msg_id),
                        )
                    )

                list_chat.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(
                                            f"ID {m.usuario_id[:8]} [{m.tipo}]:",
                                            size=10,
                                            color=ft.Colors.GREY_600,
                                        ),
                                        ft.Text(
                                            m.informacion,
                                            color=ft.Colors.BLACK,
                                            size=14,
                                        ),
                                    ],
                                    expand=True,
                                ),
                                *btn_borrar,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        padding=6,
                        border=ft.Border.all(1, ft.Colors.GREY_200),
                        border_radius=6,
                    )
                )
            self.page.update()

        def enviar_texto(e):
            if txt_mensaje.value and txt_mensaje.value.strip():
                self.gestor_grupos.enviar_mensaje(
                    grupo.id_grupo,
                    self.usuario_actual.id_usuario,
                    txt_mensaje.value.strip(),
                    tipo="TEXTO",
                )
                txt_mensaje.value = ""
                cargar_mensajes()

        def enviar_sticker(sticker_txt):
            self.gestor_grupos.enviar_mensaje(
                grupo.id_grupo,
                self.usuario_actual.id_usuario,
                sticker_txt,
                tipo="STICKER",
            )
            cargar_mensajes()

        def borrar_msg(msg_id):
            self.gestor_grupos.moderar_eliminar_mensaje(
                msg_id, self.usuario_actual.id_usuario, grupo.id_grupo
            )
            cargar_mensajes()

        cargar_mensajes()

        # Barra de Stickers Rápidos de Ánimo
        stickers_row = ft.Row(
            [
                _boton(
                    "👏 ¡Dale!",
                    ft.Colors.BLUE_600,
                    lambda _: enviar_sticker("👏 ¡Excelente ritmo de lectura!"),
                ),
                _boton(
                    "📚 ¡Gran libro!",
                    ft.Colors.BLUE_600,
                    lambda _: enviar_sticker("📚 ¡Excelente elección de libro!"),
                ),
                _boton(
                    "⭐ ¡Ánimo!",
                    ft.Colors.BLUE_600,
                    lambda _: enviar_sticker("⭐ ¡Sigue así, vas muy bien!"),
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
        )

        dlg_chat = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                f"💬 Chat: {grupo.nombre}",
                color=ft.Colors.BLACK,
                size=16,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Column(
                [
                    list_chat,
                    stickers_row,
                    ft.Row(
                        [
                            txt_mensaje,
                            _boton("Enviar", ft.Colors.BLUE_600, enviar_texto),
                        ]
                    ),
                ],
                tight=True,
                spacing=8,
            ),
            actions=[_boton("Volver", ft.Colors.RED_600, self._ir_a_mis_grupos)],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=ft.Colors.WHITE,
        )
        self._mostrar_dialog(dlg_chat)
