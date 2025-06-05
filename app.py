import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Diamantanalys", layout="wide")

st.title("Diamantanalys – Streamlit App")
st.write("Ladda upp en `diamonds.csv`-fil för att analysera och visualisera data.")
uploaded_file = st.file_uploader("Ladda upp diamonds.csv", type=["csv"])

# Filuppladdning
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Data granskning / kvalitetskontroll
    df.dropna(how="any", inplace=True)
    df = df[(df["x"] > 0) & (df["y"] > 0) & (df["z"] > 0)]
    df["depth_calc"] = 2 * (df["z"] / (df["x"] + df["y"])) * 100
    df["depth_diff"] = np.abs(df["depth"] - df["depth_calc"])
    df = df[df["depth_diff"] <= 1]

    tab1, tab2 = st.tabs(["Dataanalys", "Diamant och pris fördeling av de 4C:n"])

    with tab1:
        st.subheader("Dataförhandsvisning")
        st.dataframe(df.head())

        # Histogram och Scatterplot
        st.subheader("Carat-distribution & Scatterplot (Pris vs Carat)")
        mean_carat = df["carat"].mean().round(3)
        correlation = df["carat"].corr(df["price"])

        fig = make_subplots(rows=1, cols=2, subplot_titles=["Carat distribution", "Carat vs Price"])

        fig.add_trace(
        go.Histogram(x=df["carat"], nbinsx=50, marker_color="blue", name="Carat"), row=1, col=1
        )
        fig.add_vline(x=mean_carat, line=dict(color="red", dash="dash"), row=1, col=1)

        fig.add_trace(
        go.Scatter(x=df["carat"], y=df["price"],
                   mode="markers", marker=dict(opacity=0.3, color="blue")),
        row=1, col=2
        )

        fig.update_layout(showlegend=False, height=500)
        st.plotly_chart(fig, use_container_width=True)

        # Korrelationsmatris (1–2 carat)
        st.subheader("Korrelationsmatris (1–2 carat)")

        df_filtered = df[(df["carat"] >= 1) & (df["carat"] <= 2)].copy()
        df_filtered["cut"] = pd.Categorical(df_filtered["cut"], categories=["Fair", "Good", "Very Good", "Premium", "Ideal"], ordered=True)
        df_filtered["color"] = pd.Categorical(df_filtered["color"], categories=["D", "E", "F", "G", "H", "I", "J"], ordered=True)
        df_filtered["clarity"] = pd.Categorical(df_filtered["clarity"], categories=["I1", "SI2", "SI1", "VS2", "VS1", "VVS2", "VVS1", "IF"], ordered=True)

        df_filtered["cut_encoded"] = df_filtered["cut"].cat.codes
        df_filtered["color_encoded"] = df_filtered["color"].cat.codes
        df_filtered["clarity_encoded"] = df_filtered["clarity"].cat.codes

        corr_df = df_filtered[["price", "carat", "depth", "cut_encoded", "color_encoded", "clarity_encoded"]]
        corr_df = corr_df.rename(columns={"cut_encoded": "cut", "color_encoded": "color", "clarity_encoded": "clarity"})
        corr_matrix = corr_df.corr().round(2)

        fig_corr = px.imshow(corr_matrix, text_auto=True, color_continuous_scale="RdBu_r",
                         title="Korrelationsmatris (1–2 carat)", aspect="auto")
        st.plotly_chart(fig_corr, use_container_width=True)


        # Investeringsanalys
        st.subheader("Förväntad vinstanalys (Top 100 mest vs minst volatila)")
        median_price = df["price"].median()
        good = df[
            (df["cut"].isin(["Ideal", "Premium", "Very Good"])) &
            (df["color"].isin(["D", "E", "F"])) &
            (df["clarity"].isin(["VVS1", "VVS2", "VS1"])) &
            (df["price"] < median_price)
        ].copy()

        good["expected_sale_price"] = (good["price"] * 1.1).round(2)
        good["expected_profit"] = (good["expected_sale_price"] - good["price"]).round(2)
        good["profit_per_carat"] = (good["expected_profit"] / good["carat"]).round(2)

        most = good.sort_values(by="profit_per_carat", ascending=False).head(100).copy()
        least = good.sort_values(by="profit_per_carat", ascending=True).head(100).copy()
        most["kategori"] = "Mest volatil"
        least["kategori"] = "Minst volatil"

        volatility_df = pd.concat([most, least])
        profits = volatility_df.groupby("kategori")["expected_profit"].sum()

        fig_bar = go.Figure(go.Bar(
            x=profits.index,
            y=profits.values,
            text=[f"${v:,.0f}" for v in profits.values],
            textposition='outside',
            marker_color=['crimson', 'steelblue']
        ))

        fig_bar.update_layout(
            title="Total förväntad vinst – Mest vs. Minst volatila",
            yaxis_title="Förväntad vinst (USD)",
            xaxis_title="Kategori",
            template="plotly_white"
        )
        st.plotly_chart(fig_bar, use_container_width=True)


    with tab2:
        st.subheader("Diamant och pris fördelning av de 4 C:n")

        # Carat-slider
        min_carat = float(df["carat"].min())
        max_carat = float(df["carat"].max())

        carat_range = st.slider(
            "Välj carat-intervall:",
            min_value=min_carat,
            max_value=max_carat,
            value=(min_carat, max_carat),
            step=0.1,
            key="carat_slider"
        )

        # Filtrera datan baserat på carat
        df_filtered = df[(df["carat"] >= carat_range[0]) & (df["carat"] <= carat_range[1])]

        val = st.radio(
            "Välj vilket C du vill analysera:",
         ["Carat", "Cut", "Color", "Clarity"], key="val_c_4c",
         horizontal=True
        )

        if val == "Carat":
            fig = px.histogram(df_filtered, x="carat", nbins=50, title="Diamant fördelning av Carat(Vikt)", color_discrete_sequence=["#2b8cbe"])
            st.plotly_chart(fig, use_container_width=True)

        elif val == "Cut":
            fig = px.histogram(df_filtered, x="cut", title="Diamant fördelning av Cut(Slipnings grad)", color="cut")
            st.plotly_chart(fig, use_container_width=True)

        elif val == "Color":
            fig = px.histogram(df_filtered, x="color", title="Diamant fördelning av Color(Färg)", color="color")
            st.plotly_chart(fig, use_container_width=True)

        elif val == "Clarity":
            fig = px.histogram(df_filtered, x="clarity", title="Diamant fördelning av Clarity(Klarhet)", color="clarity")
            st.plotly_chart(fig, use_container_width=True)


        if val == "Carat":
            fig = px.scatter(df_filtered, x="carat", y="price", title="Pris fördelning av Carat(Vikt)", color_discrete_sequence=["#2b8cbe"])
            st.plotly_chart(fig, use_container_width=True)

        elif val == "Cut":
            fig = px.box(df_filtered, x="cut", y="price" , title="Pris fördelning av Cut(Slipnings grad)", color="cut")
            st.plotly_chart(fig, use_container_width=True)

        elif val == "Color":
            fig = px.box(df_filtered, x="color", y="price" , title="Pris fördelning av Color(Färg)", color="color")
            st.plotly_chart(fig, use_container_width=True)

        elif val == "Clarity":
            fig = px.box(df_filtered, x="clarity", y="price" , title="Pris fördelning av Clarity(Klarhet)", color="clarity")
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Ladda upp en CSV-fil med diamantdata för att börja.")
