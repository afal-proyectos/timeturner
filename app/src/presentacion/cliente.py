from dominio.calcular_proyecciones import CalculadorProyecciones
from dominio.controlador_lectura import ControladorLectura
from dominio.models_sesion import EstadoSesion
from dominio.servicio_autenticacion import ServicioAutenticacion

# from dominio.servicio_metricaslibro import ServicioMetricasLibro
from dominio.servicio_metricaspersonal import ServicioMetricasPersonal


class CLI:
    """Interfaz de consola interactiva para validar la lógica del Sprint 1."""

    def __init__(self, controlador: ControladorLectura, usuario_id_defecto: str):
        self.controlador = controlador
        self.usuario_id = usuario_id_defecto

    def iniciar(self) -> None:
        """Flujo Principal: primer Login/Registro, luego menú de biblioteca"""
        if not self._menu_autenticacion():
            return

        """una vez verificado, se ingresa al menú principal usando self.usuario_actual.id_usuario"""
        while True:
            self._mostrar_menu_principal()
            opcion = input("Selecciona una opción (0-5): ").strip()

            if opcion == "1":
                self._opcion_registrar_libro()
            elif opcion == "2":
                self._opcion_ver_biblioteca()
            elif opcion == "3":
                self._opcion_iniciar_sesion_lectura()
            elif opcion == "4":
                self._opcion_consultar_metricas_libro()
            elif opcion == "5":
                self._opcion_ver_acumulado_anual()
            elif opcion == "0":
                print("\n¡Gracias por usar LeerJuntos! Hasta la próxima.\n")
                break
            else:
                print("\n⚠️ Opción no válida. Por favor, intenta de nuevo.\n")

    def _mostrar_menu_principal(self) -> None:
        print("\n" + "=" * 50)
        print("          📚 LEERJUNTOS - MODULO CONSOLA (MVP)      ")
        print("=" * 50)
        print("1. Registrar un nuevo libro")
        print("2. Ver mi biblioteca de libros")
        print("3. Iniciar sesión de lectura (Cronómetro)")
        print("4. Consultar métricas y proyecciones de un libro")
        print("5. Ver acumulado anual de lectura")
        print("0. Salir")
        print("=" * 50)

    # --- Opciones del Menú ---

    def _opcion_registrar_libro(self) -> None:
        print("\n--- 📖 Registrar Nuevo Libro ---")
        titulo = input("Título del libro: ").strip()
        autor = input("Autor: ").strip()
        genero = input("Género literario: ").strip()

        try:
            total_paginas = int(input("Total de páginas: "))
            libro = self.controlador.registrar_libro(
                usuario_id=self.usuario_id,
                titulo=titulo,
                autor=autor,
                genero=genero,
                total_paginas=total_paginas,
            )
            print(
                f"\n✅ ¡Libro '{libro.titulo}' registrado exitosamente con ID: {libro.id_libro}!"
            )
        except ValueError as e:
            print(f"\n❌ Error al registrar libro: {e}")

    def _opcion_ver_biblioteca(self) -> None:
        print("\n--- 📚 Mi Biblioteca ---")
        libros = self.controlador.obtener_biblioteca(self.usuario_id)

        if not libros:
            print("Tu biblioteca está vacía. ¡Registra tu primer libro!")
            return

        for i, libro in enumerate(libros, 1):
            sesiones = self.controlador.repo.obtener_sesiones(libro.id_libro)
            pagina_actual = 0
            if sesiones:
                paginas_validas = [
                    s.pagina_fin for s in sesiones if s.pagina_fin is not None
                ]
                if paginas_validas:
                    pagina_actual = max(paginas_validas)

            avance_pct = libro.calcular_porcentaje_avance(pagina_actual)
            print(
                f"{i}. [{libro.id_libro[:8]}] '{libro.titulo}' de {libro.autor} "
                f"({libro.total_paginas} págs) - Avance: {avance_pct}% (Pág {pagina_actual})"
            )

    def _opcion_iniciar_sesion_lectura(self) -> None:
        print("\n--- ⏱️ Sesión de Lectura ---")
        libros = self.controlador.obtener_biblioteca(self.usuario_id)

        if not libros:
            print("No tienes libros registrados para leer.")
            return

        self._opcion_ver_biblioteca()
        try:
            idx = int(input("\nSelecciona el número del libro que vas a leer: ")) - 1
            if idx < 0 or idx >= len(libros):
                print("❌ Selección fuera de rango.")
                return
            libro_sel = libros[idx]
        except ValueError:
            print("❌ Entrada no válida.")
            return

        # Determinar última página leída como sugerencia inicial
        sesiones_previas = self.controlador.repo.obtener_sesiones(libro_sel.id_libro)
        pagina_sugerida = 0
        if sesiones_previas:
            paginas_fin = [
                s.pagina_fin for s in sesiones_previas if s.pagina_fin is not None
            ]
            if paginas_fin:
                pagina_sugerida = max(paginas_fin)

        try:
            pagina_inicio = int(
                input(f"Página inicial de lectura [{pagina_sugerida}]: ")
                or pagina_sugerida
            )
            if pagina_inicio > libro_sel.total_paginas:
                print("❌ La página inicial no puede superar el total de páginas.")
                return
        except ValueError:
            print("❌ Número de página no válido.")
            return

        # Iniciar entidad SesionLectura
        sesion = self.controlador.iniciar_sesion_lectura(
            libro_id=libro_sel.id_libro,
            usuario_id=self.usuario_id,
            pagina_inicio=pagina_inicio,
        )

        print(
            f"\n🟢 Sesión iniciada para '{libro_sel.titulo}' a las "
            f"{sesion.inicio_utc.strftime('%H:%M:%S UTC')}."
        )

        # Control del cronómetro interactivo
        self._gestionar_cronometro_interactivo(sesion, libro_sel)

    def _gestionar_cronometro_interactivo(self, sesion, libro_sel) -> None:
        """Maneja el menú de pausa, reanudación y cierre de sesión de lectura."""
        while sesion.estado in (EstadoSesion.LEYENDO, EstadoSesion.PAUSADA):
            estado_lbl = (
                "LEYENDO 📖" if sesion.estado == EstadoSesion.LEYENDO else "PAUSADA ⏸️"
            )
            print(f"\nEstado actual del Cronómetro: [{estado_lbl}]")
            print(
                "1. Pausar lectura"
                if sesion.estado == EstadoSesion.LEYENDO
                else "1. Reanudar lectura"
            )
            print("2. Detener y finalizar lectura")
            print("3. Cancelar sesión (descartar)")

            sub_op = input("Opción: ").strip()

            if sub_op == "1":
                if sesion.estado == EstadoSesion.LEYENDO:
                    sesion.pausar()
                    print(
                        "⏸️ Lectura pausada. El tiempo en pausa no afectará tu velocidad real."
                    )
                else:
                    sesion.reanudar()
                    print("▶️ Lectura reanudada. ¡Sigue así!")

            elif sub_op == "2":
                try:
                    pagina_fin = int(
                        input(
                            f"\nIngresa la página final alcanzada (Total: {libro_sel.total_paginas}): "
                        )
                    )
                    resultado = self.controlador.finalizar_y_guardar_sesion(
                        sesion, pagina_fin
                    )
                    self._mostrar_resumen_sesion_finalizada(resultado, libro_sel)
                    break
                except ValueError as e:
                    print(f"❌ Error al guardar sesión: {e}")

            elif sub_op == "3":
                print("❌ Sesión cancelada. No se guardaron registros.")
                break

    def _mostrar_resumen_sesion_finalizada(self, resultado: dict, libro) -> None:
        met = resultado["metricas_sesion"]
        proy = resultado["proyeccion"]

        print("\n" + "🎉 " * 10)
        print("        ¡SESION FINALIZADA Y GUARDADA!        ")
        print("🎉 " * 10)
        print(f"⏱️ Tiempo neto leído: {met['minutos_netos']} minutos")
        print(f"📄 Páginas leídas: {met['paginas_leidas']}")
        print(f"⚡ Velocidad: {met['velocidad_ppm']} páginas/minuto (PPM)")
        print(f"📈 Avance del libro: {met['porcentaje_avance_libro']}%")

        if not proy["completado"] and proy["minutos_estimados_restantes"]:
            print(
                f"\n🔮 PROYECCIÓN: Te quedan aprox. {proy['horas_estimadas_restantes']} horas de lectura."
            )
            print(f"📅 Fecha estimada de finalización: {proy['fecha_estimada_fin']}")
        elif proy["completado"]:
            print("\n🏆 ¡FELICIDADES! ¡Has completado este libro! 🏆")

    def _opcion_consultar_metricas_libro(self) -> None:
        print("\n--- 📊 Métricas y Proyecciones por Libro ---")
        libros = self.controlador.obtener_biblioteca(self.usuario_id)

        if not libros:
            print("No tienes libros registrados.")
            return

        self._opcion_ver_biblioteca()
        try:
            idx = int(input("\nSelecciona el número del libro: ")) - 1
            if idx < 0 or idx >= len(libros):
                print("❌ Selección fuera de rango.")
                return
            libro_sel = libros[idx]
        except ValueError:
            print("❌ Entrada no válida.")
            return

        sesiones = self.controlador.repo.obtener_sesiones(libro_sel.id_libro)
        pares = CalculadorProyecciones.obtener_pares_ordenados(sesiones)

        print(f"\n📊 Análises de '{libro_sel.titulo}':")
        print(f"• Total de sesiones registradas: {len(sesiones)}")
        print(f"• Pares Ordenados (Tiempo Acumulado Min, Página): {pares}")

        pagina_actual = pares[-1][1] if pares else 0
        proyeccion = CalculadorProyecciones.estimar_tiempo_restante(
            libro_sel, sesiones, pagina_actual
        )

        if proyeccion["minutos_estimados_restantes"]:
            print(
                f"• Tiempo estimado restante: {proyeccion['horas_estimadas_restantes']} hrs "
                f"({proyeccion['minutos_estimados_restantes']} min)"
            )
            print(f"• Fecha proyectada de término: {proyeccion['fecha_estimada_fin']}")

    def _opcion_ver_acumulado_anual(self) -> None:
        print("\n--- 📅 Métricas Acumuladas Anuales ---")
        libros = self.controlador.obtener_biblioteca(self.usuario_id)

        todas_sesiones = []
        for libro in libros:
            todas_sesiones.extend(
                self.controlador.repo.obtener_sesiones(libro.id_libro)
            )

        acum = ServicioMetricasPersonal.calcular_acumulado_anual(todas_sesiones, libros)

        print(f"\n🏆 Resumen del Año {acum['anio']}:")
        print(f"• Horas totales leídas: {acum['horas_leidas_anual']} hrs")
        print(f"• Libros completados al 100%: {acum['libros_terminados_anual']}")
        print(f"• Total de sesiones de lectura: {acum['total_sesiones_anual']}")

    def _menu_autenticacion(self) -> bool:
        while True:
            while True:
                print("\n" + "=" * 50)
                print("        📚 LEERJUNTOS - INICIO DE SESION          ")
                print("=" * 50)
                print("1. Iniciar Sesión (Alias y Contraseña)")
                print("2. Crear nueva cuenta")
                print("0. Salir")
                print("=" * 50)

                op = input("Selecciona una opción: ").strip()

                if op == "1":
                    apodo = input("Alias (máx 8 caracteres): ").strip()
                    password = input("Contraseña: ").strip()
                    self.servicio_auth = ServicioAutenticacion(self.controlador.repo)
                    exito, mensaje, usuario = self.servicio_auth.iniciar_sesion(
                        apodo, password
                    )
                    print(f"\n{mensaje}")
                    if exito and usuario:
                        self.usuario_id = usuario.id_usuario
                        self.usuario_actual = usuario
                        return True

                elif op == "2":
                    print("\n--- 📝 Registro de Nuevo Lector ---")
                    email = input("Correo electrónico: ").strip()
                    apodo = input("Alias (máx 8 caracteres): ").strip()
                    password = input("Contraseña (4 a 8 caracteres): ").strip()
                    self.servicio_auth = ServicioAutenticacion(self.controlador.repo)
                    exito, mensaje, usuario = self.servicio_auth.registrar_usuario(
                        email, apodo, password
                    )
                    print(f"\n{mensaje}")
                    if exito and usuario:
                        self.usuario_id = usuario.id_usuario
                        self.usuario_actual = usuario
                        return True

                elif op == "0":
                    return False
