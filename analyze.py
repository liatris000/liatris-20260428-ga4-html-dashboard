#!/usr/bin/env python3
"""
GA4風CSVデータからHTMLダッシュボードを自動生成するスクリプト
※ データはすべてサンプル（架空のフィクション）です
"""

import csv
import json
from datetime import datetime
from collections import defaultdict

def load_csv(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def parse_duration(s):
    """'00:04:30' -> seconds"""
    parts = s.strip().split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0

def fmt_duration(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m}分{s:02d}秒"

def analyze(rows):
    daily = defaultdict(lambda: {"sessions": 0, "pageviews": 0, "conversions": 0, "revenue": 0})
    by_page = defaultdict(lambda: {"sessions": 0, "pageviews": 0, "conversions": 0, "revenue": 0, "duration_sum": 0, "duration_count": 0, "bounce_sum": 0})

    for r in rows:
        d = r["date"]
        daily[d]["sessions"] += int(r["sessions"])
        daily[d]["pageviews"] += int(r["pageviews"])
        daily[d]["conversions"] += int(r["conversions"])
        daily[d]["revenue"] += int(r["revenue"])

        p = r["page_title"]
        by_page[p]["sessions"] += int(r["sessions"])
        by_page[p]["pageviews"] += int(r["pageviews"])
        by_page[p]["conversions"] += int(r["conversions"])
        by_page[p]["revenue"] += int(r["revenue"])
        by_page[p]["duration_sum"] += parse_duration(r["avg_session_duration"]) * int(r["sessions"])
        by_page[p]["duration_count"] += int(r["sessions"])
        by_page[p]["bounce_sum"] += float(r["bounce_rate"]) * int(r["sessions"])

    sorted_dates = sorted(daily.keys())

    totals = {
        "sessions": sum(v["sessions"] for v in daily.values()),
        "pageviews": sum(v["pageviews"] for v in daily.values()),
        "conversions": sum(v["conversions"] for v in daily.values()),
        "revenue": sum(v["revenue"] for v in daily.values()),
    }
    totals["cvr"] = totals["conversions"] / totals["sessions"] * 100 if totals["sessions"] else 0

    return sorted_dates, daily, by_page, totals

def build_html(sorted_dates, daily, by_page, totals):
    dates_json = json.dumps(sorted_dates)
    sessions_json = json.dumps([daily[d]["sessions"] for d in sorted_dates])
    pv_json = json.dumps([daily[d]["pageviews"] for d in sorted_dates])
    conv_json = json.dumps([daily[d]["conversions"] for d in sorted_dates])
    rev_json = json.dumps([daily[d]["revenue"] // 1000 for d in sorted_dates])

    page_rows = ""
    for title, v in sorted(by_page.items(), key=lambda x: -x[1]["sessions"]):
        avg_dur = v["duration_sum"] / v["duration_count"] if v["duration_count"] else 0
        avg_bounce = v["bounce_sum"] / v["duration_count"] if v["duration_count"] else 0
        cvr = v["conversions"] / v["sessions"] * 100 if v["sessions"] else 0
        page_rows += f"""
        <tr>
          <td>{title}</td>
          <td class="num">{v['sessions']:,}</td>
          <td class="num">{v['pageviews']:,}</td>
          <td class="num">{fmt_duration(avg_dur)}</td>
          <td class="num">{avg_bounce*100:.1f}%</td>
          <td class="num">{v['conversions']:,}</td>
          <td class="num">{cvr:.2f}%</td>
          <td class="num">¥{v['revenue']:,}</td>
        </tr>"""

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Webアクセス解析ダッシュボード（サンプルデータ）</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --primary: #6c47ff;
    --accent: #ff6b6b;
    --bg: #0f0f1a;
    --surface: #1a1a2e;
    --border: #2a2a4a;
    --text: #e8e8f0;
    --muted: #8888aa;
    --green: #00c896;
    --yellow: #ffd166;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', 'Hiragino Sans', sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 24px;
    min-height: 100vh;
  }}
  header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 32px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
  }}
  header h1 {{ font-size: 1.5rem; font-weight: 700; }}
  header h1 span {{ color: var(--primary); }}
  .notice {{
    font-size: 0.75rem;
    color: var(--accent);
    background: rgba(255,107,107,0.1);
    border: 1px solid var(--accent);
    padding: 4px 10px;
    border-radius: 4px;
  }}
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin-bottom: 32px;
  }}
  .kpi-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }}
  .kpi-card .label {{ font-size: 0.75rem; color: var(--muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em; }}
  .kpi-card .value {{ font-size: 1.8rem; font-weight: 700; }}
  .kpi-card .value.green {{ color: var(--green); }}
  .kpi-card .value.purple {{ color: var(--primary); }}
  .kpi-card .value.yellow {{ color: var(--yellow); }}
  .kpi-card .value.red {{ color: var(--accent); }}
  .charts-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 32px;
  }}
  @media (max-width: 768px) {{ .charts-grid {{ grid-template-columns: 1fr; }} }}
  .chart-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }}
  .chart-card h3 {{ font-size: 0.9rem; color: var(--muted); margin-bottom: 16px; }}
  .chart-card.full {{ grid-column: 1 / -1; }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }}
  thead th {{
    text-align: left;
    padding: 10px 12px;
    color: var(--muted);
    font-weight: 600;
    font-size: 0.75rem;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border);
  }}
  tbody tr {{
    border-bottom: 1px solid var(--border);
    transition: background 0.15s;
  }}
  tbody tr:hover {{ background: rgba(108,71,255,0.06); }}
  tbody td {{ padding: 10px 12px; }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .table-section {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 32px;
    overflow-x: auto;
  }}
  .table-section h3 {{ font-size: 0.9rem; color: var(--muted); margin-bottom: 16px; }}
  footer {{
    text-align: center;
    font-size: 0.75rem;
    color: var(--muted);
    padding-top: 24px;
    border-top: 1px solid var(--border);
  }}
  .generated-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.7rem;
    color: var(--muted);
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 4px 8px;
    border-radius: 4px;
    margin-top: 8px;
  }}
</style>
</head>
<body>

<header>
  <div>
    <h1>📊 Webアクセス解析 <span>ダッシュボード</span></h1>
    <div style="font-size:0.8rem; color:var(--muted); margin-top:4px;">2026年4月 — サイト全体</div>
  </div>
  <div class="notice">⚠️ このデータはすべてサンプル（架空のフィクション）です</div>
</header>

<div class="kpi-grid">
  <div class="kpi-card">
    <div class="label">総セッション数</div>
    <div class="value purple">{totals['sessions']:,}</div>
  </div>
  <div class="kpi-card">
    <div class="label">総ページビュー</div>
    <div class="value purple">{totals['pageviews']:,}</div>
  </div>
  <div class="kpi-card">
    <div class="label">コンバージョン数</div>
    <div class="value green">{totals['conversions']:,}</div>
  </div>
  <div class="kpi-card">
    <div class="label">CVR</div>
    <div class="value green">{totals['cvr']:.2f}%</div>
  </div>
  <div class="kpi-card">
    <div class="label">売上合計（架空）</div>
    <div class="value yellow">¥{totals['revenue']:,}</div>
  </div>
</div>

<div class="charts-grid">
  <div class="chart-card full">
    <h3>日別セッション数 / ページビュー推移</h3>
    <canvas id="lineChart" height="80"></canvas>
  </div>
  <div class="chart-card">
    <h3>日別コンバージョン数</h3>
    <canvas id="barChart" height="150"></canvas>
  </div>
  <div class="chart-card">
    <h3>日別売上（架空・千円単位）</h3>
    <canvas id="revenueChart" height="150"></canvas>
  </div>
</div>

<div class="table-section">
  <h3>ページ別パフォーマンス</h3>
  <table>
    <thead>
      <tr>
        <th>ページ名</th>
        <th style="text-align:right">セッション</th>
        <th style="text-align:right">PV</th>
        <th style="text-align:right">平均滞在時間</th>
        <th style="text-align:right">直帰率</th>
        <th style="text-align:right">CV数</th>
        <th style="text-align:right">CVR</th>
        <th style="text-align:right">売上（架空）</th>
      </tr>
    </thead>
    <tbody>
      {page_rows}
    </tbody>
  </table>
</div>

<footer>
  <p>Claude Code で自動生成されたサンプルダッシュボード</p>
  <div class="generated-badge">⚡ Generated by Claude Code · {generated_at} · ※全データ架空</div>
</footer>

<script>
const dates = {dates_json};
const sessions = {sessions_json};
const pvs = {pv_json};
const convs = {conv_json};
const revs = {rev_json};

const gridColor = 'rgba(255,255,255,0.05)';
const labelColor = '#8888aa';

Chart.defaults.color = labelColor;
Chart.defaults.borderColor = gridColor;

new Chart(document.getElementById('lineChart'), {{
  type: 'line',
  data: {{
    labels: dates,
    datasets: [
      {{
        label: 'セッション数',
        data: sessions,
        borderColor: '#6c47ff',
        backgroundColor: 'rgba(108,71,255,0.12)',
        fill: true,
        tension: 0.4,
        pointRadius: 2,
      }},
      {{
        label: 'ページビュー',
        data: pvs,
        borderColor: '#00c896',
        backgroundColor: 'rgba(0,200,150,0.08)',
        fill: true,
        tension: 0.4,
        pointRadius: 2,
      }}
    ]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ position: 'top' }} }},
    scales: {{
      x: {{ ticks: {{ maxTicksLimit: 14, font: {{ size: 11 }} }} }},
      y: {{ beginAtZero: false }}
    }}
  }}
}});

new Chart(document.getElementById('barChart'), {{
  type: 'bar',
  data: {{
    labels: dates,
    datasets: [{{
      label: 'コンバージョン数',
      data: convs,
      backgroundColor: 'rgba(0,200,150,0.7)',
      borderRadius: 3,
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ ticks: {{ maxTicksLimit: 10, font: {{ size: 10 }} }} }},
      y: {{ beginAtZero: true }}
    }}
  }}
}});

new Chart(document.getElementById('revenueChart'), {{
  type: 'bar',
  data: {{
    labels: dates,
    datasets: [{{
      label: '売上（千円）',
      data: revs,
      backgroundColor: 'rgba(255,209,102,0.7)',
      borderRadius: 3,
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ ticks: {{ maxTicksLimit: 10, font: {{ size: 10 }} }} }},
      y: {{ beginAtZero: true }}
    }}
  }}
}});
</script>
</body>
</html>"""
    return html

def main():
    print("🔍 CSVデータを読み込み中...")
    rows = load_csv("/tmp/note_artifact/data/sample_ga4.csv")
    print(f"   → {len(rows)}行を読み込みました")

    print("📊 データを集計中...")
    sorted_dates, daily, by_page, totals = analyze(rows)
    print(f"   → 期間: {sorted_dates[0]} 〜 {sorted_dates[-1]}")
    print(f"   → 総セッション: {totals['sessions']:,}")
    print(f"   → 総PV: {totals['pageviews']:,}")
    print(f"   → CV数: {totals['conversions']:,} (CVR: {totals['cvr']:.2f}%)")
    print(f"   → 売上合計（架空）: ¥{totals['revenue']:,}")

    print("🎨 HTMLダッシュボードを生成中...")
    html = build_html(sorted_dates, daily, by_page, totals)

    out = "/tmp/note_artifact/report.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"   → 保存先: {out}")
    print("✅ 完了!")

if __name__ == "__main__":
    main()
