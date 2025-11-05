"""Streamlit dashboard for interactive sales analysis."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_PATH = "data/sample_sales_data.csv"


@st.cache_data(show_spinner=False)
def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    """Load the sample sales dataset."""
    df = pd.read_csv(path, parse_dates=["order_date"])
    df.sort_values("order_date", inplace=True)
    df["month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
    df["gross_margin"] = df["profit"] / df["revenue"]
    return df


def main() -> None:
    st.set_page_config(
        page_title="Sales Performance Cockpit",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("📈 Cockpit estratégico de ventas")
    st.caption(
        "Dashboard de ejemplo inspirado en flujos de trabajo de analítica avanzada."
        " Utiliza un conjunto de datos sintético para mostrar cómo priorizar"
        " decisiones comerciales clave."
    )

    df = load_data()

    with st.sidebar:
        st.header("Controles de exploración")
        min_date, max_date = df["order_date"].min(), df["order_date"].max()
        start_date, end_date = st.slider(
            "Rango de fechas",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="YYYY-MM-DD",
        )

        regions = sorted(df["region"].unique())
        selected_regions = st.multiselect(
            "Regiones",
            options=regions,
            default=regions,
        )

        segments = sorted(df["customer_segment"].unique())
        selected_segments = st.multiselect(
            "Segmentos de cliente",
            options=segments,
            default=segments,
        )

        categories = sorted(df["product_category"].unique())
        selected_categories = st.multiselect(
            "Categorías",
            options=categories,
            default=categories,
        )

        st.markdown("---")
        st.caption(
            "💡 Consejo: ajusta los filtros para simular decisiones y observar"
            " impactos en KPIs en tiempo real."
        )

    mask = (
        (df["order_date"] >= pd.Timestamp(start_date))
        & (df["order_date"] <= pd.Timestamp(end_date))
        & (df["region"].isin(selected_regions))
        & (df["customer_segment"].isin(selected_segments))
        & (df["product_category"].isin(selected_categories))
    )
    filtered = df.loc[mask]

    if filtered.empty:
        st.warning("No hay datos para la combinación de filtros seleccionada.")
        return

    # KPIs
    total_revenue = filtered["revenue"].sum()
    total_profit = filtered["profit"].sum()
    total_units = filtered["units"].sum()
    avg_discount = filtered["discount"].mean()
    gross_margin = filtered["gross_margin"].mean()

    st.subheader("Indicadores clave")
    kpi_cols = st.columns(5)
    kpi_cols[0].metric("Ingresos", f"${total_revenue:,.0f}")
    kpi_cols[1].metric("Utilidad", f"${total_profit:,.0f}")
    kpi_cols[2].metric("Unidades vendidas", f"{total_units:,.0f}")
    kpi_cols[3].metric("Descuento medio", f"{avg_discount:.1%}")
    kpi_cols[4].metric("Margen bruto medio", f"{gross_margin:.1%}")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs([
        "Evolución temporal",
        "Desempeño por segmentos",
        "Tablero de oportunidades",
    ])

    with tab1:
        st.markdown("#### Tendencia de ingresos")
        revenue_by_month = (
            filtered.groupby("month", as_index=False)["revenue"].sum()
        )
        fig_revenue = px.line(
            revenue_by_month,
            x="month",
            y="revenue",
            markers=True,
            labels={"month": "Mes", "revenue": "Ingresos"},
            template="plotly_white",
        )
        fig_revenue.update_traces(line_color="#3366CC")
        st.plotly_chart(fig_revenue, use_container_width=True)

        st.markdown("#### Comparativa de margen por categoría")
        margin_by_category = (
            filtered.groupby("product_category", as_index=False)["gross_margin"].mean()
        )
        fig_margin = px.bar(
            margin_by_category,
            x="product_category",
            y="gross_margin",
            labels={"product_category": "Categoría", "gross_margin": "Margen"},
            template="plotly_white",
            text_auto=".1%",
        )
        fig_margin.update_traces(marker_color="#109618")
        st.plotly_chart(fig_margin, use_container_width=True)

    with tab2:
        st.markdown("#### Ingresos por región")
        revenue_by_region = (
            filtered.groupby("region", as_index=False)["revenue"].sum()
        )
        fig_region = px.bar(
            revenue_by_region,
            x="region",
            y="revenue",
            color="region",
            template="plotly_white",
            labels={"region": "Región", "revenue": "Ingresos"},
        )
        st.plotly_chart(fig_region, use_container_width=True)

        st.markdown("#### Mix de productos")
        mix_fig = px.sunburst(
            filtered,
            path=["product_category", "sub_category"],
            values="revenue",
            color="gross_margin",
            color_continuous_scale="RdYlGn",
            color_continuous_midpoint=filtered["gross_margin"].mean(),
            labels={"gross_margin": "Margen"},
        )
        st.plotly_chart(mix_fig, use_container_width=True)

    with tab3:
        st.markdown("#### Pipeline priorizado")
        ranked = (
            filtered.assign(
                revenue_per_unit=lambda x: x["revenue"] / x["units"],
                contribution=lambda x: x["revenue"] / total_revenue,
            )
            .sort_values("revenue", ascending=False)
            .head(15)
        )
        st.dataframe(
            ranked[
                [
                    "order_date",
                    "region",
                    "product_category",
                    "sub_category",
                    "customer_segment",
                    "revenue",
                    "profit",
                    "revenue_per_unit",
                    "contribution",
                ]
            ]
            .rename(
                columns={
                    "order_date": "Fecha",
                    "region": "Región",
                    "product_category": "Categoría",
                    "sub_category": "Subcategoría",
                    "customer_segment": "Segmento",
                    "revenue": "Ingresos",
                    "profit": "Utilidad",
                    "revenue_per_unit": "Ingresos por unidad",
                    "contribution": "Contribución",
                }
            )
            .style.format(
                {
                    "Ingresos": "${:,.0f}",
                    "Utilidad": "${:,.0f}",
                    "Ingresos por unidad": "${:,.0f}",
                    "Contribución": "{:.1%}",
                }
            ),
            use_container_width=True,
        )

        st.markdown("#### Insights automáticos")
        key_regions = revenue_by_region.sort_values("revenue", ascending=False)
        best_region = key_regions.iloc[0]
        worst_region = key_regions.iloc[-1]
        st.success(
            f"Mayor ingreso en **{best_region['region']}** (${best_region['revenue']:,.0f})."
        )
        st.info(
            f"Oportunidad de crecimiento en **{worst_region['region']}**"
            f" (${worst_region['revenue']:,.0f})."
        )

        top_margin = margin_by_category.sort_values("gross_margin", ascending=False).iloc[0]
        st.write(
            f"La categoría con mejor margen promedio es **{top_margin['product_category']}**"
            f" ({top_margin['gross_margin']:.1%})."
        )

    st.markdown("---")
    st.caption(
        "Construido con Streamlit y Plotly. Personaliza este esqueleto para"
        " conectarlo a tus fuentes de datos y modelos predictivos."
    )


if __name__ == "__main__":
    main()
