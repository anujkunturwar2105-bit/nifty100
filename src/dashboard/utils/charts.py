"""
Plotly Interactive Chart Utilities
Nifty 100 Financial Intelligence Platform
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def create_radar_chart(df: pd.DataFrame, company_id: str, group_name: str) -> go.Figure:
    """Create radar chart for peer percentiles."""
    fig = go.Figure()

    comp_df = df[df["company_id"] == company_id]
    if comp_df.empty:
        return fig

    metrics = comp_df["metric"].tolist()
    percentiles = comp_df["percentile"].tolist()

    # Close loop for radar plot
    metrics_closed = metrics + [metrics[0]]
    pct_closed = percentiles + [percentiles[0]]

    fig.add_trace(go.Scatterpolar(
        r=pct_closed,
        theta=metrics_closed,
        fill="toself",
        name=company_id,
        line=dict(color="#2563eb", width=2),
        fillcolor="rgba(37, 99, 235, 0.2)"
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], ticksuffix="%"),
        ),
        showlegend=True,
        title=dict(text=f"Peer Percentile Radar: {company_id} vs {group_name}", font=dict(size=14)),
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40)
    )
    return fig


def create_multi_metric_trend_chart(df: pd.DataFrame, ticker: str, metrics: list[tuple[str, str]]) -> go.Figure:
    """Create multi-line trend chart over financial years."""
    fig = go.Figure()
    if df.empty:
        return fig

    years = df["year"].tolist()
    colors_list = ["#2563eb", "#16a34a", "#dc2626", "#d97706", "#9333ea"]

    for idx, (col_name, label) in enumerate(metrics):
        if col_name in df.columns:
            vals = df[col_name].tolist()
            color = colors_list[idx % len(colors_list)]
            fig.add_trace(go.Scatter(
                x=years,
                y=vals,
                mode="lines+markers",
                name=label,
                line=dict(width=2.5, color=color),
                marker=dict(size=6)
            ))

    fig.update_layout(
        title=dict(text=f"{ticker} Multi-Year Financial Trends", font=dict(size=14)),
        xaxis=dict(title="Financial Year"),
        yaxis=dict(title="Value"),
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def create_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str, color_col: str | None = None) -> go.Figure:
    """Create sleek bar chart."""
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        color=color_col or x_col,
        title=title,
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig.update_layout(showlegend=False, xaxis=dict(title=x_col), yaxis=dict(title=y_col))
    return fig
