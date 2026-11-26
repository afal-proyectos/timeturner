"""Vista 04 - Estadísticas personales del usuario (año en curso)."""

from datetime import datetime, timezone

import flet as ft
from dominio.servicio_metricaspersonal import ServicioMetricasPersonal

from presentacion.ui_comun import (
    encabezado,
    fmt_minutos,
    tarjeta_estadistica,
)


def construir(ui) -> ft.Control:
    libros = ui.controlador.obtener_biblioteca(ui.usuario["id_usuario"])
    todas = []
    for libro in libros:
        todas.extend(ui.repo.obtener_sesiones(libro.id_libro))

    ahora = datetime.now(timezone.utc)
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
        [
            encabezado(
                f"Mis estadísticas {ahora.year}", lambda e: ui.navegar("01_inicio")
            ),
            *tarjetas,
        ],
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )
