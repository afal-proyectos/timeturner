"""Vista 03 - Estadísticas de un libro: gráfico (tiempo, página) con ajuste lineal."""

import base64
import inspect
from io import BytesIO

import flet as ft
from dominio.calcular_proyecciones import CalculadorProyecciones
from dominio.models_sesion import EstadoSesion

from presentacion.ui_comun import (
    AZUL,
    encabezado,
    fmt_minutos,
    tarjeta_estadistica,
    texto,
)


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


def construir(ui, libro) -> ft.Control:
    sesiones = [
        s
        for s in ui.repo.obtener_sesiones(libro.id_libro)
        if s.estado in (EstadoSesion.FINALIZADA, EstadoSesion.GUARDADA)
        and s.pagina_fin is not None
    ]
    pares = CalculadorProyecciones.obtener_pares_ordenados(sesiones)
    pagina_actual = max((s.pagina_fin for s in sesiones), default=0)

    # --- Gráfico principal ---
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

    # --- Métricas ---
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
    if proy["completado"]:
        fecha = "Completado"
    else:
        fecha = proy["fecha_estimada_fin"] or "—"

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
            encabezado("Estadísticas", lambda e: ui.navegar("02_biblioteca_completa")),
            texto(libro.titulo, 18, negrita=True),
            ft.Row([grafico], alignment=centro),
            nota,
            ft.Row(tarjetas[:2], alignment=centro),
            ft.Row(tarjetas[2:], alignment=centro),
        ],
        spacing=12,
    )
