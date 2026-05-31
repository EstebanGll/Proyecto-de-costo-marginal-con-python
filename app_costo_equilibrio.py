"""
Aplicación de Escritorio - Punto de Equilibrio Económico
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
    """
        Toma la estructura de cada ejemplo y realiza los calculos para obtener el punto de equilibrio.
        Parametro:
            datos (dict[dict]) lista de costos de los insumos con una breve descripcion de cada caso
        Retorno:
        dic: diccionario con los calculos obtenidos de cada ejemplo
    """
    pv  = datos["precio_venta"]
    cvs = datos["costos_variables"] # diccionario de costos unitarios
    cfs = datos["costos_fijos"] # diccionario de costos fijos
    vp  = datos["ventas_presupuestadas"]
    ud  = datos["utilidad_deseada"]
    up  = datos["utilidad_pct_costos"]

    # costo variable unitario
    cvu          = sum(cvs.values())
    # costos fijos
    cf           = sum(cfs.values())
    # margen de contribucion unitario
    mcu          = pv - cvu
    # porcentaje de margen de contribucion unitario
    mcu_pct      = mcu / pv
    # cantidad en equilibrio
    qe           = cf / mcu
    # ventas en equilibrio
    ve           = qe * pv
    # margen de seguridad por unidades
    ms_u         = vp - qe
    # porcentaje de margen de seguridad
    ms_pct       = ms_u / vp if vp else 0
    

    # Punto de cierre (sin amortizaciones)
    def obtener_amortizacion(datos):
        for clave, valor in datos.items():
            if clave.startswith("Amortiz"):
                return valor
        return 0
    
    amort = cfs.get("Amortizaciones", obtener_amortizacion(cfs))

    punto_cierre = (cf - amort) / mcu

    # Cantidad para utilidad fija
    q_ud = (cf + ud) / mcu


    # Utilidad del n% sobre costos totales:
    # PV*Q = CT + n% CT
    # PV*Q = 1.n * (CF + CVu*Q)
    # PV*Q - 1.n*CVu*Q = 1.n*CF
    # Q = 1.n*CF / (PV - 1.n*CVu)
    
    def calcular_utilidad_porcentaje_ingresado(cfs, pv, cvu, utilidad):
        denom = (pv - (1 + utilidad/100) * cvu)
        return ((1+ utilidad/100) * cfs) / denom
    
    q_up = calcular_utilidad_porcentaje_ingresado(cf, pv, cvu, up)

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
        self.fig = Figure(figsize=(7, 4.5), facecolor="#ffffff")
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
 
    def actualizar(self, datos: dict, res: dict):
        self.fig.clear()
        ax = self.fig.add_subplot(111, facecolor="#f8f9fc")
 
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
 
        # Paleta Power BI
        C_ING  = "#118DFF"   # azul Power BI
        C_CT   = "#E6445A"   # rojo vibrante
        C_CV   = "#F2BC00"   # amarillo dorado
        C_CF   = "#8B4FD8"   # violeta medio
        C_LOSS = "#E6445A"
        C_GAIN = "#12B76A"   # verde esmeralda
 
        ax.plot(q, ingresos,       color=C_ING,  lw=2.8, label="Ingresos Totales")
        ax.plot(q, costos_totales, color=C_CT,   lw=2.8, label="Costos Totales")
        ax.plot(q, costos_var,     color=C_CV,   lw=2.0, ls="--", label="Costos Variables")
        ax.plot(q, costos_fijos_l, color=C_CF,   lw=2.0, ls=":",  label="Costos Fijos")
 
        ax.fill_between(q, ingresos, costos_totales,
                        where=(costos_totales > ingresos),
                        color=C_LOSS, alpha=0.10, label="Zona de pérdidas")
        ax.fill_between(q, ingresos, costos_totales,
                        where=(ingresos >= costos_totales),
                        color=C_GAIN, alpha=0.12, label="Zona de ganancias")
 
        ax.scatter([qe], [ve], color="#F2BC00", s=140, zorder=6,
                   edgecolors="#1a1a2e", lw=1.5)
        ax.axvline(qe, ls="--", color="#555770", lw=1, alpha=0.6)
        ax.axhline(ve, ls="--", color="#555770", lw=1, alpha=0.6)
 
        ax.annotate(
            f"  PE: {qe:.1f} {un}s\n  ${ve:,.0f}",
            xy=(qe, ve), xytext=(qe + q_max * 0.03, ve * 0.90),
            color="#1a1a2e", fontsize=9, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#dddddd", lw=1),
            arrowprops=dict(arrowstyle="->", color="#555770", lw=1.2),
        )
 
        # Ventas presupuestadas
        ax.axvline(vp, ls="-.", color="#F2BC00", lw=1.6, alpha=0.9,
                   label=f"Vtas. presup. ({vp})")
 
        ax.set_title(f"Punto de Equilibrio — {datos['descripcion']}",
                     color="#1a1a2e", fontsize=12, fontweight="bold", pad=12)
        ax.set_xlabel(f"Cantidad ({un}s)", color="#555770", fontsize=10)
        ax.set_ylabel("Pesos ($)", color="#555770", fontsize=10)
        ax.tick_params(colors="#555770", labelsize=8)
        for sp in ax.spines.values():
            sp.set_edgecolor("#e0e0e8")
 
        fmt = mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")
        ax.yaxis.set_major_formatter(fmt)
 
        ax.legend(facecolor="white", edgecolor="#e0e0e8",
                  labelcolor="#1a1a2e", fontsize=8, loc="upper left",
                  framealpha=1)
        ax.grid(color="#e8e8f0", lw=0.8, linestyle="-")
 
        self.fig.tight_layout()
        self.draw()
 
 
# =============================================================================
# VENTANA PRINCIPAL
# =============================================================================
 
STYLE = """
QMainWindow, QWidget {
    background-color: #f3f4f8;
    color: #1a1a2e;
    font-family: "Segoe UI", "Ubuntu", sans-serif;
}
 
QGroupBox {
    border: 1px solid #dde1ed;
    border-radius: 8px;
    margin-top: 14px;
    padding: 10px 8px 8px 8px;
    font-weight: bold;
    color: #7b8ab8;
    font-size: 10px;
    letter-spacing: 1px;
    background-color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    left: 10px;
}
 
QLabel {
    color: #1a1a2e;
    background-color: transparent;
}
QLabel#titulo_app {
    color: #0A0A0A;
    font-size: 18px;
    font-weight: bold;
    letter-spacing: 2px;
}

QLabel#dato_label {
    color: #6b7280;
    font-size: 11px;
}
QLabel#dato_valor {
    color: #1a1a2e;
    font-size: 12px;
    font-weight: bold;
}
QLabel#seccion {
    color: #F2BC00;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1.5px;
}
 
/* Tabla */
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f8f9fc;
    gridline-color: #eaedf5;
    border: 1px solid #dde1ed;
    border-radius: 6px;
    color: #1a1a2e;
    font-size: 11px;
}
QTableWidget::item { padding: 6px 10px; }
QTableWidget::item:selected {
    background-color: #dbeafe;
    color: #1a1a2e;
}
QHeaderView::section {
    background-color: #f3f4f8;
    color: #7b8ab8;
    border: none;
    border-bottom: 2px solid #dde1ed;
    padding: 8px 10px;
    font-weight: bold;
    font-size: 11px;
    letter-spacing: 0.5px;
}
 
/* Barra inferior de ejemplos */
QFrame#barra_ejemplos {
    background-color: #ffffff;
    border-top: 2px solid #F2BC00;
}
QPushButton#btn_ejemplo {
    background-color: #f3f4f8;
    color: #6b7280;
    border: 1px solid #dde1ed;
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.5px;
    min-width: 100px;
}
QPushButton#btn_ejemplo:hover {
    background-color: #dbeafe;
    color: #118DFF;
    border-color: #118DFF;
}
QPushButton#btn_ejemplo_activo {
    background-color: #118DFF;
    color: #ffffff;
    border: 1.5px solid #118DFF;
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.5px;
    min-width: 100px;
}
 
QScrollArea { border: none; background-color: #f3f4f8; }
QScrollBar:vertical {
    background: #f3f4f8;
    width: 6px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #c5ccde;
    border-radius: 3px;
}
QSplitter::handle { background-color: #dde1ed; }
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
        header.setStyleSheet(
            "background-color: #F29100;"
            "border-bottom: 3px solid #d4a400;"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 0, 24, 0)
 
        titulo = QLabel("⚖  ANÁLISIS DE PUNTO DE EQUILIBRIO  ·  Herramienta de costeo y decisión empresarial")
        titulo.setObjectName("titulo_app")

        hl.addWidget(titulo)
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
        contenedor.setStyleSheet("background-color:#f3f4f8;")
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
 
        # Descripción del ejemplo
        grp_desc = QGroupBox("EMPRESA / PRODUCTO")
        gl = QVBoxLayout(grp_desc)
        self.lbl_descripcion = QLabel()
        self.lbl_descripcion.setWordWrap(True)
        self.lbl_descripcion.setStyleSheet("color:#374151; font-size:12px;")
        gl.addWidget(self.lbl_descripcion)
        layout.addWidget(grp_desc)
 
        # Precio de venta
        grp_pv = QGroupBox("PRECIO DE VENTA")
        pvl = QVBoxLayout(grp_pv)
        self.lbl_pv = QLabel()
        self.lbl_pv.setObjectName("dato_valor")
        self.lbl_pv.setStyleSheet("color:#118DFF; font-size:16px; font-weight:bold;")
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
 
        # ── Resumen de cálculo ──────────────────────────────────────────
        grp_res = QGroupBox("RESUMEN DE CÁLCULO")
        resl = QGridLayout(grp_res)
        resl.setHorizontalSpacing(10)
        resl.setVerticalSpacing(6)
 
        def _fila_resumen(grid, row, etiqueta, attr_val, color_val="#e0e6f0"):
            lbl_e = QLabel(etiqueta)
            lbl_e.setObjectName("dato_label")
            lbl_v = QLabel()
            lbl_v.setObjectName("dato_valor")
            lbl_v.setAlignment(Qt.AlignRight)
            lbl_v.setStyleSheet(f"color:{color_val}; font-size:12px; font-weight:bold;")
            grid.addWidget(lbl_e, row, 0)
            grid.addWidget(lbl_v, row, 1)
            return lbl_v
 
        # Separador visual dentro del grupo
        def _sep(grid, row, texto):
            lbl = QLabel(texto)
            lbl.setStyleSheet(
                "color:#118DFF; font-size:9px; font-weight:bold; "
                "letter-spacing:1px; padding-top:6px;"
            )
            grid.addWidget(lbl, row, 0, 1, 2)
 
        _sep(resl, 0, "COSTOS")
        self.res_cvu  = _fila_resumen(resl, 1, "Costo variable unitario:",  "cvu",  "#E67E00")
        self.res_cf   = _fila_resumen(resl, 2, "Costos fijos totales:",      "cf",   "#8B4FD8")
        _sep(resl, 3, "MARGEN DE CONTRIBUCIÓN")
        self.res_mcu  = _fila_resumen(resl, 4, "Margen contribución unit.:", "mcu",  "#12B76A")
        self.res_mpct = _fila_resumen(resl, 5, "Margen contribución %:",     "mpct", "#12B76A")
 
        layout.addWidget(grp_res)
 
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
        tabla.setFixedHeight(220)
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
                color = QColor("#EFF6FF")
                item_c.setBackground(color)
                item_v.setBackground(color)
                item_c.setForeground(QColor("#118DFF"))
 
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
 
        # Resumen de cálculo (panel izquierdo)
        self.res_cvu.setText(f"${res['cvu']:,.2f}")
        self.res_cf.setText(f"${res['cf']:,.2f}")
        self.res_mcu.setText(f"${res['mcu']:,.2f}")
        self.res_mpct.setText(f"{res['mcu_pct']*100:.2f}%")
 
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
    palette.setColor(QPalette.Window,        QColor("#f3f4f8"))
    palette.setColor(QPalette.WindowText,    QColor("#1a1a2e"))
    palette.setColor(QPalette.Base,          QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#f8f9fc"))
    palette.setColor(QPalette.Text,          QColor("#1a1a2e"))
    palette.setColor(QPalette.Button,        QColor("#f3f4f8"))
    palette.setColor(QPalette.ButtonText,    QColor("#1a1a2e"))
    app.setPalette(palette)
 
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())
 
 
if __name__ == "__main__":
    main()