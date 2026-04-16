from flask import Flask, render_template_string, request
from collections import Counter
import json
import os

app = Flask(__name__)
DB_FILE = 'movies.json'

def load_movies():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        return []
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
        for m in data:
            if 'status' not in m:
                m['status'] = 'ranked'
            if 'series' not in m:
                m['series'] = ''
            if 'director' not in m:
                m['director'] = ''
            if 'starring' not in m:
                m['starring'] = ''
            if 'synopsis' not in m:
                m['synopsis'] = ''
            if 'watch_count' not in m:
                m['watch_count'] = 1
        return data

@app.route('/')
def index():
    all_movies = load_movies()
    movies = [m for m in all_movies if m.get('status') == 'ranked']
    series_filter = request.args.get('series')

    if series_filter:
        movies = [m for m in movies if m.get('series', '').lower() == series_filter.lower()]

    sort_mode = request.args.get('sort', 'mine')

    total_count = len(movies)
    all_scores = []
    subgenres = []
    for m in movies:
        m['id'] = all_movies.index(m)
        cats = [float(m.get(k, 0)) for k in ['scare', 'atmosphere', 'story', 'acting', 'originality']]
        m['avg'] = round(sum(cats) / 5, 1)
        all_scores.append(m['avg'])

        f_raw_list = m.get('friend_scores', [])
        f_numeric_list = []
        for s in f_raw_list:
            if isinstance(s, dict):
                f_numeric_list.append(float(s.get('score', 0)))
            else:
                f_numeric_list.append(float(s))

        m['friend_avg'] = round(sum(f_numeric_list) / len(f_numeric_list), 1) if f_numeric_list else "—"

        if m.get('subgenre'): subgenres.append(m['subgenre'].strip().title())

    avg_overall = round(sum(all_scores) / total_count, 1) if total_count > 0 else 0
    top_genre = Counter(subgenres).most_common(1)[0][0] if subgenres else "N/A"

    if sort_mode == 'friends':
        ranked_movies = sorted(movies, key=lambda x: (x['friend_avg'] if isinstance(x['friend_avg'], float) else -1), reverse=True)
    else:
        ranked_movies = sorted(movies, key=lambda x: x['avg'], reverse=True)

    top_movie = ranked_movies[0] if ranked_movies else None
    latest_movie = movies[-1] if movies else None

    return render_template_string(HTML_TEMPLATE,
        page="home", movies=ranked_movies, total_count=total_count,
        avg_overall=avg_overall, top_genre=top_genre,
        sort_mode=sort_mode, top_movie=top_movie, latest_movie=latest_movie, series_filter=series_filter)

@app.route('/watchlist')
def watchlist():
    all_movies = load_movies()
    movies = [m for m in all_movies if m.get('status') == 'watchlist']
    series_filter = request.args.get('series')
    if series_filter:
        movies = [m for m in movies if m.get('series', '').lower() == series_filter.lower()]

    for m in movies:
        m['id'] = all_movies.index(m)

    return render_template_string(HTML_TEMPLATE, page="watchlist", movies=movies, series_filter=series_filter)

@app.route('/about')
def about():
    return render_template_string(HTML_TEMPLATE, page="about", movies=[])

# --- SHARED HTML TEMPLATE ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>THE GORE LIST</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
    <style>html { scroll-behavior: smooth; } :root { --friend-bg: rgba(0, 200, 83, 0.1); }</style>
    <style>
        :root { --bg: #0a0a0a; --card: #161616; --accent: #e50914; --friend: #00c853; --text: #ffffff; --sub: #a0a0a0; }
        body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; margin: 0; padding: 0; }
        .container { max-width: 1000px; margin: auto; padding: 40px 20px; }

        .main-nav { display: flex; gap: 30px; margin-bottom: 20px; border-bottom: 1px solid #222; padding-bottom: 15px; }
        .nav-link { text-decoration: none; color: var(--sub); font-weight: 900; text-transform: uppercase; letter-spacing: 1px; }
        .nav-link.active { color: var(--accent); border-bottom: 2px solid var(--accent); padding-bottom: 13px; }

        .search-container { margin-bottom: 25px; }
        #movieSearch {
            width: 100%;
            background: transparent;
            border: none;
            border-bottom: 2px solid #333;
            color: white;
            padding: 10px;
            font-size: 1.1em;
            outline: none;
            transition: border-color 0.3s;
        }
        #movieSearch:focus { border-color: var(--accent); }

        .stats-ribbon { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 30px; }
        .stat-card { background: var(--card); padding: 15px; border-radius: 10px; border: 1px solid #333; text-align: center; }
        .stat-val { display: block; font-size: 1.5em; font-weight: 900; color: var(--accent); }
        .stat-label { font-size: 10px; text-transform: uppercase; color: var(--sub); letter-spacing: 1px; }

        .dashboard-hero { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
        .hero-card {
            background: linear-gradient(145deg, #1a1a1a, #111); border: 1px solid #333; border-radius: 12px;
            padding: 20px; display: flex; gap: 20px; align-items: center; position: relative; overflow: hidden;
            text-decoration: none; color: inherit; transition: border-color 0.2s, transform 0.2s;
        }
        .hero-card:hover { border-color: var(--accent); transform: translateY(-2px); }
        .hero-card::after { content: ''; position: absolute; top: 0; right: 0; width: 100px; height: 100%; background: linear-gradient(90deg, transparent, rgba(229, 9, 20, 0.05)); }
        .hero-poster-mini { width: 70px; height: 100px; object-fit: cover; border-radius: 6px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        .hero-info h4 { margin: 0; font-size: 10px; color: var(--accent); text-transform: uppercase; letter-spacing: 2px; }
        .hero-info h2 { margin: 5px 0; font-size: 1.3em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 250px; }
        .hero-score { font-size: 1.5em; font-weight: 900; color: var(--text); }

        .movie-card { background: var(--card); border-radius: 12px; display: flex; flex-wrap: wrap; margin-bottom: 20px; border: 1px solid #222; overflow: hidden; cursor: pointer; transition: transform 0.2s; align-items: stretch; }
        .movie-card:hover { border-color: #444; }
        .poster { width: 160px; height: 260px; object-fit: cover; }
        .content { padding: 20px; flex: 1; min-width: 300px; position: relative; }
        .card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
        .badge { text-align: center; padding: 4px 8px; border-radius: 6px; min-width: 45px; border: 1px solid; display: inline-block; }

        .series-tag { font-size: 9px; background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 4px; color: var(--sub); text-decoration: none; margin-left: 10px; vertical-align: middle; border: 1px solid #333; transition: 0.2s; font-weight: normal; text-transform: uppercase; }
        .series-tag:hover { background: var(--accent); color: white; border-color: var(--accent); }

        .filter-header { background: rgba(229, 9, 20, 0.1); border: 1px solid var(--accent); padding: 15px; border-radius: 12px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }
        .filter-header a { color: white; text-transform: uppercase; font-size: 10px; font-weight: 900; text-decoration: none; background: var(--accent); padding: 6px 15px; border-radius: 6px; }

        .detail-pane { display: none; width: 100%; background: #0f0f0f; padding: 25px; border-top: 1px solid #222; box-sizing: border-box; }
        .detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
        .detail-title { font-size: 10px; color: var(--accent); font-weight: 900; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; display: block; }
        .score-row { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1px solid #222; }
        .reco-item { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; text-decoration: none; color: white; background: #1a1a1a; padding: 8px; border-radius: 8px; border: 1px solid #333; }
        .reco-item:hover { border-color: var(--accent); }
        .reco-poster { width: 40px; height: 60px; object-fit: cover; border-radius: 4px; }

        .about-section { line-height: 1.6; margin-top: 20px; }
        .about-card { background: var(--card); padding: 20px; border-radius: 12px; border: 1px solid #333; margin-bottom: 20px; }
        .about-card h3 { color: var(--accent); margin-top: 0; text-transform: uppercase; font-size: 1.1em; margin-bottom: 10px; }
        .about-card p { color: #ccc; margin: 0; font-size: 0.9em; }
        .about-header { font-size: 2em; font-weight: 900; color: white; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>THE GORE LIST</h1>
            <nav class="main-nav">
                <a href="/" class="nav-link {{ 'active' if page == 'home' }}">The Rankings</a>
                <a href="/watchlist" class="nav-link {{ 'active' if page == 'watchlist' }}">Watchlist</a>
                <a href="/about" class="nav-link {{ 'active' if page == 'about' }}">About the Scores</a>
            </nav>
        </header>

        {% if page != 'about' %}
        <div class="search-container">
            <input type="text" id="movieSearch" onkeyup="filterMovies()" placeholder="Search by title, year, or subgenre...">
        </div>
        {% endif %}

        {% if series_filter is defined and series_filter %}
        <div class="filter-header">
            <span>Showing the <strong>{{ series_filter }}</strong> collection</span>
            <a href="{{ '/watchlist' if page == 'watchlist' else '/' }}">Clear Filter</a>
        </div>
        {% endif %}

        {% if page == 'home' %}
        <div class="stats-ribbon">
            <div class="stat-card"><span class="stat-val">{{ total_count }}</span><span class="stat-label">Ranked Movies</span></div>
            <div class="stat-card"><span class="stat-val">{{ avg_overall }}</span><span class="stat-label">Avg Master Score</span></div>
            <div class="stat-card"><span class="stat-val">{{ top_genre }}</span><span class="stat-label">Top Genre</span></div>
        </div>

        {% if top_movie %}
        <div class="dashboard-hero">
            <a href="#movie-{{ top_movie.id }}" class="hero-card">
                <img src="{{ top_movie.poster }}" class="hero-poster-mini" onerror="this.src='https://via.placeholder.com/70x100?text=? '">
                <div class="hero-info">
                    <h4>Hall of Fame</h4>
                    <h2>{{ top_movie.title }}</h2>
                    <div class="hero-score">{{ top_movie.avg }} <span style="font-size: 12px; color: var(--sub);">MASTER SCORE</span></div>
                </div>
            </a>
            <a href="#movie-{{ latest_movie.id }}" class="hero-card">
                <img src="{{ latest_movie.poster }}" class="hero-poster-mini" onerror="this.src='https://via.placeholder.com/70x100?text=? '">
                <div class="hero-info">
                    <h4>Latest Entry</h4>
                    <h2>{{ latest_movie.title }}</h2>
                    <div class="hero-score">{{ latest_movie.avg }} <span style="font-size: 12px; color: var(--sub);">MASTER SCORE</span></div>
                </div>
            </a>
        </div>
        {% endif %}
        {% endif %}

        {% if page == 'about' %}
        <div class="about-section">
            <div class="about-header">HOW WE RANK THE GORE</div>
            <p style="color: var(--sub); margin-bottom: 30px;">Every movie is rated on a scale of 0 to 10 across five distinct categories. The average of these scores creates the <strong>Master Score</strong>.</p>

            <div class="about-card">
                <h3>Scare Factor</h3>
                <p>Measures pure fear. This includes the effectiveness of jump scares, psychological dread, and how likely you are to need the lights on after watching.</p>
            </div>
            <div class="about-card">
                <h3>Atmosphere</h3>
                <p>Focuses on the technical "vibes." Sound design, cinematography, lighting, and set pieces that build an immersive world of horror.</p>
            </div>
            <div class="about-card">
                <h3>Story</h3>
                <p>The strength of the narrative. Is the plot cohesive? Are the characters well-developed? Does the pacing keep you engaged or leave you bored?</p>
            </div>
            <div class="about-card">
                <h3>Acting</h3>
                <p>The quality of the performances. Horror often suffers from "cheesy" acting; this score rewards actors who make the terror feel real.</p>
            </div>
            <div class="about-card">
                <h3>Originality</h3>
                <p>How fresh is the concept? Does it subvert tropes and offer something new, or is it another "family moves into a haunted house" clone?</p>
            </div>
        </div>
        {% endif %}

        {% if page != 'about' %}
        <div id="movieGrid">
            {% for movie in movies %}
            <div class="movie-card" id="movie-{{ movie.id }}" onclick="toggleDetails('{{ movie.id }}')">
                <img src="{{ movie.poster }}" class="poster" onerror="this.src='https://via.placeholder.com/160x260?text=No+Poster'">
                <div class="content">
                    <div style="color:var(--sub); font-size: 0.7em; font-weight:900; text-transform: uppercase; letter-spacing: 0.5px;">{{ movie.year }} • {{ movie.subgenre }}</div>
                    <div style="font-size: 1.6em; font-weight: 900; margin: 4px 0 8px 0; line-height: 1.2;">
                        {{ movie.title }}
                        {% if movie.series %}
                        <a href="/?series={{ movie.series }}" class="series-tag" onclick="event.stopPropagation()">{{ movie.series }} Series</a>
                        {% endif %}
                    </div>
                    {% if movie.director %}<div style="font-size: 0.8em; color: var(--sub); margin-top: 5px;">Directed by: {{ movie.director }}</div>{% endif %}
                    {% if movie.starring %}<div style="font-size: 0.8em; color: var(--sub);">Starring: {{ movie.starring }}</div>{% endif %}
                    
                    {% if movie.synopsis %}
                    <p style="font-size: 0.9em; color: #ccc; margin-top: 10px; line-height: 1.4; margin-bottom: 12px;">{{ movie.synopsis }}</p>
                    {% endif %}

                    <div style="display: flex; gap: 15px; align-items: center; margin-top: auto; padding-top: 10px; margin-bottom: 10px;">
                        {% if movie.trailer %}
                        <a href="{{ movie.trailer }}" target="_blank" style="color:var(--accent); font-size:10px; text-decoration:none; font-weight:bold; letter-spacing: 1px;" onclick="event.stopPropagation()">WATCH TRAILER</a>
                        {% endif %}
                        <span style="font-size: 9px; color: var(--sub); font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;">Views: {{ movie.watch_count }}</span>
                    </div>

                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        {% if page == 'home' %}
                        <div style="display: flex; gap: 8px;">
                            <div class="badge" style="color:var(--accent); border-color:var(--accent);"><div style="font-size:1em; font-weight:900;">{{ movie.avg }}</div><div style="font-size:6px;">MASTER</div></div>
                            <div class="badge" style="color:var(--friend); border-color:var(--friend);"><div style="font-size:1em; font-weight:900;">{{ movie.friend_avg }}</div><div style="font-size:6px;">FRIENDS</div></div>
                        </div>
                        {% endif %}
                    </div>
                </div>

                <div class="detail-pane" id="details-{{ movie.id }}" onclick="event.stopPropagation()">
                    <div class="detail-grid">
                        <div>
                            <span class="detail-title">Score Breakdown</span>
                            {% for key, label in [('scare','Scare Factor'), ('atmosphere','Atmosphere'), ('story','Story/Plot'), ('acting','Acting Quality'), ('originality','Originality')] %}
                            <div class="score-row">
                                <span>{{ label }}</span>
                                <span style="font-weight: 900; color: var(--accent);">{{ movie[key] }}</span>
                            </div>
                            {% endfor %}

                            <span class="detail-title" style="margin-top: 20px; color: var(--friend);">Friend Log</span>
                            <div style="display: flex; flex-direction: column; gap: 8px;">
                                {% for s in movie.friend_scores %}
                                <div style="background: var(--friend-bg); border: 1px solid var(--friend); padding: 8px; border-radius: 6px; font-size: 11px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="font-weight: 900; color: var(--friend);">{{ s.name if s is mapping else 'Legacy Score' }}</span>
                                        <span style="background: var(--friend); color: white; padding: 2px 6px; border-radius: 4px; font-weight: 900;">{{ s.score if s is mapping else s }}</span>
                                    </div>
                                    {% if s is mapping and s.date %}
                                    <div style="font-size: 8px; color: var(--sub); text-transform: uppercase; margin-top: 4px;">Added: {{ s.date }}</div>
                                    {% endif %}
                                </div>
                                {% else %}
                                <span style="font-size: 10px; color: var(--sub);">No friend scores yet.</span>
                                {% endfor %}
                            </div>
                        </div>
                        <div>
                            <span class="detail-title">Recommended Based on this</span>
                            <div id="reco-container-{{ movie.id }}">
                                <!-- Populated by JS -->
                            </div>
                        </div>
                    </div>
                    {% if movie.notes %}
                    <div style="margin-top: 25px; border-top: 1px solid #222; padding-top: 20px;">
                        <span class="detail-title">Review & Notes</span>
                        <p style="color:#ccc; font-size: 0.9em; line-height: 1.6; margin: 0; white-space: pre-wrap;">{{ movie.notes }}</p>
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>

    <script>
        const allMovies = {{ movies|tojson }};

        function toggleDetails(id) {
            const pane = document.getElementById('details-' + id);
            const isOpening = pane.style.display !== 'block';

            document.querySelectorAll('.detail-pane').forEach(p => p.style.display = 'none');

            if (isOpening) {
                pane.style.display = 'block';
                loadRecommendations(id);
            }
        }

        function loadRecommendations(movieId) {
            const current = allMovies.find(m => m.id == movieId);
            const container = document.getElementById('reco-container-' + movieId);
            if (!current || !container) return;

            const currentSubs = current.subgenre.toLowerCase().split(',').map(s => s.trim());

            const recos = allMovies
                .filter(m => m.id != movieId && m.status === 'ranked')
                .map(m => {
                    let sim = 0;
                    const mSubs = m.subgenre.toLowerCase().split(',').map(s => s.trim());
                    const matches = currentSubs.filter(s => mSubs.includes(s)).length;
                    sim += matches * 10;
                    sim += (10 - Math.abs(current.avg - m.avg));
                    return { ...m, similarity: sim };
                })
                .sort((a, b) => b.similarity - a.similarity)
                .slice(0, 3);

            container.innerHTML = recos.map(r => `
                <a href="#movie-${r.id}" class="reco-item" onclick="toggleDetails('${r.id}')">
                    <img src="${r.poster}" class="reco-poster" onerror="this.src='https://via.placeholder.com/40x60'">
                    <div style="flex-grow:1">
                        <div style="font-size: 11px; font-weight: 900;">${r.title}</div>
                        <div style="font-size: 9px; color: var(--sub);">${r.subgenre}</div>
                    </div>
                    <div style="font-weight:900; color:var(--accent); font-size:12px;">${r.avg}</div>
                </a>
            `).join('');
        }

        function filterMovies() {
            let input = document.getElementById('movieSearch').value.toLowerCase();
            let cards = document.getElementsByClassName('movie-card');
            for (let card of cards) {
                card.style.display = card.innerText.toLowerCase().includes(input) ? "flex" : "none";
            }
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
