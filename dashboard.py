"""
Simple web dashboard to view collected articles
Default view: Relevant only
Toggle: All (includes filtered/irrelevant)
"""
from flask import Flask, jsonify, send_file
import csv
import glob
import os

app = Flask(__name__)

def get_latest_csv():
    csv_files = glob.glob("articles_*.csv")
    if not csv_files:
        return None
    return max(csv_files, key=os.path.getctime)

def load_articles():
    csv_file = get_latest_csv()
    if not csv_file:
        return []
    with open(csv_file, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

@app.route("/")
def index():
    return r"""
<!DOCTYPE html>
<html>
<head>
  <title>⚡ Energy-AI Monitor Dashboard</title>
  <meta charset="UTF-8">
  <style>
    * { margin:0; padding:0; box-sizing:border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      padding: 20px;
    }
    .container {
      max-width: 1400px;
      margin: 0 auto;
      background: white;
      padding: 30px;
      border-radius: 15px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    h1 { color:#2c3e50; margin-bottom:10px; font-size:32px; }
    .subtitle { color:#7f8c8d; margin-bottom: 18px; font-size:16px; }

    .stats {
      display:grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 20px;
      margin-bottom: 18px;
    }
    .stat-box {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 22px;
      border-radius: 10px;
      text-align:center;
      box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .stat-box h2 { margin:0; font-size:44px; font-weight:700; }
    .stat-box p {
      margin-top: 8px;
      font-size: 13px;
      opacity: 0.9;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
    .stat-box.green { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
    .stat-box.red   { background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%); }
    .stat-box.blue  { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }

    .tabs {
      display:flex;
      gap: 10px;
      margin: 10px 0 16px 0;
      flex-wrap: wrap;
    }
    .tab-btn {
      padding: 10px 14px;
      border-radius: 999px;
      border: 2px solid #e0e0e0;
      background: #fff;
      cursor: pointer;
      font-weight: 700;
      font-size: 14px;
      color: #2c3e50;
    }
    .tab-btn.active {
      border-color: #667eea;
      background: rgba(102,126,234,0.12);
    }

    .controls {
      display:flex;
      gap: 12px;
      margin-bottom: 10px;
      flex-wrap: wrap;
      align-items: center;
    }
    #search {
      flex:1;
      min-width: 280px;
      padding: 12px 16px;
      font-size: 16px;
      border: 2px solid #e0e0e0;
      border-radius: 8px;
    }
    #search:focus { outline:none; border-color:#667eea; }

    .btn {
      padding: 12px 18px;
      font-size: 15px;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 700;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }
    .btn:hover { filter: brightness(1.02); transform: translateY(-1px); }

    .showing {
      margin: 8px 0 0 0;
      color: #7f8c8d;
      font-size: 13px;
    }

    table { width:100%; border-collapse: collapse; margin-top: 16px; background:white; }
    th {
      background: #2c3e50;
      color:white;
      padding: 14px;
      text-align:left;
      font-weight:700;
      position: sticky;
      top: 0;
    }
    td { padding: 14px; border-bottom: 1px solid #ecf0f1; vertical-align: top; }
    tr:hover { background: #f8f9fa; }
    .relevant { background: rgba(39,174,96,0.10); }
    .filtered { background: rgba(231,76,60,0.10); opacity: 0.65; }

    a { color:#3498db; text-decoration:none; font-weight:600; }
    a:hover { text-decoration: underline; }

    .badge {
      display:inline-block;
      padding: 4px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
    }
    .badge-success { background:#27ae60; color:white; }
    .badge-danger  { background:#e74c3c; color:white; }

    .source-tag {
      display:inline-block;
      padding: 4px 10px;
      background:#ecf0f1;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 800;
      color:#34495e;
    }
    .article-title { font-size: 16px; font-weight: 800; color:#2c3e50; margin-bottom: 6px; }
    .article-summary { font-size: 14px; color:#7f8c8d; line-height: 1.45; }

    #loading { text-align:center; padding: 34px; font-size: 16px; color:#7f8c8d; }
    .spinner {
      border: 4px solid #f3f3f3;
      border-top: 4px solid #667eea;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      animation: spin 1s linear infinite;
      margin: 18px auto;
    }
    @keyframes spin { 0% {transform:rotate(0deg)} 100% {transform:rotate(360deg)} }
  </style>
</head>

<body>
<div class="container">
  <h1>⚡ Energy-AI Infrastructure Monitor</h1>
  <div class="subtitle">Default view: Relevant-only. Switch to All to see everything (including filtered).</div>

  <div class="stats">
    <div class="stat-box blue"><h2 id="total">0</h2><p>Total Articles</p></div>
    <div class="stat-box green"><h2 id="relevant">0</h2><p>Relevant</p></div>
    <div class="stat-box red"><h2 id="filtered">0</h2><p>Filtered Out</p></div>
    <div class="stat-box"><h2 id="sources">0</h2><p>News Sources</p></div>
  </div>

  <div class="tabs">
    <button class="tab-btn active" id="tab-relevant" onclick="setView('relevant')">✅ Relevant (default)</button>
    <button class="tab-btn" id="tab-all" onclick="setView('all')">📄 All (includes filtered)</button>
  </div>

  <div class="controls">
    <input type="text" id="search" placeholder="🔍 Search within the current tab (title/source/summary/reason)…">
    <button class="btn" onclick="downloadCSV()">📥 Download CSV</button>
    <button class="btn" onclick="location.reload()">🔄 Refresh</button>
  </div>

  <div class="showing" id="showing">Loading…</div>

  <div id="loading"><div class="spinner"></div>Loading articles...</div>

  <table id="articles-table" style="display:none;">
    <thead>
      <tr>
        <th style="width: 20%;">Source</th>
        <th style="width: 45%;">Title & Summary</th>
        <th style="width: 15%;">Published</th>
        <th style="width: 20%;">Status</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>
</div>

<script>
  let currentView = 'relevant';   // default landing view
  let lastData = null;
  let searchQuery = '';

  function downloadCSV() { window.location.href = '/download'; }

  function setView(view) {
    currentView = view;
    document.getElementById('tab-relevant').classList.toggle('active', view === 'relevant');
    document.getElementById('tab-all').classList.toggle('active', view === 'all');
    renderTable();
  }

  function getBaseArticles() {
    if (!lastData) return [];
    if (currentView === 'relevant') {
      return lastData.articles.filter(a => a.relevant === 'True');
    }
    return lastData.articles; // all (includes filtered)
  }

  function renderTable() {
    if (!lastData) return;

    let articles = getBaseArticles();

    if (searchQuery) {
      articles = articles.filter(a => {
        const blob = ((a.title||'') + ' ' + (a.source||'') + ' ' + (a.summary||'') + ' ' + (a.reason||'')).toLowerCase();
        return blob.includes(searchQuery);
      });
    }

    const tbody = document.querySelector('#articles-table tbody');
    tbody.innerHTML = '';

    articles.forEach(article => {
      const isRelevant = article.relevant === 'True';
      const row = tbody.insertRow();
      row.className = isRelevant ? 'relevant' : 'filtered';

      row.innerHTML = `
        <td><span class="source-tag">${article.source || ''}</span></td>
        <td>
          <div class="article-title">
            <a href="${article.link || '#'}" target="_blank" rel="noopener noreferrer">${article.title || ''}</a>
          </div>
          <div class="article-summary">${article.summary || ''}</div>
        </td>
        <td style="font-size: 14px; color: #7f8c8d;">${article.published || ''}</td>
        <td>
          <span class="badge ${isRelevant ? 'badge-success' : 'badge-danger'}">
            ${isRelevant ? '✅ Relevant' : '❌ Filtered'}
          </span>
          <div style="margin-top: 6px; font-size: 12px; color: #7f8c8d;">
            ${article.reason || ''}
          </div>
        </td>
      `;
    });

    const viewLabel = (currentView === 'relevant') ? 'Relevant' : 'All';
    const showingText = `Showing ${articles.length} article(s) — View: ${viewLabel}${searchQuery ? ` — Search: "${searchQuery}"` : ''}`;
    document.getElementById('showing').textContent = showingText;

    document.getElementById('loading').style.display = 'none';
    document.getElementById('articles-table').style.display = 'table';
  }

  function loadArticles() {
    fetch('/api/articles')
      .then(r => r.json())
      .then(data => {
        lastData = data;

        document.getElementById('total').textContent = data.total;
        document.getElementById('relevant').textContent = data.relevant;
        document.getElementById('filtered').textContent = data.total - data.relevant;
        document.getElementById('sources').textContent = data.sources;

        renderTable(); // uses default currentView='relevant'
      })
      .catch(() => {
        document.getElementById('loading').innerHTML =
          '<p style="color:#e74c3c;">❌ Error loading articles. Run mini_prototype.py first.</p>';
      });
  }

  document.getElementById('search').addEventListener('keyup', () => {
    searchQuery = document.getElementById('search').value.toLowerCase().trim();
    renderTable();
  });

  loadArticles();
  setInterval(loadArticles, 300000);
</script>
</body>
</html>
"""

@app.route("/api/articles")
def api_articles():
    articles = load_articles()
    relevant_count = sum(1 for a in articles if a.get("relevant") == "True")
    sources = set(a.get("source", "") for a in articles)
    return jsonify({
        "total": len(articles),
        "relevant": relevant_count,
        "sources": len(sources),
        "articles": articles,
    })

@app.route("/download")
def download():
    csv_file = get_latest_csv()
    if csv_file:
        return send_file(csv_file, as_attachment=True)
    return "No data available", 404

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("⚡ Starting Energy-AI Monitor Dashboard")
    print("=" * 60)
    print("\n📊 Dashboard will open at: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server\n")
    app.run(debug=False, port=5000, host="127.0.0.1")
