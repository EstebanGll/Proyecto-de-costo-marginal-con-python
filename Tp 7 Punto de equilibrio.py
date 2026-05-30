import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# DATOS DEL TP
# =========================

precio_venta = 25000

costo_rollo = 350000
metros_por_rollo = 70
consumo_tela_por_remera = 0.75

insumos_estampa = 450
incentivo_operarios = 300
consumo_electrico = 50
impuestos_pct = 0.05

alquiler = 600000
amortizaciones = 180000
sueldos = 1800000

ventas_presupuestadas = 180
utilidad_deseada = 700000

# =========================
# CÁLCULOS
# =========================

costo_tela_por_metro = costo_rollo / metros_por_rollo
costo_tela_por_remera = costo_tela_por_metro * consumo_tela_por_remera

impuestos_por_remera = precio_venta * impuestos_pct

lista_costo_variable_unitario = [ costo_tela_por_remera, insumos_estampa, incentivo_operarios, consumo_electrico, impuestos_por_remera]
def costos_variables_unitarios(lista_costos):
    return sum(lista_costos)
costo_variable_unitario= costos_variables_unitarios(lista_costo_variable_unitario)


costos_fijos = alquiler + amortizaciones + sueldos

margen_contribucion_unitario = precio_venta - costo_variable_unitario
margen_contribucion_pct = margen_contribucion_unitario / precio_venta

qe = costos_fijos / margen_contribucion_unitario
ve = qe * precio_venta

margen_seguridad_unidades = ventas_presupuestadas - qe
margen_seguridad_pct = margen_seguridad_unidades / ventas_presupuestadas

punto_cierre = (costos_fijos - amortizaciones) / margen_contribucion_unitario

cantidad_utilidad = (costos_fijos + utilidad_deseada) / margen_contribucion_unitario

# Utilidad del 20% sobre costos totales:
# PV*Q = CT + 20% CT
# PV*Q = 1,2 * (CF + CVu*Q)
# PV*Q - 1,2*CVu*Q = 1,2*CF
# Q = 1,2*CF / (PV - 1,2*CVu)

def calcular_utilidad_porcentaje_ingresado(precio_venta ,costos_fijos ,costo_variable_unitario, utilidad):
    if utilidad < 100:
        return "valor ingresado fuera de rango"
    else:
        return ((1+utilidad/100) * costos_fijos) / (precio_venta - (1 + utilidad/100) * costo_variable_unitario)

cantidad_utilidad_20_costos = calcular_utilidad_porcentaje_ingresado(precio_venta ,costos_fijos ,costo_variable_unitario, 20)

# =========================
# TABLA DE RESULTADOS
# =========================

resultados = pd.DataFrame({
    "Concepto": [
        "Costo tela por metro",
        "Costo tela por remera",
        "Costo variable unitario",
        "Costos fijos",
        "Margen contribución unitario",
        "Margen contribución %",
        "Punto de equilibrio en remeras",
        "Punto de equilibrio en pesos",
        "Margen de seguridad en remeras",
        "Margen de seguridad %",
        "Punto de cierre en remeras",
        "Remeras para utilidad de $700.000",
        "Remeras para utilidad del 20% sobre costos"
    ],
    "Valor": [
        costo_tela_por_metro,
        costo_tela_por_remera,
        costo_variable_unitario,
        costos_fijos,
        margen_contribucion_unitario,
        margen_contribucion_pct,
        qe,
        ve,
        margen_seguridad_unidades,
        margen_seguridad_pct,
        punto_cierre,
        cantidad_utilidad,
        cantidad_utilidad_20_costos
    ]
})

print(resultados)

# =========================
# VERIFICACIÓN NUMÉRICA
# =========================

ingresos_eq = qe * precio_venta
cv_eq = qe * costo_variable_unitario
ct_eq = costos_fijos + cv_eq

print("\nVERIFICACIÓN DEL PUNTO DE EQUILIBRIO")
print(f"Ingresos en equilibrio: ${ingresos_eq:,.2f}")
print(f"Costos variables en equilibrio: ${cv_eq:,.2f}")
print(f"Costos fijos: ${costos_fijos:,.2f}")
print(f"Costos totales en equilibrio: ${ct_eq:,.2f}")
print(f"Resultado: ${ingresos_eq - ct_eq:,.2f}")

# =========================
# GRÁFICO PUNTO DE EQUILIBRIO
# =========================

q = np.linspace(0, 220, 300)

ingresos = precio_venta * q
costos_variables = costo_variable_unitario * q
costos_totales = costos_fijos + costos_variables
costos_fijos_linea = np.full_like(q, costos_fijos)

plt.figure(figsize=(13, 7))

plt.plot(q, ingresos, linewidth=3, label="Ingresos Totales = PV × Q")
plt.plot(q, costos_totales, linewidth=3, label="Costos Totales = CF + CVu × Q")
plt.plot(q, costos_variables, linestyle="--", linewidth=2, label="Costos Variables = CVu × Q")
plt.plot(q, costos_fijos_linea, linewidth=2, label="Costos Fijos")

# Zona de pérdidas
plt.fill_between(
    q,
    ingresos,
    costos_totales,
    where=(costos_totales > ingresos),
    alpha=0.25,
    label="Zona de pérdidas"
)

# Zona de beneficios
plt.fill_between(
    q,
    ingresos,
    costos_totales,
    where=(ingresos > costos_totales),
    alpha=0.25,
    label="Zona de beneficios"
)

# Punto de equilibrio
plt.scatter(qe, ve, s=120, zorder=5)

plt.axvline(qe, linestyle="--", linewidth=1)
plt.axhline(ve, linestyle="--", linewidth=1)

plt.text(
    qe + 3,
    ve,
    f"Punto de equilibrio\nQe = {qe:.2f} remeras\nVe = ${ve:,.0f}",
    fontsize=10
)

plt.title("Punto de equilibrio económico - Melbourne SA", fontsize=16)
plt.xlabel("Cantidad de remeras", fontsize=12)
plt.ylabel("Pesos ($)", fontsize=12)

plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()