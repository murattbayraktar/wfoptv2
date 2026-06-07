import pandas as pd
import numpy as np
import os
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


def plot_forecast(
    forecast_df: pd.DataFrame,
    transaction_type: str,
    output_path: str,
    title: str = None,
) -> str:
    """
    Günlük tahmin grafiği: çizgi + %80 güven bandı + tatil işaretçileri.
    forecast_df: date, predicted_count, lower_80, upper_80, calendar_flags sütunları beklenir.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=forecast_df["date"],
        y=forecast_df["upper_80"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        name="Üst PI",
    ))
    fig.add_trace(go.Scatter(
        x=forecast_df["date"],
        y=forecast_df["lower_80"],
        mode="lines",
        fill="tonexty",
        fillcolor="rgba(100, 149, 237, 0.2)",
        line=dict(width=0),
        name="%80 PI",
    ))
    fig.add_trace(go.Scatter(
        x=forecast_df["date"],
        y=forecast_df["predicted_count"],
        mode="lines+markers",
        name="Tahmin",
        line=dict(color="royalblue", width=2),
        marker=dict(size=4),
    ))

    # Tatil günleri
    if "calendar_flags" in forecast_df.columns:
        holiday_mask = forecast_df["calendar_flags"].str.contains(
            "is_public_holiday|is_religious_holiday", na=False
        )
        holidays = forecast_df[holiday_mask]
        if not holidays.empty:
            fig.add_trace(go.Scatter(
                x=holidays["date"],
                y=holidays["predicted_count"],
                mode="markers",
                marker=dict(color="red", size=8, symbol="star"),
                name="Tatil",
            ))

    fig.update_layout(
        title=title or f"{transaction_type} Günlük Tahmin",
        xaxis_title="Tarih",
        yaxis_title="İşlem Adedi",
        hovermode="x unified",
        template="plotly_white",
    )

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    fig.write_html(output_path)
    return output_path


def plot_hourly_heatmap(
    forecast_df: pd.DataFrame,
    transaction_type: str,
    output_path: str,
) -> str:
    """
    Saatlik ısı haritası: gün × saat matris.
    forecast_df: date, hour, predicted_count beklenir.
    """
    pivot = forecast_df.pivot_table(
        index="date", columns="hour", values="predicted_count", aggfunc="sum"
    )
    pivot.index = pivot.index.astype(str)

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[str(h) for h in pivot.columns],
        y=pivot.index.tolist(),
        colorscale="Blues",
        colorbar=dict(title="İşlem Adedi"),
    ))
    fig.update_layout(
        title=f"{transaction_type} Saatlik Isı Haritası",
        xaxis_title="Saat",
        yaxis_title="Tarih",
        template="plotly_white",
    )

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    fig.write_html(output_path)
    return output_path


def plot_model_comparison(scores: dict, metric: str, output_path: str) -> str:
    """
    Model karşılaştırma bar grafiği: her işlem tipi için model skorları.
    scores: {transaction_type: {model_name: score, ...}, ...}
    """
    rows = []
    for tt, model_scores in scores.items():
        for model_name, score in model_scores.items():
            rows.append({"Tip": tt, "Model": model_name, metric.upper(): score})
    df = pd.DataFrame(rows)

    fig = px.bar(
        df, x="Tip", y=metric.upper(), color="Model",
        barmode="group",
        title=f"Model Karşılaştırması ({metric.upper()})",
        template="plotly_white",
    )

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    fig.write_html(output_path)
    return output_path


def plot_feature_importance(importance_df: pd.DataFrame, title: str, output_path: str) -> str:
    top = importance_df.head(20)
    col = "gain" if "gain" in top.columns else top.columns[-1]
    fig = px.bar(
        top, x=col, y="feature", orientation="h",
        title=title,
        template="plotly_white",
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    fig.write_html(output_path)
    return output_path
