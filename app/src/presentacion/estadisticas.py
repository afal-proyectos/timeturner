"""
Contenido de las vistas de estadísticas, reutilizable para el usuario y sus amigos.

  * contenido_estadistica_libro   -> vistas 03 (propia) y 08 (libro de un amigo)
  * contenido_estadistica_usuario -> vistas 04 (propia) y 07 (amigo)
"""

import base64
import inspect
from datetime import UTC, datetime
from io import BytesIO

import flet as ft
from dominio.calcular_proyecciones import CalculadorProyecciones
from dominio.models_sesion import EstadoSesion
from dominio.servicio_metricaspersonal import ServicioMetricasPersonal

from presentacion.ui_comun import (
    AZUL,
    encabezado,
    fmt_minutos,
    tarjeta_estadistica,
    texto,
)


# --------------------------------------------------------------------------
# Libro
# --------------------------------------------------------------------------
def _ajuste_lineal(pares):
    """Mínimos cuadrados y = m*x + b. Devuelve None si no hay suficientes datos."""
    n = len(pares)
    if n < 2:
        return None
    xs = [p[0] for p in pares]
    ys = [p[1] for p in pares]
    mx, my = sum(xs) / n, sum(ys) / n
    var = sum((x - mx) ** 2 for x in xs)
    if var == 0:
        return None
    m = sum((x - mx) * (y - my) for x, y in pares) / var
    return m, my - m * mx


def _grafico_base64(pares) -> str:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4), dpi=110)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    xs = [p[0] for p in pares]
    ys = [p[1] for p in pares]
    ax.scatter(xs, ys, color=AZUL, zorder=3, label="Sesiones")

    ajuste = _ajuste_lineal(pares)
    if ajuste:
        m, b = ajuste
        x0, x1 = 0, max(xs)
        ax.plot(
            [x0, x1],
            [m * x0 + b, m * x1 + b],
            color="black",
            linewidth=1.5,
            label="Ajuste lineal",
        )

    ax.set_xlabel("Tiempo acumulado (min)", color="black")
    ax.set_ylabel("Página", color="black")
    ax.tick_params(colors="black")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _imagen(png_b64: str) -> ft.Image:
    # Flet 1.x acepta base64 en `src`; versiones previas usan `src_base64`.
    if "src_base64" in inspect.signature(ft.Image.__init__).parameters:
        return ft.Image(src_base64=png_b64, width=400, height=270)
    return ft.Image(src=png_b64, width=400, height=270)


def contenido_estadistica_libro(
    ui, libro, on_volver, subtitulo: str = ""
) -> ft.Control:
    sesiones = [
        s
        for s in ui.repo.obtener_sesiones(libro.id_libro)
        if s.estado in (EstadoSesion.FINALIZADA, EstadoSesion.GUARDADA)
        and s.pagina_fin is not None
    ]
    pares = CalculadorProyecciones.obtener_pares_ordenados(sesiones)
    pagina_actual = max((s.pagina_fin for s in sesiones), default=0)

    if pares:
        try:
            grafico = _imagen(_grafico_base64(pares))
        except ImportError:
            grafico = texto("Falta matplotlib: pip install matplotlib")
        nota = (
            texto("El ajuste lineal necesita al menos 2 sesiones.", 12)
            if len(pares) < 2
            else ft.Container()
        )
    else:
        grafico = texto("Aún no hay sesiones registradas para este libro.")
        nota = ft.Container()

    n = len(sesiones)
    total_pag = sum(s.calcular_paginas_leidas() for s in sesiones)
    total_min = sum(s.calcular_minutos_netos() for s in sesiones)
    ppm = round(total_pag / total_min, 2) if total_min > 0 else 0.0
    prom_pag = round(total_pag / n, 1) if n else 0
    prom_min = total_min / n if n else 0.0
    pct = libro.calcular_porcentaje_avance(pagina_actual)

    proy = CalculadorProyecciones.estimar_tiempo_restante(
        libro, sesiones, pagina_actual
    )
    fecha = "Completado" if proy["completado"] else (proy["fecha_estimada_fin"] or "—")

    tarjetas = [
        tarjeta_estadistica(
            "Hojas leídas", f"{pct}%", f"Pág. {pagina_actual} de {libro.total_paginas}"
        ),
        tarjeta_estadistica(
            "Velocidad lectora", f"{ppm} pág/min", "Páginas leídas / tiempo total"
        ),
        tarjeta_estadistica(
            "Promedio por sesión",
            f"{prom_pag} págs",
            f"{fmt_minutos(prom_min)} por sesión",
        ),
        tarjeta_estadistica("Fecha estimada de término", fecha),
    ]

    centro = ft.MainAxisAlignment.CENTER
    return ft.Column(
        [
            encabezado("Estadísticas", on_volver),
            texto(libro.titulo, 18, negrita=True),
            texto(subtitulo, 12) if subtitulo else ft.Container(),
            ft.Row([grafico], alignment=centro),
            nota,
            ft.Row(tarjetas[:2], alignment=centro),
            ft.Row(tarjetas[2:], alignment=centro),
        ],
        spacing=12,
    )


# --------------------------------------------------------------------------
# Usuario
# --------------------------------------------------------------------------
def contenido_estadistica_usuario(
    ui, usuario_id: str, titulo: str, on_volver
) -> ft.Control:
    libros = ui.controlador.obtener_biblioteca(usuario_id)
    todas = []
    for libro in libros:
        todas.extend(ui.repo.obtener_sesiones(libro.id_libro))

    ahora = datetime.now(UTC)
    acum = ServicioMetricasPersonal.calcular_acumulado_anual(todas, libros, ahora.year)

    sesiones_anio = [
        s for s in todas if s.inicio_utc and s.inicio_utc.year == ahora.year
    ]
    n = acum["total_sesiones_anual"]
    minutos = sum(s.calcular_minutos_netos() for s in sesiones_anio)
    paginas = sum(s.calcular_paginas_leidas() for s in sesiones_anio)

    prom_mes = round(n / ahora.month, 1)  # sesiones / meses transcurridos del año
    prom_duracion = minutos / n if n else 0.0
    ppm = round(paginas / minutos, 2) if minutos > 0 else 0.0

    tarjetas = [
        tarjeta_estadistica("Total de sesiones del año", str(n), cuadrada=False),
        tarjeta_estadistica(
            "Promedio de sesiones al mes", str(prom_mes), cuadrada=False
        ),
        tarjeta_estadistica(
            "Tiempo de lectura acumulado anual",
            f"{acum['horas_leidas_anual']} h",
            cuadrada=False,
        ),
        tarjeta_estadistica(
            "Duración promedio de sesión", fmt_minutos(prom_duracion), cuadrada=False
        ),
        tarjeta_estadistica(
            "Libros completados al 100%",
            str(acum["libros_terminados_anual"]),
            cuadrada=False,
        ),
        tarjeta_estadistica(
            "Velocidad de lectura promedio", f"{ppm} pág/min", cuadrada=False
        ),
    ]

    return ft.Column(
        [encabezado(titulo, on_volver), *tarjetas],
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )
