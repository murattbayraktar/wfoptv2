import json
import os
from datetime import datetime
import pandas as pd


def _metric_row(label: str, val) -> str:
    if val is None or (isinstance(val, float) and val != val):
        return f"<td>{label}</td><td>-</td>"
    if isinstance(val, float):
        return f"<td>{label}</td><td>{val:.2f}</td>"
    return f"<td>{label}</td><td>{val}</td>"


def generate_training_report(
    model_registry: dict,
    output_path: str,
    plot_paths: dict = None,
) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    plot_paths = plot_paths or {}

    rows = ""
    for key, info in model_registry.get("models", {}).items():
        top5 = ", ".join(info.get("feature_importance_top5", []))
        all_scores_str = " | ".join(
            f"{m}: {s:.2f}" for m, s in info.get("all_scores", {}).items()
        )
        rows += f"""
        <tr>
            <td><b>{key}</b></td>
            <td>{info.get('best_model', '-')}</td>
            <td>{info.get('cv_rmse', '-'):.2f}</td>
            <td>{info.get('cv_mae', '-'):.2f}</td>
            <td>{all_scores_str}</td>
            <td>{top5}</td>
            <td>{info.get('selection_reason', '-')}</td>
        </tr>"""

    plots_html = ""
    for name, path in plot_paths.items():
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            plots_html += f"<h3>{name}</h3>\n{content}\n"

    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Eğitim Raporu — {ts}</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 40px; background: #f9f9f9; }}
  h1 {{ color: #2c3e50; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
  th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
  th {{ background: #2c3e50; color: white; }}
  tr:nth-child(even) {{ background: #f2f2f2; }}
</style>
</head>
<body>
<h1>Banka Tahmin Sistemi — Eğitim Raporu</h1>
<p>Oluşturulma: {ts}</p>
<p>Veri aralığı: {model_registry.get('data_range', {}).get('start', '?')} →
   {model_registry.get('data_range', {}).get('end', '?')}</p>

<h2>Model Seçimi Sonuçları</h2>
<table>
<tr>
  <th>Anahtar</th><th>Seçilen Model</th><th>CV RMSE</th><th>CV MAE</th>
  <th>Tüm Skorlar</th><th>Top 5 Feature</th><th>Gerekçe</th>
</tr>
{rows}
</table>

{plots_html}
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


def generate_forecast_report(
    forecast_data: dict,
    output_path: str,
    plot_paths: dict = None,
) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    plot_paths = plot_paths or {}

    summary = forecast_data.get("summary", {})
    by_type = forecast_data.get("by_type", {})

    summary_rows = ""
    for tt, info in by_type.items():
        daily = info.get("daily", [])
        total = sum(d.get("predicted_count", 0) for d in daily)
        model = info.get("model_used", "-")
        summary_rows += f"<tr><td>{tt}</td><td>{model}</td><td>{total:,.0f}</td></tr>"

    plots_html = ""
    for name, path in plot_paths.items():
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            plots_html += f"<h3>{name}</h3>\n{content}\n"

    # Takvim uyarıları
    calendar_rows = ""
    for tt, info in by_type.items():
        for day in info.get("daily", []):
            flags = day.get("calendar_flags", [])
            if flags:
                calendar_rows += f"<tr><td>{day['date']}</td><td>{tt}</td><td>{', '.join(flags)}</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Tahmin Raporu — {ts}</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 40px; background: #f9f9f9; }}
  h1 {{ color: #2c3e50; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
  th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
  th {{ background: #2c3e50; color: white; }}
  tr:nth-child(even) {{ background: #f2f2f2; }}
  .card {{ background: white; border-radius: 8px; padding: 16px; margin: 12px 0;
           box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
</style>
</head>
<body>
<h1>Banka Tahmin Sistemi — Tahmin Raporu</h1>
<p>Oluşturulma: {ts}</p>
<p>Tahmin aralığı: {forecast_data.get('forecast_range', {}).get('start', '?')} →
   {forecast_data.get('forecast_range', {}).get('end', '?')}</p>

<div class="card">
<h2>Özet</h2>
<table>
<tr><th>İşlem Tipi</th><th>Kullanılan Model</th><th>Toplam Tahmin</th></tr>
{summary_rows}
</table>
</div>

{plots_html}

<div class="card">
<h2>Takvim Uyarıları</h2>
<table>
<tr><th>Tarih</th><th>İşlem Tipi</th><th>Bayraklar</th></tr>
{calendar_rows}
</table>
</div>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path
