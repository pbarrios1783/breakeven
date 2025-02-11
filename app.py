import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# Configuración inicial de la página
st.set_page_config(layout="wide", page_title="Break Even Calculator")


# Función para calcular datos actuales desde el archivo
def calculate_current_data(transactions_df):
    # Filtrar los costos de producción por tipo
    produccion_df = transactions_df[transactions_df['account_credito'].isin([
        "Inventario - Producción en Proceso (MP)", "Inventario - Producción en Proceso (MI)",
        "Inventario - Producción en Proceso (MOD)", "Inventario - Producción en Proceso (MOI)",
        "Inventario - Producción en Proceso (CFD)", "Inventario - Producción en Proceso (CFS)"
    ])]

    # Agrupar por tipo de costo
    costos = produccion_df.groupby('account_credito').agg(
        Total_Costo=('amount_credit', lambda x: x.abs().sum())  # Convertir valores negativos a positivos
    ).reset_index()

    # Identificar costos fijos y variables
    costos['Tipo'] = costos['account_credito'].map({
        "Inventario - Producción en Proceso (MOD)": "Fijo",
        "Inventario - Producción en Proceso (MOI)": "Fijo",
        "Inventario - Producción en Proceso (CFD)": "Fijo",
        "Inventario - Producción en Proceso (MP)": "Variable",
        "Inventario - Producción en Proceso (CFS)": "Variable",
        "Inventario - Producción en Proceso (MI)": "Variable"
    })

    costos_fijos_totales = costos[costos['Tipo'] == "Fijo"]['Total_Costo'].sum()
    costos_variables_totales = costos[costos['Tipo'] == "Variable"]['Total_Costo'].sum()

    # Cálculo del precio de venta unitario
    ventas_df = transactions_df[transactions_df['account_credito'].isin([
        "Ventas de Productos - Económica", "Ventas de Productos - Premium"
    ])]
    total_ventas = ventas_df['amount_credit'].abs().sum()  # Convertir valores negativos a positivos
    total_cantidad = ventas_df['cantidad'].sum()
    precio_venta_unitario = max(total_ventas / total_cantidad, 0) if total_cantidad != 0 else 0

    # Costo variable unitario
    costo_variable_unitario = costos_variables_totales / total_cantidad if total_cantidad != 0 else 0

    return costos_fijos_totales, precio_venta_unitario, costo_variable_unitario, total_cantidad, total_ventas


# Función para formatear números redondeados sin decimales
def format_currency(value):
    return f"{int(round(value, 0)):,}".replace(",", "X").replace(".", ",").replace("X", ".")


# Función para formatear números con dos decimales
def format_decimal(value):
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# Mostrar el dashboard del punto de equilibrio
def show():
    file_path = 'sample_transactions_df.xlsx'
    transactions_df = pd.read_excel(file_path)

    # Obtener datos actuales
    costos_fijos_totales, precio_venta_unitario, costo_variable_unitario, total_cantidad, total_ventas = calculate_current_data(transactions_df)

    # Calculadora de punto de equilibrio
    st.title("Breakeven Calculator")
    
     # Botón para regresar al Menú Principal
     #if st.button("Regresar"):
     
    #st.session_state.current_page = None

    # Mostrar indicadores actuales del período
    #st.markdown("### Datos Actuales del Período")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Fixed Costs", format_currency(costos_fijos_totales))
    col2.metric("Unit Selling Price", format_decimal(precio_venta_unitario))
    col3.metric("Unit Variable Cost", format_decimal(costo_variable_unitario))
    col4.metric("Actual Sold Units", format_currency(total_cantidad))
    col5.metric("Total Revenue", format_currency(total_ventas))

    # Entrada de datos en la barra lateral
    st.sidebar.header("Input Parameters")
    costos_fijos_input = st.sidebar.number_input("Total Fixed Costs:", value=float(costos_fijos_totales), step=100.0)
    precio_venta_input = st.sidebar.number_input("Unit Selling Price:", value=float(precio_venta_unitario), step=1.0)
    costo_variable_input = st.sidebar.number_input("Unit Variable Cost:", value=float(costo_variable_unitario), step=1.0)

    # Cálculo del punto de equilibrio
    if precio_venta_input > costo_variable_input:
        unidades_equilibrio = costos_fijos_input / (precio_venta_input - costo_variable_input)
        ingresos_equilibrio = unidades_equilibrio * precio_venta_input
    else:
        unidades_equilibrio = 0
        ingresos_equilibrio = 0

    # Mostrar resultados
    st.subheader("Results")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"Break-even Units: {format_decimal(unidades_equilibrio)}")
    with col2:
        st.write(f"Break-even Revenue: {format_currency(ingresos_equilibrio)}")

    # Visualización del punto de equilibrio
    #st.subheader("Visualización del Punto de Equilibrio")
    fig = go.Figure()

    # Línea de costos fijos
    fig.add_trace(go.Scatter(
        x=[0, unidades_equilibrio * 1.5], 
        y=[costos_fijos_input, costos_fijos_input],
        mode="lines", name="Fixed Costs", line=dict(color="#00B496", dash="dash")
    ))

    # Línea de costos totales
    x_totales = list(range(0, int(unidades_equilibrio * 1.5)))
    y_totales = [costos_fijos_input + (costo_variable_input * x) for x in x_totales]
    fig.add_trace(go.Scatter(
        x=x_totales, y=y_totales,
        mode="lines", name="Total Costs", line=dict(color="#EE0943")
    ))

    # Línea de ingresos
    y_ingresos = [precio_venta_input * x for x in x_totales]
    fig.add_trace(go.Scatter(
        x=x_totales, y=y_ingresos,
        mode="lines", name="Revenues", line=dict(color="#12239E")
    ))

    # Configuración del gráfico
    fig.update_layout(
        #title="Punto de Equilibrio: Costos e Ingresos",
        xaxis_title="Units Sold",
        yaxis_title="Amounts",
        height=400,
        legend_title="Components",
    )

    st.plotly_chart(fig, use_container_width=True)

    st.sidebar.markdown("""
<div class="instrucciones-box">
<h3>💡 How to Use This Tool</h3>
<ol>
    <li>📊 Adjust input parameters such as fixed costs, variable costs, and unit selling price.</li>
    <li>🔄 Calculate the break-even point —the number of units needed to cover costs.</li>
    <li>📉 Visualize cost structures and revenue in the interactive chart.</li>
    <li>💡 Use the insights to optimize pricing and business strategy.</li>
</ol>
</div>
<style>
    .instrucciones-box {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        font-size: 14px;
    }
    .instrucciones-box ol, .instrucciones-box li {
        font-size: 16px;
        line-height: 1.4;
    }
    .instrucciones-box h3 {
        margin-top: 0;
        margin-bottom: 5px;
        font-size: 15px;
    }
</style>
""", unsafe_allow_html=True)

    st.markdown("""
---
### ⚠ Disclaimer  
This tool is designed for **informational and educational purposes only** and does not constitute financial or business advice.  The accuracy of the results depends on the data entered, and actual business conditions may vary.  

© 2024 **Patricia Barrios**. All rights reserved.
""")





# Ejecutar la página
if __name__ == "__main__":
    show()

