"""
Aplicación de Escritorio - Punto de Equilibrio Económico
Desarrollada con PySide6 + Matplotlib
"""

import sys
import numpy as np

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QPushButton, QScrollArea, QSizePolicy,
    QGridLayout, QGroupBox, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QPalette, QIcon

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# =============================================================================
# DATOS DE EJEMPLOS
# =============================================================================

EJEMPLOS = {
    "Melbourne SA\n(Remeras)": {
        "descripcion": "Fábrica de remeras estampadas",
        "unidad": "remera",
        "precio_venta": 25000,
        "costos_variables": {
            "Tela por remera":       (350000 / 70) * 0.75,
            "Insumos estampa":       450,
            "Incentivo operarios":   300,
            "Consumo eléctrico":     50,
            "Impuestos (5% PV)":     25000 * 0.05,
        },
        "costos_fijos": {
            "Alquiler":         600000,
            "Amortizaciones":   180000,
            "Sueldos":         1800000,
        },
        "ventas_presupuestadas": 180,
        "utilidad_deseada": 700000,
        "utilidad_pct_costos": 20,
    },
    "Pan Dorado\n(Panadería)": {
        "descripcion": "Panadería artesanal - Pan de campo",
        "unidad": "pan",
        "precio_venta": 3500,
        "costos_variables": {
            "Harina y levadura":   420,
            "Sal, agua, aditivos": 80,
            "Bolsas / embalaje":   60,
            "Comisión repartidor": 175,
            "Impuestos (5% PV)":   3500 * 0.05,
        },
        "costos_fijos": {
            "Alquiler local":   120000,
            "Amortización horno": 45000,
            "Sueldos":          380000,
            "Servicios":         55000,
        },
        "ventas_presupuestadas": 900,
        "utilidad_deseada": 250000,
        "utilidad_pct_costos": 15,
    },
    "TechPrint\n(Impresiones 3D)": {
        "descripcion": "Servicio de impresión 3D por encargo",
        "unidad": "pieza",
        "precio_venta": 18000,
        "costos_variables": {
            "Filamento PLA/ABS":   1200,
            "Consumo impresora":    400,
            "Post-proceso / lija":  350,
            "Embalaje y envío":     600,
            "Impuestos (5% PV)":   18000 * 0.05,
        },
        "costos_fijos": {
            "Alquiler taller":    280000,
            "Amortiz. impresoras":150000,
            "Sueldos técnicos":   720000,
            "Internet / softw.":   48000,
        },
        "ventas_presupuestadas": 220,
        "utilidad_deseada": 400000,
        "utilidad_pct_costos": 18,
    },
}


# =============================================================================
# CÁLCULOS
# =============================================================================

def calcular_equilibrio(datos: dict) -> dict:
    pv  = datos["precio_venta"]
    cvs = datos["costos_variables"]
    cfs = datos["costos_fijos"]
    vp  = datos["ventas_presupuestadas"]
    ud  = datos["utilidad_deseada"]
    up  = datos["utilidad_pct_costos"]

    cvu          = sum(cvs.values())
    cf           = sum(cfs.values())
    mcu          = pv - cvu
    mcu_pct      = mcu / pv
    qe           = cf / mcu
    ve           = qe * pv
    ms_u         = vp - qe
    ms_pct       = ms_u / vp if vp else 0

    # Punto de cierre (sin amortizaciones)
    amort        = cfs.get("Amortizaciones", cfs.get("Amortización horno",
                   cfs.get("Amortiz. impresoras", 0)))
    punto_cierre = (cf - amort) / mcu

    # Cantidad para utilidad fija
    q_ud = (cf + ud) / mcu

    # Cantidad para utilidad % sobre costos
    # PV*Q = (1 + up/100)*(CF + CVu*Q)
    # Q*(PV - (1+up/100)*CVu) = (1+up/100)*CF
    factor = 1 + up / 100
    denom  = pv - factor * cvu
    q_up   = (factor * cf / denom) if denom != 0 else float("inf")

    return {
        "cvu":          cvu,
        "cf":           cf,
        "mcu":          mcu,
        "mcu_pct":      mcu_pct,
        "qe":           qe,
        "ve":           ve,
        "ms_u":         ms_u,
        "ms_pct":       ms_pct,
        "punto_cierre": punto_cierre,
        "q_ud":         q_ud,
        "q_up":         q_up,
    }


# =============================================================================
# WIDGET DEL GRÁFICO
# =============================================================================

class GraficoCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(7, 4.5), facecolor="#1a1d2e")
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def actualizar(self, datos: dict, res: dict):
        self.fig.clear()
        ax = self.fig.add_subplot(111, facecolor="#12152a")

        pv  = datos["precio_venta"]
        vp  = datos["ventas_presupuestadas"]
        qe  = res["qe"]
        ve  = res["ve"]
        cf  = res["cf"]
        cvu = res["cvu"]
        un  = datos["unidad"]

        q_max = max(vp * 1.25, qe * 1.4, 50)
        q = np.linspace(0, q_max, 400)

        ingresos       = pv  * q
        costos_totales = cf  + cvu * q
        costos_var     = cvu * q
        costos_fijos_l = np.full_like(q, cf)

        # Colores
        C_ING  = "#4fc3f7"
        C_CT   = "#ef5350"
        C_CV   = "#ffa726"
        C_CF   = "#ab47bc"
        C_LOSS = "#ef5350"
        C_GAIN = "#66bb6a"

        ax.plot(q, ingresos,       color=C_ING,  lw=2.5, label="Ingresos Totales")
        ax.plot(q, costos_totales, color=C_CT,   lw=2.5, label="Costos Totales")
        ax.plot(q, costos_var,     color=C_CV,   lw=1.8, ls="--", label="Costos Variables")
        ax.plot(q, costos_fijos_l, color=C_CF,   lw=1.8, ls=":",  label="Costos Fijos")

        ax.fill_between(q, ingresos, costos_totales,
                        where=(costos_totales > ingresos),
                        color=C_LOSS, alpha=0.18, label="Zona de pérdidas")
        ax.fill_between(q, ingresos, costos_totales,
                        where=(ingresos >= costos_totales),
                        color=C_GAIN, alpha=0.18, label="Zona de ganancias")

        ax.scatter([qe], [ve], color="white", s=120, zorder=6, edgecolors=C_ING, lw=2)
        ax.axvline(qe, ls="--", color="white", lw=1, alpha=0.5)
        ax.axhline(ve, ls="--", color="white", lw=1, alpha=0.5)

        ax.annotate(
            f"  PE: {qe:.1f} {un}s\n  ${ve:,.0f}",
            xy=(qe, ve), xytext=(qe + q_max * 0.03, ve * 0.92),
            color="white", fontsize=9,
            arrowprops=dict(arrowstyle="->", color="white", lw=1),
        )

        # Ventas presupuestadas
        ax.axvline(vp, ls="-.", color="#ffd54f", lw=1.2, alpha=0.7, label=f"Vtas. presup. ({vp})")

        ax.set_title(f"Punto de Equilibrio — {datos['descripcion']}",
                     color="white", fontsize=12, pad=10)
        ax.set_xlabel(f"Cantidad ({un}s)", color="#aab4c8", fontsize=10)
        ax.set_ylabel("Pesos ($)", color="#aab4c8", fontsize=10)
        ax.tick_params(colors="#aab4c8", labelsize=8)
        for sp in ax.spines.values():
            sp.set_edgecolor("#2a2d42")

        fmt = mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")
        ax.yaxis.set_major_formatter(fmt)

        ax.legend(facecolor="#1a1d2e", edgecolor="#3a3d52",
                  labelcolor="white", fontsize=8, loc="upper left")
        ax.grid(color="#2a2d42", lw=0.7)

        self.fig.tight_layout()
        self.draw()


# =============================================================================
# VENTANA PRINCIPAL
# =============================================================================

STYLE = """
QMainWindow, QWidget {
    background-color: #12152a;
    color: #e0e6f0;
    font-family: "Segoe UI", "Ubuntu", sans-serif;
}

QGroupBox {
    border: 1px solid #2a2d42;
    border-radius: 8px;
    margin-top: 14px;
    padding: 10px 8px 8px 8px;
    font-weight: bold;
    color: #7b93c8;
    font-size: 11px;
    letter-spacing: 1px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    left: 10px;
}

QLabel {
    color: #c8d4ec;
}
QLabel#titulo_app {
    color: #4fc3f7;
    font-size: 20px;
    font-weight: bold;
    letter-spacing: 2px;
}
QLabel#subtitulo {
    color: #7b93c8;
    font-size: 11px;
}
QLabel#dato_label {
    color: #7b93c8;
    font-size: 11px;
}
QLabel#dato_valor {
    color: #e0e6f0;
    font-size: 12px;
    font-weight: bold;
}
QLabel#seccion {
    color: #4fc3f7;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1.5px;
}

/* Tabla */
QTableWidget {
    background-color: #1a1d2e;
    alternate-background-color: #1e2238;
    gridline-color: #2a2d42;
    border: none;
    border-radius: 6px;
    color: #e0e6f0;
    font-size: 11px;
}
QTableWidget::item { padding: 6px 10px; }
QTableWidget::item:selected {
    background-color: #2a3d6e;
    color: white;
}
QHeaderView::section {
    background-color: #1a1d2e;
    color: #7b93c8;
    border: none;
    border-bottom: 1px solid #2a2d42;
    padding: 8px 10px;
    font-weight: bold;
    font-size: 11px;
    letter-spacing: 0.5px;
}

/* Barra inferior de ejemplos */
QFrame#barra_ejemplos {
    background-color: #0d0f1f;
    border-top: 1px solid #2a2d42;
}
QPushButton#btn_ejemplo {
    background-color: #1a1d2e;
    color: #7b93c8;
    border: 1px solid #2a2d42;
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.5px;
    min-width: 100px;
}
QPushButton#btn_ejemplo:hover {
    background-color: #2a3050;
    color: #4fc3f7;
    border-color: #4fc3f7;
}
QPushButton#btn_ejemplo_activo {
    background-color: #1d3a6e;
    color: #4fc3f7;
    border: 1.5px solid #4fc3f7;
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.5px;
    min-width: 100px;
}

QScrollArea { border: none; }
QScrollBar:vertical {
    background: #1a1d2e;
    width: 6px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #2a3d6e;
    border-radius: 3px;
}
QSplitter::handle { background-color: #2a2d42; }
"""


def hacer_label(texto, obj_name=""):
    lbl = QLabel(texto)
    if obj_name:
        lbl.setObjectName(obj_name)
    return lbl


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Punto de Equilibrio Económico")
        self.setMinimumSize(1100, 680)
        self.resize(1280, 760)
        self.setStyleSheet(STYLE)

        self.ejemplo_actual = list(EJEMPLOS.keys())[0]
        self.botones_ejemplo = {}

        self._construir_ui()
        self._cargar_ejemplo(self.ejemplo_actual)

    # ------------------------------------------------------------------
    def _construir_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ---- Header ----
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet("background-color:#0d0f1f; border-bottom:1px solid #2a2d42;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 0, 24, 0)

        titulo = QLabel("⚖  ANÁLISIS DE PUNTO DE EQUILIBRIO")
        titulo.setObjectName("titulo_app")
        sub = QLabel("Herramienta de costeo y decisión empresarial")
        sub.setObjectName("subtitulo")
        sub.setAlignment(Qt.AlignBottom)

        hl.addWidget(titulo)
        hl.addSpacing(20)
        hl.addWidget(sub)
        hl.addStretch()

        root_layout.addWidget(header)

        # ---- Cuerpo principal ----
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)

        # Panel izquierdo: datos
        self.panel_datos = self._crear_panel_datos()
        splitter.addWidget(self.panel_datos)

        # Panel derecho: resultados + gráfico
        panel_der = QWidget()
        pd_layout = QVBoxLayout(panel_der)
        pd_layout.setContentsMargins(12, 12, 16, 12)
        pd_layout.setSpacing(10)

        self.tabla_resultados = self._crear_tabla()
        pd_layout.addWidget(self.tabla_resultados, stretch=0)

        self.canvas = GraficoCanvas()
        pd_layout.addWidget(self.canvas, stretch=1)

        splitter.addWidget(panel_der)
        splitter.setSizes([340, 780])

        root_layout.addWidget(splitter, stretch=1)

        # ---- Barra inferior de ejemplos ----
        barra = QFrame()
        barra.setObjectName("barra_ejemplos")
        barra.setFixedHeight(80)
        bl = QHBoxLayout(barra)
        bl.setContentsMargins(20, 10, 20, 10)
        bl.setSpacing(12)

        etiqueta = QLabel("EJEMPLOS:")
        etiqueta.setObjectName("seccion")
        etiqueta.setAlignment(Qt.AlignVCenter)
        bl.addWidget(etiqueta)

        for nombre in EJEMPLOS:
            btn = QPushButton(nombre)
            btn.setObjectName("btn_ejemplo")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, n=nombre: self._cargar_ejemplo(n))
            bl.addWidget(btn)
            self.botones_ejemplo[nombre] = btn

        bl.addStretch()
        root_layout.addWidget(barra)

    # ------------------------------------------------------------------
    def _crear_panel_datos(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(330)

        contenedor = QWidget()
        contenedor.setStyleSheet("background-color:#12152a;")
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Descripción del ejemplo
        grp_desc = QGroupBox("EMPRESA / PRODUCTO")
        gl = QVBoxLayout(grp_desc)
        self.lbl_descripcion = QLabel()
        self.lbl_descripcion.setWordWrap(True)
        self.lbl_descripcion.setStyleSheet("color:#c8d4ec; font-size:12px;")
        gl.addWidget(self.lbl_descripcion)
        layout.addWidget(grp_desc)

        # Precio de venta
        grp_pv = QGroupBox("PRECIO DE VENTA")
        pvl = QVBoxLayout(grp_pv)
        self.lbl_pv = QLabel()
        self.lbl_pv.setObjectName("dato_valor")
        self.lbl_pv.setStyleSheet("color:#4fc3f7; font-size:16px; font-weight:bold;")
        pvl.addWidget(self.lbl_pv)
        layout.addWidget(grp_pv)

        # Costos variables
        grp_cv = QGroupBox("COSTOS VARIABLES UNITARIOS")
        self.cv_layout = QGridLayout(grp_cv)
        self.cv_layout.setHorizontalSpacing(10)
        self.cv_layout.setVerticalSpacing(4)
        layout.addWidget(grp_cv)

        # Costos fijos
        grp_cf = QGroupBox("COSTOS FIJOS")
        self.cf_layout = QGridLayout(grp_cf)
        self.cf_layout.setHorizontalSpacing(10)
        self.cf_layout.setVerticalSpacing(4)
        layout.addWidget(grp_cf)

        # Parámetros adicionales
        grp_par = QGroupBox("PARÁMETROS")
        parl = QGridLayout(grp_par)
        parl.setHorizontalSpacing(10)
        parl.setVerticalSpacing(4)

        self.lbl_vp_l  = QLabel("Ventas presupuestadas:")
        self.lbl_vp_v  = QLabel()
        self.lbl_ud_l  = QLabel("Utilidad deseada:")
        self.lbl_ud_v  = QLabel()
        self.lbl_up_l  = QLabel("Utilidad % sobre costos:")
        self.lbl_up_v  = QLabel()

        for lbl in (self.lbl_vp_l, self.lbl_ud_l, self.lbl_up_l):
            lbl.setObjectName("dato_label")
        for lbl in (self.lbl_vp_v, self.lbl_ud_v, self.lbl_up_v):
            lbl.setObjectName("dato_valor")

        parl.addWidget(self.lbl_vp_l, 0, 0)
        parl.addWidget(self.lbl_vp_v, 0, 1)
        parl.addWidget(self.lbl_ud_l, 1, 0)
        parl.addWidget(self.lbl_ud_v, 1, 1)
        parl.addWidget(self.lbl_up_l, 2, 0)
        parl.addWidget(self.lbl_up_v, 2, 1)
        layout.addWidget(grp_par)

        layout.addStretch()
        scroll.setWidget(contenedor)
        return scroll

    # ------------------------------------------------------------------
    def _crear_tabla(self) -> QTableWidget:
        tabla = QTableWidget()
        tabla.setColumnCount(2)
        tabla.setHorizontalHeaderLabels(["Concepto", "Valor"])
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        tabla.verticalHeader().setVisible(False)
        tabla.setAlternatingRowColors(True)
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        tabla.setSelectionBehavior(QTableWidget.SelectRows)
        tabla.setFixedHeight(280)
        return tabla

    # ------------------------------------------------------------------
    def _limpiar_grid(self, grid: QGridLayout):
        while grid.count():
            item = grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    # ------------------------------------------------------------------
    def _poblar_grid(self, grid: QGridLayout, items: dict):
        self._limpiar_grid(grid)
        for fila, (concepto, valor) in enumerate(items.items()):
            lbl_c = QLabel(concepto)
            lbl_c.setObjectName("dato_label")
            lbl_v = QLabel(f"${valor:,.2f}")
            lbl_v.setObjectName("dato_valor")
            lbl_v.setAlignment(Qt.AlignRight)
            grid.addWidget(lbl_c, fila, 0)
            grid.addWidget(lbl_v, fila, 1)

    # ------------------------------------------------------------------
    def _poblar_tabla(self, datos: dict, res: dict):
        un = datos["unidad"]
        up = datos["utilidad_pct_costos"]
        ud = datos["utilidad_deseada"]

        filas = [
            ("Costo variable unitario",                         f"${res['cvu']:,.2f}",     False),
            ("Costos fijos totales",                            f"${res['cf']:,.2f}",      False),
            ("Margen de contribución unitario",                 f"${res['mcu']:,.2f}",     False),
            ("Margen de contribución %",                        f"{res['mcu_pct']*100:.2f}%", False),
            ("── PUNTO DE EQUILIBRIO ──",                       "",                        True),
            (f"Cantidad ({un}s)",                               f"{res['qe']:.2f}",        False),
            ("Ventas ($)",                                      f"${res['ve']:,.2f}",      False),
            ("── MARGEN DE SEGURIDAD ──",                       "",                        True),
            (f"Margen de seguridad ({un}s)",                    f"{res['ms_u']:.2f}",      False),
            ("Margen de seguridad %",                           f"{res['ms_pct']*100:.2f}%", False),
            ("── OTROS INDICADORES ──",                         "",                        True),
            (f"Punto de cierre ({un}s)",                        f"{res['punto_cierre']:.2f}", False),
            (f"{un.capitalize()}s para utilidad de ${ud:,.0f}", f"{res['q_ud']:.2f}",     False),
            (f"{un.capitalize()}s para utilidad {up}% sobre CT",f"{res['q_up']:.2f}",     False),
        ]

        self.tabla_resultados.setRowCount(len(filas))
        for row, (concepto, valor, es_header) in enumerate(filas):
            item_c = QTableWidgetItem(concepto)
            item_v = QTableWidgetItem(valor)
            item_v.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            if es_header:
                font = QFont()
                font.setBold(True)
                item_c.setFont(font)
                item_v.setFont(font)
                color = QColor("#1d2845")
                item_c.setBackground(color)
                item_v.setBackground(color)
                item_c.setForeground(QColor("#4fc3f7"))

            self.tabla_resultados.setItem(row, 0, item_c)
            self.tabla_resultados.setItem(row, 1, item_v)

        self.tabla_resultados.resizeRowsToContents()

    # ------------------------------------------------------------------
    def _actualizar_botones(self, activo: str):
        for nombre, btn in self.botones_ejemplo.items():
            if nombre == activo:
                btn.setObjectName("btn_ejemplo_activo")
            else:
                btn.setObjectName("btn_ejemplo")
            btn.setStyle(btn.style())   # fuerza recarga de estilo

    # ------------------------------------------------------------------
    def _cargar_ejemplo(self, nombre: str):
        self.ejemplo_actual = nombre
        datos = EJEMPLOS[nombre]
        res   = calcular_equilibrio(datos)
        un    = datos["unidad"]

        # Panel de datos
        self.lbl_descripcion.setText(datos["descripcion"])
        self.lbl_pv.setText(f"${datos['precio_venta']:,.2f} / {un}")
        self._poblar_grid(self.cv_layout, datos["costos_variables"])
        self._poblar_grid(self.cf_layout, datos["costos_fijos"])
        self.lbl_vp_v.setText(f"{datos['ventas_presupuestadas']} {un}s")
        self.lbl_ud_v.setText(f"${datos['utilidad_deseada']:,.0f}")
        self.lbl_up_v.setText(f"{datos['utilidad_pct_costos']}%")

        # Tabla y gráfico
        self._poblar_tabla(datos, res)
        self.canvas.actualizar(datos, res)

        # Botones
        self._actualizar_botones(nombre)

        # Título de ventana
        self.setWindowTitle(f"Punto de Equilibrio — {datos['descripcion']}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Paleta oscura base para que los diálogos del sistema respeten el tema
    palette = QPalette()
    palette.setColor(QPalette.Window,        QColor("#12152a"))
    palette.setColor(QPalette.WindowText,    QColor("#e0e6f0"))
    palette.setColor(QPalette.Base,          QColor("#1a1d2e"))
    palette.setColor(QPalette.AlternateBase, QColor("#1e2238"))
    palette.setColor(QPalette.Text,          QColor("#e0e6f0"))
    palette.setColor(QPalette.Button,        QColor("#1a1d2e"))
    palette.setColor(QPalette.ButtonText,    QColor("#e0e6f0"))
    app.setPalette(palette)

    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()