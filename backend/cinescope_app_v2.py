import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import spearmanr, kruskal
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import re
import warnings
warnings.filterwarnings("ignore")

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🎬 CineScope — Movie Intelligence Platform",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  .hero {
    background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 50%, #415a77 100%);
    padding: 2.5rem 2rem; border-radius: 16px;
    margin-bottom: 1.5rem; border: 1px solid #415a77;
  }
  .hero h1 { color: #e0e1dd; font-size: 2.4rem; margin:0; font-weight:800; }
  .hero p  { color: #778da9; font-size: 1rem; margin:0.4rem 0 0; }

  .metric-card {
    background: linear-gradient(135deg, #1b263b, #0d1b2a);
    border: 1px solid #415a77; border-radius: 12px;
    padding: 1.2rem 1.5rem; text-align: center;
  }
  .metric-card .val   { font-size: 2rem; font-weight:700; color: #e0e1dd; }
  .metric-card .lbl   { font-size: 0.78rem; color: #778da9; margin-top: 4px;
                         text-transform:uppercase; letter-spacing:1px; }

  .section-title {
    border-left: 4px solid #415a77; padding-left: 12px;
    font-size: 1.3rem; font-weight: 700; color: #e0e1dd;
    margin: 1.5rem 0 1rem;
  }

  .insight-box {
    background: #1b263b; border: 1px solid #778da9;
    border-radius: 10px; padding: 1rem 1.5rem;
    margin: 0.8rem 0; color: #e0e1dd;
    font-size: 0.93rem; line-height: 1.7;
  }
  .insight-box strong { color: #a8dadc; }

  /* Movie card in search */
  .movie-card {
    background: linear-gradient(160deg, #1b263b 0%, #0d1b2a 100%);
    border: 1px solid #415a77; border-radius: 16px;
    padding: 1.5rem; margin: 0.8rem 0;
  }
  .movie-title  { font-size: 1.6rem; font-weight: 800; color: #e0e1dd; margin-bottom: 4px; }
  .movie-year   { font-size: 0.9rem; color: #778da9; }
  .movie-meta   { display: flex; gap: 10px; flex-wrap: wrap; margin: 10px 0; }
  .badge {
    display: inline-block; padding: 3px 12px;
    border-radius: 20px; font-size: 0.8rem; font-weight: 600;
    border: 1px solid #415a77; color: #a8dadc; background: #0d1b2a;
  }
  .badge-pop  { background:#e63946; color:#fff; border-color:#e63946; }
  .badge-vote { background:#2a9d8f; color:#fff; border-color:#2a9d8f; }
  .overview-text { color:#c9cdd4; font-size:0.95rem; line-height:1.7; margin-top:10px; }

  /* Poster grid */
  .poster-grid { display: flex; flex-wrap: wrap; gap: 16px; padding: 10px 0; }
  .poster-item {
    width: 140px; background: #1b263b; border-radius: 10px;
    overflow: hidden; border: 1px solid #415a77;
    transition: transform 0.2s; cursor: pointer;
  }
  .poster-item:hover { transform: scale(1.04); border-color: #778da9; }
  .poster-item img   { width: 100%; height: 210px; object-fit: cover; }
  .poster-item .info { padding: 8px; font-size: 0.72rem; color: #e0e1dd; }
  .poster-item .info .ptitle { font-weight:600; white-space:nowrap;
                                overflow:hidden; text-overflow:ellipsis; }
  .poster-item .info .pscore { color:#a8dadc; }

  /* Comparison table */
  .compare-table td, .compare-table th {
    padding: 8px 14px; border: 1px solid #415a77; color: #e0e1dd;
  }
  .compare-table th { background: #1b263b; color: #a8dadc; }
  .compare-table tr:nth-child(even) { background: #0d1b2a; }

  footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

PALETTE   = px.colors.qualitative.Vivid
TEMPLATE  = "plotly_dark"

# ─────────────────────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="🎬 Loading and preparing dataset…")
def load_data(path):
    df = pd.read_csv(path, lineterminator='\n')

    df['Release_Date'] = pd.to_datetime(df['Release_Date'], errors='coerce')
    df['Year']   = df['Release_Date'].dt.year.astype('Int64')
    df['Month']  = df['Release_Date'].dt.month
    df['Decade'] = (df['Year'] // 10 * 10).astype('Int64')
    df['Original_Language'] = df['Original_Language'].str.strip().str.upper()
    df['Overview'] = (
        df['Overview']
        .fillna('')
        .astype(str)
        .str.replace('<', '', regex=False)
        .str.replace('>', '', regex=False)
    )

    df['Overview_WC'] = df['Overview'].apply(
        lambda x: len(str(x).split())
    )

    def categorize(series, labels):
        q = series.quantile([0, .25, .5, .75, 1.0]).values
        return pd.cut(series, bins=np.unique(q), labels=labels, include_lowest=True)

    df['Vote_Bucket'] = categorize(df['Vote_Average'],
        ['Not Popular', 'Below Avg', 'Average', 'Popular'])
    df['Pop_Tier'] = categorize(df['Popularity'],
        ['Low', 'Medium', 'High', 'Viral'])

    bins   = [1900, 1980, 1990, 2000, 2010, 2015, 2020, 2030]
    labels = ['Pre-80s', '80s', '90s', '2000s', '2010-14', '2015-19', '2020+']
    df['Era'] = pd.cut(df['Year'].astype(float), bins=bins, labels=labels, right=False)

    df_exp = df.copy()
    df_exp['Genre'] = df_exp['Genre'].str.split(', ')
    df_exp = df_exp.explode('Genre').reset_index(drop=True)
    df_exp['Genre'] = df_exp['Genre'].str.strip()

    return df, df_exp


@st.cache_data(show_spinner=False)
def build_recommender(df):
    """Build a cosine-similarity recommender from genre one-hot + scaled numerics."""
    genres = df['Genre'].str.split(', ')
    all_g  = sorted({g.strip() for gs in genres.dropna() for g in gs})
    rows = []
    for _, row in df.iterrows():
        genre_list = [g.strip() for g in str(row['Genre']).split(', ')]
        vec = [1 if g in genre_list else 0 for g in all_g]
        rows.append(vec)
    genre_mat = np.array(rows, dtype=np.float32)

    num_cols = ['Popularity', 'Vote_Count', 'Vote_Average']
    num_mat  = df[num_cols].fillna(0).values.astype(np.float32)
    scaler   = StandardScaler()
    num_mat  = scaler.fit_transform(num_mat)

    combined = np.hstack([genre_mat * 2, num_mat])
    sim_mat  = cosine_similarity(combined)
    return sim_mat


def get_similar(title, df, sim_mat, n=6):
    matches = df[df['Title'].str.lower() == title.lower()]
    if matches.empty:
        return pd.DataFrame()
    idx = matches.index[0]
    scores = list(enumerate(sim_mat[idx]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)
    top_idx = [i for i, _ in scores[1:n+1]]
    return df.iloc[top_idx]


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎬 CineScope")
    st.markdown("*Movie Intelligence Platform v2*")
    st.divider()

    st.markdown("### 📌 Navigation")
    page = st.radio("Go to", [
        "🏠 Dashboard",
        "🔍 Movie Search & Posters",
        "🎯 Smart Recommender",
        "⚔️ Movie Comparator",
        "📊 Univariate Analysis",
        "🎭 Genre Intelligence",
        "📅 Temporal Trends",
        "🔗 Correlation & Stats",
        "🏆 Leaderboards",
        "📝 Text Mining",
        "🤖 Cluster Analysis",
    ], label_visibility="collapsed")

    st.divider()
    uploaded = st.file_uploader("📁 Upload CSV", type=['csv'])

    if uploaded:
        import io
        raw_df, exp_df = load_data.__wrapped__(io.StringIO(uploaded.read().decode('utf-8')))
    else:
        try:
            raw_df, exp_df = load_data('dataset/mymoviedb.csv')
        except FileNotFoundError:
            st.error("⚠️ Dataset not found. Upload your CSV above.")
            st.stop()

    st.success(f"✅ {len(raw_df):,} movies loaded")
    st.divider()

    st.subheader("🔧 Global Filters")
    year_min, year_max = int(raw_df['Year'].min()), int(raw_df['Year'].max())
    year_range = st.slider("Release Year", year_min, year_max, (1990, year_max))

    all_langs = ['All'] + sorted(raw_df['Original_Language'].dropna().unique().tolist())
    sel_lang  = st.selectbox("Language", all_langs)

    all_genres = sorted(exp_df['Genre'].dropna().unique().tolist())
    sel_genres = st.multiselect("Genre(s)", all_genres, default=[])
    min_votes  = st.slider("Min Vote Count", 0, int(raw_df['Vote_Count'].quantile(0.9)), 0, step=50)


# ── Apply filters ──────────────────────────────────────────────────────────
def apply_filters(df, exp):
    mask = (
        (df['Year'].fillna(0).astype(float) >= year_range[0]) &
        (df['Year'].fillna(0).astype(float) <= year_range[1]) &
        (df['Vote_Count'] >= min_votes)
    )
    if sel_lang != 'All':
        mask &= df['Original_Language'] == sel_lang
    df_f = df[mask].copy()

    mask2 = (
        (exp['Year'].fillna(0).astype(float) >= year_range[0]) &
        (exp['Year'].fillna(0).astype(float) <= year_range[1]) &
        (exp['Vote_Count'] >= min_votes)
    )
    if sel_lang != 'All':
        mask2 &= exp['Original_Language'] == sel_lang
    if sel_genres:
        mask2 &= exp['Genre'].isin(sel_genres)
    return df_f, exp[mask2].copy()

df, exp_df = apply_filters(raw_df, exp_df)

# ─────────────────────────────────────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🎬 CineScope — Movie Intelligence Platform</h1>
  <p>Poster Gallery · Smart Search · AI Recommendations · Deep Analytics · Cluster ML</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
STAR_COLORS = {
    'Popular':     '#2a9d8f',
    'Average':     '#e9c46a',
    'Below Avg':   '#f4a261',
    'Not Popular': '#e76f51',
}

def star_html(score, max_score=10):
    pct = score / max_score * 100
    return f"""
    <div style="display:inline-flex;align-items:center;gap:6px;">
      <div style="background:#1b263b;border-radius:20px;width:120px;height:10px;overflow:hidden;">
        <div style="width:{pct:.0f}%;height:100%;background:linear-gradient(90deg,#e63946,#f4a261,#e9c46a);border-radius:20px;"></div>
      </div>
      <span style="color:#e0e1dd;font-size:0.85rem;font-weight:600;">{score:.1f}/10</span>
    </div>"""

def poster_html(url, title, score, year):
    safe_url = url if pd.notna(url) and str(url).startswith('http') else ""
    img_tag = (f'<img src="{safe_url}" onerror="this.src=\'https://via.placeholder.com/140x210/1b263b/778da9?text=No+Poster\'">'
               if safe_url else
               '<div style="width:140px;height:210px;background:#1b263b;display:flex;align-items:center;justify-content:center;color:#415a77;font-size:0.7rem;">No Poster</div>')
    short_title = title[:18] + '…' if len(title) > 18 else title
    return f"""
    <div class="poster-item">
      {img_tag}
      <div class="info">
        <div class="ptitle" title="{title}">{short_title}</div>
        <div class="pscore">⭐ {score:.1f} · {int(year) if pd.notna(year) else '?'}</div>
      </div>
    </div>"""

def render_poster_grid(subset, max_items=24):
    html = '<div class="poster-grid">'
    for _, row in subset.head(max_items).iterrows():
        html += poster_html(row.get('Poster_Url',''), row['Title'],
                            row['Vote_Average'], row.get('Year', ''))
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def render_movie_card(row):

    with st.container():

        col1, col2 = st.columns([1, 4])

        # LEFT SIDE — POSTER
        with col1:

            poster_url = row.get('Poster_Url', '')

            if pd.notna(poster_url) and str(poster_url).startswith('http'):
                st.image(poster_url, width=130)

            else:
                st.markdown("""
                <div style="
                    width:130px;
                    height:195px;
                    background:#1b263b;
                    border-radius:10px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    color:#778da9;
                    border:1px solid #415a77;
                ">
                    No Poster
                </div>
                """, unsafe_allow_html=True)

        # RIGHT SIDE — DETAILS
        with col2:

            st.markdown(f"## 🎬 {row['Title']}")

            year = (
                int(row['Year'])
                if pd.notna(row.get('Year'))
                else "Unknown"
            )

            st.markdown(
                f"📅 {year} | 🌐 {row.get('Original_Language', '?')}"
            )

            genres = row.get('Genre', 'N/A')

            st.markdown(
                f"**Genres:** {genres}"
            )

            st.markdown(
                f"⭐ **Rating:** {row.get('Vote_Average', 0):.1f}/10"
            )

            st.markdown(
                f"🔥 **Popularity:** {row.get('Popularity', 0):.1f}"
            )

            st.markdown(
                f"🗳️ **Votes:** {int(row.get('Vote_Count', 0)):,}"
            )

            st.markdown("### Overview")

            overview = str(
                row.get(
                    'Overview',
                    'No overview available.'
                )
            )

            st.write(overview)

            st.caption(
                f"Vote Category: {row.get('Vote_Bucket', 'N/A')} | "
                f"Era: {row.get('Era', 'N/A')} | "
                f"Popularity Tier: {row.get('Pop_Tier', 'N/A')}"
            )

        st.divider()


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    c1,c2,c3,c4,c5 = st.columns(5)
    mets = [
        (f"{len(df):,}", "Total Movies"),
        (f"{exp_df['Genre'].nunique()}", "Unique Genres"),
        (f"{df['Vote_Average'].mean():.2f}", "Avg Vote"),
        (f"{df['Popularity'].median():.1f}", "Median Pop."),
        (f"{df['Year'].max()}", "Latest Year"),
    ]
    for col, (val, lbl) in zip([c1,c2,c3,c4,c5], mets):
        col.markdown(f'<div class="metric-card"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>',
                     unsafe_allow_html=True)

    st.markdown('<div class="section-title">📈 Quick Overview</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        yr = df.groupby('Year').size().reset_index(name='Count')
        fig = px.area(yr[yr['Year']>=1990], x='Year', y='Count',
            title='Movies Released per Year', template=TEMPLATE,
            color_discrete_sequence=['#415a77'])
        fig.update_traces(fill='tozeroy', line_color='#778da9')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        top_g = exp_df['Genre'].value_counts().head(10).reset_index()
        top_g.columns = ['Genre','Count']
        fig = px.bar(top_g, x='Count', y='Genre', orientation='h',
            color='Count', color_continuous_scale='Viridis',
            title='Top 10 Genres', template=TEMPLATE)
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        vd = df['Vote_Bucket'].value_counts().reset_index()
        vd.columns = ['Category','Count']
        fig = px.pie(vd, values='Count', names='Category', hole=0.4,
            title='Vote Distribution', color_discrete_sequence=PALETTE, template=TEMPLATE)
        st.plotly_chart(fig, use_container_width=True)
    with col4:
        ld = df['Original_Language'].value_counts().head(8).reset_index()
        ld.columns = ['Language','Count']
        fig = px.bar(ld, x='Language', y='Count', color='Count',
            color_continuous_scale='Plasma', title='Top 8 Languages', template=TEMPLATE)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # Poster strip — top 12 most popular
    st.markdown('<div class="section-title">🎬 Top Popularity Poster Strip</div>', unsafe_allow_html=True)
    top12 = df.nlargest(12, 'Popularity')
    render_poster_grid(top12, max_items=12)

    # Insights
    st.markdown('<div class="section-title">💡 Auto Insights</div>', unsafe_allow_html=True)
    top_movie  = df.loc[df['Popularity'].idxmax(), 'Title'] if len(df) > 0 else 'N/A'
    top_genre  = exp_df['Genre'].value_counts().idxmax() if len(exp_df) > 0 else 'N/A'
    peak_year  = df.groupby('Year').size().idxmax() if len(df) > 0 else 'N/A'
    best_lang  = df.groupby('Original_Language')['Vote_Average'].mean().idxmax()
    st.markdown(f"""
    <div class="insight-box">
    🏆 <strong>Most Popular Movie:</strong> {top_movie}<br>
    🎭 <strong>Most Frequent Genre:</strong> {top_genre}<br>
    📅 <strong>Peak Release Year:</strong> {peak_year}<br>
    🌐 <strong>Best Avg-Rated Language:</strong> {best_lang}<br>
    📊 <strong>Avg Vote Average:</strong> {df['Vote_Average'].mean():.2f}/10 &nbsp;·&nbsp;
       <strong>Max Popularity:</strong> {df['Popularity'].max():.1f}
    </div>
    """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: MOVIE SEARCH & POSTERS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Movie Search & Posters":
    st.markdown('<div class="section-title">🔍 Movie Search & Full Details</div>', unsafe_allow_html=True)

    search_tab, browse_tab = st.tabs(["🔎 Search by Title / Details", "🖼️ Browse Poster Gallery"])

    with search_tab:
        query = st.text_input("🔍 Search movie title, genre, or keyword in overview",
                              placeholder="e.g. Spider-Man, Action, love story…")

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            yr_f = st.slider("Year filter", int(raw_df['Year'].min()), int(raw_df['Year'].max()),
                             (int(raw_df['Year'].min()), int(raw_df['Year'].max())), key='search_yr')
        with col_f2:
            vote_f = st.slider("Min vote average", 0.0, 10.0, 0.0, 0.5, key='search_va')
        with col_f3:
            sort_by = st.selectbox("Sort results by",
                ['Popularity ↓','Vote_Average ↓','Vote_Count ↓','Year ↓','Year ↑'])

        sort_map = {
            'Popularity ↓':  ('Popularity', False),
            'Vote_Average ↓':('Vote_Average',False),
            'Vote_Count ↓':  ('Vote_Count',  False),
            'Year ↓':        ('Year',         False),
            'Year ↑':        ('Year',         True),
        }
        sort_col, sort_asc = sort_map[sort_by]

        if query:
            q = query.lower().strip()
            mask = (
                raw_df['Title'].str.lower().str.contains(q, na=False) |
                raw_df['Genre'].str.lower().str.contains(q, na=False) |
                raw_df['Overview'].fillna('').str.lower().str.contains(q, na=False) |
                raw_df['Original_Language'].str.lower().str.contains(q, na=False)
            )
            results = raw_df[mask].copy()
            results = results[
                (results['Year'].fillna(0).astype(float) >= yr_f[0]) &
                (results['Year'].fillna(0).astype(float) <= yr_f[1]) &
                (results['Vote_Average'] >= vote_f)
            ]
            results = results.sort_values(sort_col, ascending=sort_asc)

            st.markdown(f"<div style='color:#778da9;font-size:0.9rem;margin-bottom:8px;'>"
                        f"Found <strong style='color:#a8dadc;'>{len(results)}</strong> results for "
                        f"<strong style='color:#e0e1dd;'>'{query}'</strong></div>",
                        unsafe_allow_html=True)

            if len(results) == 0:
                st.warning("No movies found. Try a different keyword.")
            else:
                # Show full card for exact/top match
                top_match = results.iloc[0]
                st.markdown("#### 🎯 Best Match")
                render_movie_card(top_match)

                if len(results) > 1:
                    st.markdown(f"#### 📋 All {min(len(results),50)} Results")
                    for _, row in results.head(50).iterrows():
                        with st.expander(f"🎬 {row['Title']}  ({int(row['Year']) if pd.notna(row.get('Year')) else '?'})  ⭐ {row['Vote_Average']:.1f}  🔥 {row['Popularity']:.1f}"):
                            render_movie_card(row)
        else:
            st.info("👆 Type a movie title, genre, or any keyword to search across all 9,000+ movies.")
            # Show random highlights
            st.markdown("#### 🎲 Random Highlights")
            sample = raw_df.sample(4, random_state=np.random.randint(0,999))
            for _, row in sample.iterrows():
                render_movie_card(row)

    with browse_tab:
        st.markdown("#### 🖼️ Poster Gallery Browser")
        b_col1, b_col2, b_col3, b_col4 = st.columns(4)
        with b_col1:
            gallery_genre = st.selectbox("Genre", ['All'] + all_genres, key='gallery_g')
        with b_col2:
            gallery_sort  = st.selectbox("Sort by", ['Popularity','Vote_Average','Vote_Count','Year'], key='gallery_s')
        with b_col3:
            gallery_n = st.slider("Posters to show", 12, 60, 24, step=12, key='gallery_n')
        with b_col4:
            gallery_yr = st.slider("Year range", year_min, year_max, (2000, year_max), key='gallery_yr')

        gallery_df = raw_df[
            (raw_df['Year'].fillna(0).astype(float) >= gallery_yr[0]) &
            (raw_df['Year'].fillna(0).astype(float) <= gallery_yr[1])
        ].copy()
        if gallery_genre != 'All':
            gallery_df = gallery_df[gallery_df['Genre'].str.contains(gallery_genre, na=False)]

        gallery_df = gallery_df.sort_values(gallery_sort, ascending=False)
        render_poster_grid(gallery_df, max_items=gallery_n)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: SMART RECOMMENDER
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🎯 Smart Recommender":
    st.markdown('<div class="section-title">🎯 AI-Powered Movie Recommender</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="insight-box">
    This recommender uses <strong>cosine similarity</strong> on a combined feature vector of
    genre one-hot encoding + scaled popularity, vote count, and vote average.
    It finds movies that are most <em>cinematically similar</em> to the one you select.
    </div>
    """, unsafe_allow_html=True)

    movie_list = sorted(raw_df['Title'].dropna().unique().tolist())
    selected   = st.selectbox("🎬 Pick a movie to get recommendations for", movie_list)

    n_recs = st.slider("Number of recommendations", 4, 12, 6)

    if st.button("🚀 Find Similar Movies", type="primary"):
        with st.spinner("Computing similarities across all movies…"):
            sim_mat = build_recommender(raw_df)
            recs    = get_similar(selected, raw_df, sim_mat, n=n_recs)

        # Show the selected movie
        sel_row = raw_df[raw_df['Title'] == selected].iloc[0]
        st.markdown("#### 📌 You selected:")
        render_movie_card(sel_row)

        st.markdown(f"#### 🎯 {n_recs} Most Similar Movies:")
        for _, row in recs.iterrows():
            render_movie_card(row)

        # Poster grid of recommendations
        st.markdown("#### 🖼️ Recommendation Poster Wall")
        render_poster_grid(recs, max_items=n_recs)

    # ── Mood-based recommender ─────────────────────────────────────────────
    st.divider()
    st.markdown("#### 🎭 Mood-Based Quick Picks")
    mood = st.selectbox("What are you in the mood for?", [
        "😂 Feel-good Comedy",
        "😰 Edge-of-your-seat Thriller",
        "💥 Big Action Blockbuster",
        "😢 Emotional Drama",
        "🚀 Mind-blowing Sci-Fi",
        "👻 Scary Horror",
        "💘 Romantic",
        "🌏 World Cinema (non-English)",
    ])

    mood_map = {
        "😂 Feel-good Comedy":          lambda d: d[d['Genre'].str.contains('Comedy', na=False)],
        "😰 Edge-of-your-seat Thriller": lambda d: d[d['Genre'].str.contains('Thriller', na=False)],
        "💥 Big Action Blockbuster":     lambda d: d[d['Genre'].str.contains('Action', na=False)],
        "😢 Emotional Drama":            lambda d: d[d['Genre'].str.contains('Drama', na=False)],
        "🚀 Mind-blowing Sci-Fi":        lambda d: d[d['Genre'].str.contains('Science Fiction', na=False)],
        "👻 Scary Horror":               lambda d: d[d['Genre'].str.contains('Horror', na=False)],
        "💘 Romantic":                   lambda d: d[d['Genre'].str.contains('Romance', na=False)],
        "🌏 World Cinema (non-English)": lambda d: d[~d['Original_Language'].isin(['EN'])],
    }

    mood_df = mood_map[mood](raw_df)
    mood_top = mood_df[mood_df['Vote_Count'] >= 200].nlargest(8, 'Vote_Average')

    if len(mood_top) > 0:
        st.markdown(f"**Top picks for {mood}:**")
        render_poster_grid(mood_top, max_items=8)
    else:
        st.info("Not enough results for this mood with current filters.")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: MOVIE COMPARATOR
# ═════════════════════════════════════════════════════════════════════════════
elif page == "⚔️ Movie Comparator":
    st.markdown('<div class="section-title">⚔️ Head-to-Head Movie Comparator</div>', unsafe_allow_html=True)
    st.markdown("Compare up to **4 movies** side by side across every metric.")

    movie_list = sorted(raw_df['Title'].dropna().unique().tolist())
    c1, c2, c3, c4 = st.columns(4)
    picks = [
        c1.selectbox("Movie 1", ['(none)']+movie_list, key='c1'),
        c2.selectbox("Movie 2", ['(none)']+movie_list, key='c2'),
        c3.selectbox("Movie 3", ['(none)']+movie_list, key='c3'),
        c4.selectbox("Movie 4", ['(none)']+movie_list, key='c4'),
    ]
    picks = [p for p in picks if p != '(none)']

    if len(picks) < 2:
        st.info("Select at least 2 movies to compare.")
    else:
        comp_rows = [raw_df[raw_df['Title']==p].iloc[0] for p in picks]

        # Poster row
        st.markdown("#### 🖼️ Poster Comparison")
        cols = st.columns(len(picks))
        for col, row in zip(cols, comp_rows):
            poster_url = row.get('Poster_Url','')
            safe_p = poster_url if pd.notna(poster_url) and str(poster_url).startswith('http') else ''
            with col:
                if safe_p:
                    st.image(safe_p, use_container_width=True)
                else:
                    st.markdown(f"<div style='height:220px;background:#1b263b;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#415a77;'>No Poster</div>", unsafe_allow_html=True)
                st.markdown(f"**{row['Title']}**")
                st.caption(f"{'?' if pd.isna(row.get('Year')) else int(row['Year'])}")

        # Stats table
        st.markdown("#### 📊 Stats Table")
        table_data = {}
        for row in comp_rows:
            table_data[row['Title']] = {
                'Year':       int(row['Year']) if pd.notna(row.get('Year')) else '?',
                'Genre':      row.get('Genre','N/A'),
                'Language':   row.get('Original_Language','N/A'),
                'Popularity': f"{row.get('Popularity',0):.2f}",
                'Vote Count': f"{int(row.get('Vote_Count',0)):,}",
                'Vote Avg':   f"{row.get('Vote_Average',0):.2f}/10",
                'Vote Cat.':  str(row.get('Vote_Bucket','N/A')),
                'Era':        str(row.get('Era','N/A')),
                'Pop Tier':   str(row.get('Pop_Tier','N/A')),
                'Overview WC':f"{row.get('Overview_WC',0)} words",
            }
        st.dataframe(pd.DataFrame(table_data), use_container_width=True)

        # Radar comparison
        st.markdown("#### 🕸️ Radar — Multi-Metric Comparison")
        num_metrics = ['Popularity','Vote_Count','Vote_Average']
        fig = go.Figure()
        for row in comp_rows:
            vals_raw = [float(row.get(m, 0)) for m in num_metrics]
            # Normalise relative to dataset max
            vals_norm = [v / raw_df[m].max() for v, m in zip(vals_raw, num_metrics)]
            vals_norm += [vals_norm[0]]
            fig.add_trace(go.Scatterpolar(
                r=vals_norm,
                theta=['Popularity','Vote Count','Vote Avg','Popularity'],
                fill='toself', name=row['Title'], opacity=0.65
            ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0,1])),
            template=TEMPLATE, height=440,
            title='Normalised metric comparison (relative to dataset max)'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Bar side-by-side
        st.markdown("#### 📊 Side-by-Side Bar Charts")
        bar_metric = st.selectbox("Metric", ['Popularity','Vote_Count','Vote_Average'])
        fig = px.bar(
            x=[r['Title'] for r in comp_rows],
            y=[float(r.get(bar_metric,0)) for r in comp_rows],
            color=[r['Title'] for r in comp_rows],
            title=f'{bar_metric} Comparison',
            template=TEMPLATE, color_discrete_sequence=PALETTE,
            labels={'x':'Movie','y':bar_metric}
        )
        st.plotly_chart(fig, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: UNIVARIATE
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📊 Univariate Analysis":
    st.markdown('<div class="section-title">📊 Univariate Analysis</div>', unsafe_allow_html=True)
    col = st.selectbox("Column", ['Popularity','Vote_Count','Vote_Average','Overview_WC'])
    data = df[col].dropna()

    stats_dict = {
        'Count':   f'{len(data):,}', 'Mean':    f'{data.mean():.2f}',
        'Std Dev': f'{data.std():.2f}', 'Min':  f'{data.min():.2f}',
        '25%':     f'{data.quantile(0.25):.2f}', 'Median': f'{data.median():.2f}',
        '75%':     f'{data.quantile(0.75):.2f}', 'Max':    f'{data.max():.2f}',
        'Skewness':f'{data.skew():.3f}', 'Kurtosis':f'{data.kurtosis():.3f}',
    }
    sc = st.columns(5)
    for i,(k,v) in enumerate(stats_dict.items()): sc[i%5].metric(k,v)

    c1,c2 = st.columns(2)
    with c1:
        fig = px.histogram(df, x=col, nbins=60, marginal='box',
            title=f'Histogram + Box — {col}', template=TEMPLATE,
            color_discrete_sequence=['#415a77'])
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.violin(df.dropna(subset=['Vote_Bucket']), y=col, x='Vote_Bucket',
            box=True, points='outliers', color='Vote_Bucket',
            title=f'{col} by Vote Category', template=TEMPLATE,
            color_discrete_sequence=PALETTE)
        st.plotly_chart(fig, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: GENRE INTELLIGENCE
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🎭 Genre Intelligence":
    st.markdown('<div class="section-title">🎭 Genre Intelligence</div>', unsafe_allow_html=True)
    tab1,tab2,tab3,tab4 = st.tabs(["📊 Frequency","📈 Performance","🌳 Treemap","🕸️ Radar"])

    genre_stats = exp_df.groupby('Genre').agg(
        Count=('Title','nunique'), Avg_Pop=('Popularity','mean'),
        Avg_Vote=('Vote_Average','mean'), Avg_VoteCount=('Vote_Count','mean'),
    ).reset_index().sort_values('Count', ascending=False)

    with tab1:
        n = st.slider("Top N genres", 5, len(genre_stats), 20)
        fig = px.bar(genre_stats.head(n), x='Count', y='Genre', orientation='h',
            color='Count', color_continuous_scale='Turbo',
            title=f'Top {n} Genres', template=TEMPLATE)
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=600)
        st.plotly_chart(fig, use_container_width=True)

        # Poster wall for selected genre
        sel_g_poster = st.selectbox("🖼️ Show poster wall for genre", all_genres, key='genre_poster')
        genre_poster_df = raw_df[raw_df['Genre'].str.contains(sel_g_poster, na=False)].nlargest(16,'Popularity')
        render_poster_grid(genre_poster_df, max_items=16)

    with tab2:
        metric = st.selectbox("Metric", ['Avg_Pop','Avg_Vote','Avg_VoteCount'],
            format_func=lambda x: {'Avg_Pop':'Avg Popularity','Avg_Vote':'Avg Vote','Avg_VoteCount':'Avg Vote Count'}[x])
        sorted_gs = genre_stats.sort_values(metric, ascending=False).head(20)
        fig = px.bar(sorted_gs, x='Genre', y=metric, color=metric,
            color_continuous_scale='RdYlGn', template=TEMPLATE,
            title=f'Top 20 Genres — {metric}')
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        tree = exp_df.dropna(subset=['Vote_Bucket']).groupby(['Genre','Vote_Bucket']).size().reset_index(name='Count')
        fig = px.treemap(tree, path=['Genre','Vote_Bucket'], values='Count',
            color='Count', color_continuous_scale='RdYlGn',
            title='Genre × Vote Category Treemap', template=TEMPLATE)
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        top8 = genre_stats.head(8).copy()
        for c in ['Avg_Pop','Avg_Vote','Avg_VoteCount']:
            mn,mx = top8[c].min(), top8[c].max()
            top8[c+'_n'] = (top8[c]-mn)/(mx-mn+1e-9)
        fig = go.Figure()
        for _, row in top8.iterrows():
            vals = [row[m+'_n'] for m in ['Avg_Pop','Avg_Vote','Avg_VoteCount']] + [row['Avg_Pop_n']]
            fig.add_trace(go.Scatterpolar(r=vals,
                theta=['Popularity','Vote Score','Vote Volume','Popularity'],
                fill='toself', name=row['Genre'], opacity=0.6))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,1])),
            title='Radar: Top 8 Genres', template=TEMPLATE, height=520)
        st.plotly_chart(fig, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: TEMPORAL TRENDS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📅 Temporal Trends":
    st.markdown('<div class="section-title">📅 Temporal Trends</div>', unsafe_allow_html=True)
    tab1,tab2,tab3 = st.tabs(["📈 Volume","🎭 Genre Trends","🗓️ Monthly Heatmap"])

    with tab1:
        yr  = df.groupby('Year').size().reset_index(name='Count')
        yr_avg = df.groupby('Year').agg(Avg_Vote=('Vote_Average','mean'),Avg_Pop=('Popularity','mean')).reset_index()
        fig = make_subplots(rows=2,cols=1,shared_xaxes=True,
            subplot_titles=('Movies per Year','Avg Vote & Popularity'))
        fig.add_trace(go.Bar(x=yr['Year'],y=yr['Count'],name='Count',marker_color='#415a77'),row=1,col=1)
        fig.add_trace(go.Scatter(x=yr_avg['Year'],y=yr_avg['Avg_Vote'],name='Avg Vote',line=dict(color='#e63946')),row=2,col=1)
        fig.add_trace(go.Scatter(x=yr_avg['Year'],y=yr_avg['Avg_Pop'],name='Avg Pop',line=dict(color='#a8dadc',dash='dot')),row=2,col=1)
        fig.update_layout(template=TEMPLATE,height=600)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        top_genres = exp_df['Genre'].value_counts().head(8).index.tolist()
        dec_g = exp_df[exp_df['Genre'].isin(top_genres)].groupby(['Decade','Genre']).size().reset_index(name='Count')
        fig = px.bar(dec_g[dec_g['Decade']>=1980], x='Decade', y='Count', color='Genre',
            barmode='group', title='Top Genres per Decade', template=TEMPLATE,
            color_discrete_sequence=PALETTE)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        hm = df.groupby(['Year','Month']).size().reset_index(name='Count')
        hm = hm[hm['Year']>=1990]
        hm_pivot = hm.pivot(index='Year', columns='Month', values='Count').fillna(0)
        month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        hm_pivot.columns = [month_names[m-1] for m in hm_pivot.columns]
        fig = px.imshow(hm_pivot, aspect='auto', color_continuous_scale='YlOrRd',
            title='Monthly Release Heatmap', template=TEMPLATE)
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: CORRELATION & STATS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🔗 Correlation & Stats":
    st.markdown('<div class="section-title">🔗 Correlation & Statistical Testing</div>', unsafe_allow_html=True)
    num_data = df[['Popularity','Vote_Count','Vote_Average']].dropna()
    corr = num_data.corr(method='spearman')

    c1,c2 = st.columns(2)
    with c1:
        fig = px.imshow(corr, text_auto='.3f', color_continuous_scale='RdBu_r',
            title='Spearman Correlation Matrix', template=TEMPLATE, zmin=-1, zmax=1)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.scatter(df.sample(min(3000,len(df)), random_state=42),
            x='Vote_Count', y='Popularity', color='Vote_Bucket',
            size='Vote_Average', hover_data=['Title'],
            title='Popularity vs Vote Count', template=TEMPLATE,
            color_discrete_sequence=PALETTE, opacity=0.6)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Spearman Pairwise p-values")
    cols_s = ['Popularity','Vote_Count','Vote_Average']
    results = []
    for i in range(len(cols_s)):
        for j in range(i+1,len(cols_s)):
            r,p = spearmanr(num_data[cols_s[i]], num_data[cols_s[j]])
            results.append({'Pair':f'{cols_s[i]} ↔ {cols_s[j]}',
                'r':round(r,4),'p-value':f'{p:.2e}',
                'Sig':'***' if p<0.001 else '**' if p<0.01 else '*' if p<0.05 else 'ns'})
    st.dataframe(pd.DataFrame(results), use_container_width=True)

    top10g = exp_df['Genre'].value_counts().head(10).index.tolist()
    groups = [exp_df[exp_df['Genre']==g]['Popularity'].dropna().values for g in top10g]
    H,p = kruskal(*groups)
    st.markdown(f"""<div class="insight-box">
    <strong>Kruskal-Wallis H:</strong> {H:.2f} &nbsp;|&nbsp;
    <strong>p-value:</strong> {p:.2e} &nbsp;|&nbsp;
    <strong>Result:</strong> {'✅ Significant' if p<0.05 else '❌ Not Significant'} (α=0.05)
    </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: LEADERBOARDS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🏆 Leaderboards":
    st.markdown('<div class="section-title">🏆 Leaderboards</div>', unsafe_allow_html=True)
    tab1,tab2,tab3 = st.tabs(["🔥 Most Popular","⭐ Best Rated","🌍 Language Leaders"])

    with tab1:
        n = st.slider("Top N",5,50,20,key='lp')
        top_pop = df.nlargest(n,'Popularity')
        fig = px.bar(top_pop, x='Popularity', y='Title', orientation='h',
            color='Vote_Average', color_continuous_scale='RdYlGn',
            title=f'Top {n} by Popularity', template=TEMPLATE)
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=max(400,n*22))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("#### 🖼️ Poster Wall")
        render_poster_grid(top_pop, max_items=20)

    with tab2:
        min_v = st.slider("Min votes",100,5000,500,step=100)
        credible = df[df['Vote_Count']>=min_v].copy()
        credible['Score'] = credible['Vote_Average'] * np.log1p(credible['Vote_Count'])
        top_rated = credible.nlargest(20,'Score')
        fig = px.scatter(top_rated, x='Vote_Count', y='Vote_Average',
            size='Score', color='Score', hover_data=['Title','Year'],
            color_continuous_scale='Viridis',
            title=f'Best Rated (≥{min_v} votes)', template=TEMPLATE)
        st.plotly_chart(fig, use_container_width=True)
        render_poster_grid(top_rated, max_items=20)

    with tab3:
        lang_perf = df.groupby('Original_Language').agg(
            Count=('Title','count'), Avg_Vote=('Vote_Average','mean'),
            Avg_Pop=('Popularity','mean'), Total_Votes=('Vote_Count','sum')
        ).reset_index().sort_values('Count',ascending=False).head(20)
        fig = px.scatter(lang_perf, x='Count', y='Avg_Vote',
            size='Total_Votes', color='Avg_Pop',
            text='Original_Language', hover_data=['Original_Language'],
            color_continuous_scale='Plasma',
            title='Language: Volume vs Quality', template=TEMPLATE)
        fig.update_traces(textposition='top center')
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: TEXT MINING
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📝 Text Mining":
    st.markdown('<div class="section-title">📝 Overview Text Mining</div>', unsafe_allow_html=True)
    STOPWORDS = {'the','a','an','in','of','to','and','is','are','he','she','his','her',
        'they','their','with','on','for','as','at','but','from','by','was','it','be',
        'this','that','have','has','who','when','after','into','its','not','or','about',
        'one','two','him','them','also','all','which','will','been','more','new'}

    all_text = ' '.join(df['Overview'].dropna().str.lower().values)
    words = re.findall(r'\b[a-z]{4,}\b', all_text)
    filtered = [w for w in words if w not in STOPWORDS]
    freq = Counter(filtered)
    top_n = st.slider("Top N words",10,100,30)
    top_words = pd.DataFrame(freq.most_common(top_n), columns=['Word','Frequency'])

    fig = px.bar(top_words, x='Frequency', y='Word', orientation='h',
        color='Frequency', color_continuous_scale='Cividis',
        title=f'Top {top_n} Overview Words', template=TEMPLATE)
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=600)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(top_words, use_container_width=True)

    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        wc_col = st.color_picker("Background color","#0d1b2a")
        wc = WordCloud(width=1200,height=500,background_color=wc_col,
            colormap='plasma',max_words=150,collocations=False).generate(' '.join(filtered))
        fig_wc,ax = plt.subplots(figsize=(16,6))
        ax.imshow(wc, interpolation='bilinear'); ax.axis('off')
        fig_wc.patch.set_facecolor(wc_col)
        st.pyplot(fig_wc)
    except ImportError:
        st.info("Install `wordcloud` to see the word cloud.")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: CLUSTER ANALYSIS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🤖 Cluster Analysis":
    st.markdown('<div class="section-title">🤖 K-Means Cluster Analysis</div>', unsafe_allow_html=True)
    clust_input = df[['Popularity','Vote_Count','Vote_Average']].dropna()
    scaler = StandardScaler()
    X = scaler.fit_transform(clust_input)

    k = st.slider("Number of Clusters (K)", 2, 10, 4)

    if st.checkbox("Run Elbow + Silhouette", value=True):
        with st.spinner("Computing…"):
            inertias,silhs = [],[]
            for ki in range(2,9):
                km = KMeans(n_clusters=ki, random_state=42, n_init=10)
                lbl = km.fit_predict(X)
                inertias.append(km.inertia_)
                silhs.append(silhouette_score(X,lbl))
        fig = make_subplots(rows=1,cols=2,subplot_titles=('Elbow','Silhouette'))
        fig.add_trace(go.Scatter(x=list(range(2,9)),y=inertias,mode='lines+markers',
            line=dict(color='#e63946'),name='Inertia'),row=1,col=1)
        fig.add_trace(go.Scatter(x=list(range(2,9)),y=silhs,mode='lines+markers',
            line=dict(color='#2a9d8f'),name='Silhouette'),row=1,col=2)
        fig.update_layout(template=TEMPLATE,height=360)
        st.plotly_chart(fig, use_container_width=True)
        best_k = list(range(2,9))[silhs.index(max(silhs))]
        st.info(f"🔍 Best K by Silhouette: **{best_k}**")

    km_final = KMeans(n_clusters=k, random_state=42, n_init=10)
    clust_labels = km_final.fit_predict(X)
    clust_df = clust_input.copy()
    clust_df['Cluster'] = clust_labels.astype(str)
    clust_df['Title'] = df.loc[clust_input.index,'Title'].values

    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X)
    clust_df['PC1'] = coords[:,0]; clust_df['PC2'] = coords[:,1]

    fig = px.scatter(clust_df.sample(min(3000,len(clust_df)),random_state=42),
        x='PC1', y='PC2', color='Cluster',
        hover_data=['Title','Popularity','Vote_Average'],
        title=f'K={k} Clusters — PCA Projection', template=TEMPLATE,
        color_discrete_sequence=PALETTE, opacity=0.7)
    fig.update_layout(height=520)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Cluster Profiles")
    st.dataframe(clust_df.groupby('Cluster')[['Popularity','Vote_Count','Vote_Average']].mean().round(2),
                 use_container_width=True)

    # Show poster wall per cluster
    st.markdown("#### 🖼️ Poster Wall by Cluster")
    sel_cluster = st.selectbox("Select cluster", sorted(clust_df['Cluster'].unique()))
    cluster_titles = clust_df[clust_df['Cluster']==sel_cluster]['Title'].tolist()
    cluster_movies = raw_df[raw_df['Title'].isin(cluster_titles)].nlargest(16,'Popularity')
    render_poster_grid(cluster_movies, max_items=16)


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center;color:#415a77;font-size:0.82rem;padding:1rem 0'>
  🎬 CineScope v2 &nbsp;|&nbsp; Poster Gallery · Smart Search · AI Recommender · Movie Comparator · Deep Analytics
  &nbsp;|&nbsp; Python · Streamlit · Plotly · Scikit-learn
</div>
""", unsafe_allow_html=True)