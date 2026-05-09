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
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* Dark hero header */
  .hero {
    background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 50%, #415a77 100%);
    padding: 2.5rem 2rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    border: 1px solid #415a77;
  }
  .hero h1 { color: #e0e1dd; font-size: 2.4rem; margin:0; font-weight:700; }
  .hero p  { color: #778da9; font-size: 1rem; margin:0.4rem 0 0; }

  /* Metric cards */
  .metric-card {
    background: linear-gradient(135deg, #1b263b, #0d1b2a);
    border: 1px solid #415a77;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    text-align: center;
  }
  .metric-card .val  { font-size: 2rem; font-weight:700; color: #e0e1dd; }
  .metric-card .lbl  { font-size: 0.8rem; color: #778da9; margin-top: 4px; text-transform:uppercase; letter-spacing:1px; }
  .metric-card .delta{ font-size: 0.85rem; color: #a8dadc; }

  /* Section headers */
  .section-title {
    border-left: 4px solid #415a77;
    padding-left: 12px;
    font-size: 1.3rem;
    font-weight: 700;
    color: #e0e1dd;
    margin: 1.5rem 0 1rem;
  }

  /* Insight box */
  .insight-box {
    background: #1b263b;
    border: 1px solid #778da9;
    border-radius: 10px;
    padding: 1rem 1.5rem;
    margin: 0.8rem 0;
    color: #e0e1dd;
    font-size: 0.93rem;
    line-height: 1.6;
  }
  .insight-box strong { color: #a8dadc; }

  /* Hide default Streamlit footer */
  footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

PALETTE = px.colors.qualitative.Vivid
TEMPLATE = "plotly_dark"

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING & CACHING
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading and preparing dataset…")
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, lineterminator='\n')
    df['Release_Date'] = pd.to_datetime(df['Release_Date'], errors='coerce')
    df['Year']   = df['Release_Date'].dt.year.astype('Int64')
    df['Month']  = df['Release_Date'].dt.month
    df['Decade'] = (df['Year'] // 10 * 10).astype('Int64')
    df['Original_Language'] = df['Original_Language'].str.strip().str.upper()
    df['Overview_WC'] = df['Overview'].fillna('').apply(lambda x: len(str(x).split()))

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

    # Exploded version
    df_exp = df.copy()
    df_exp['Genre'] = df_exp['Genre'].str.split(', ')
    df_exp = df_exp.explode('Genre').reset_index(drop=True)
    df_exp['Genre'] = df_exp['Genre'].str.strip()

    return df, df_exp


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎬 CineScope")
    st.markdown("*Movie Intelligence Platform*")
    st.divider()

    uploaded = st.file_uploader("📁 Upload your CSV", type=['csv'])
    st.caption("Expected columns: Release_Date, Title, Overview, Popularity, Vote_Count, Vote_Average, Original_Language, Genre, Poster_Url")

    st.divider()

    if uploaded:
        import io
        raw_df, exp_df = load_data.__wrapped__(io.StringIO(uploaded.read().decode('utf-8')))
    else:
        try:
            raw_df, exp_df = load_data('dataset/mymoviedb.csv')
        except FileNotFoundError:
            st.error("⚠️ Dataset not found. Please upload your CSV above.")
            st.stop()

    st.success(f"✅ {len(raw_df):,} movies loaded")

    # ── Global Filters ────────────────────────────────────────────────────────
    st.subheader("🔧 Global Filters")

    year_min, year_max = int(raw_df['Year'].min()), int(raw_df['Year'].max())
    year_range = st.slider("Release Year Range", year_min, year_max, (1990, year_max))

    all_langs = ['All'] + sorted(raw_df['Original_Language'].dropna().unique().tolist())
    sel_lang = st.selectbox("Language", all_langs)

    all_genres = sorted(exp_df['Genre'].dropna().unique().tolist())
    sel_genres = st.multiselect("Genre(s)", all_genres, default=[])

    min_votes = st.slider("Minimum Vote Count", 0, int(raw_df['Vote_Count'].quantile(0.9)), 0, step=50)

    st.divider()
    st.markdown("### 📌 Navigation")
    page = st.radio("Go to", [
        "🏠 Dashboard",
        "📊 Univariate Analysis",
        "🎭 Genre Intelligence",
        "📅 Temporal Trends",
        "🔗 Correlation & Stats",
        "🏆 Leaderboards",
        "📝 Text Mining",
        "🤖 Cluster Analysis",
    ], label_visibility="collapsed")

# ── Apply filters ─────────────────────────────────────────────────────────────
def apply_filters(df, exp):
    mask = (df['Year'].fillna(0).astype(float) >= year_range[0]) & \
           (df['Year'].fillna(0).astype(float) <= year_range[1]) & \
           (df['Vote_Count'] >= min_votes)
    if sel_lang != 'All':
        mask &= df['Original_Language'] == sel_lang
    df_f = df[mask].copy()

    mask2 = (exp['Year'].fillna(0).astype(float) >= year_range[0]) & \
            (exp['Year'].fillna(0).astype(float) <= year_range[1]) & \
            (exp['Vote_Count'] >= min_votes)
    if sel_lang != 'All':
        mask2 &= exp['Original_Language'] == sel_lang
    if sel_genres:
        mask2 &= exp['Genre'].isin(sel_genres)
    exp_f = exp[mask2].copy()
    return df_f, exp_f

df, exp_df = apply_filters(raw_df, exp_df)

# ─────────────────────────────────────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🎬 CineScope — Movie Intelligence Platform</h1>
  <p>Advanced analytics · Deep visualizations · Statistical insights · Machine Learning</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
if page == "🏠 Dashboard":
    c1, c2, c3, c4, c5 = st.columns(5)
    metrics = [
        (f"{len(df):,}", "Total Movies", ""),
        (f"{exp_df['Genre'].nunique()}", "Unique Genres", ""),
        (f"{df['Vote_Average'].mean():.2f}", "Avg Vote", ""),
        (f"{df['Popularity'].median():.1f}", "Median Popularity", ""),
        (f"{df['Year'].max()}", "Latest Year", ""),
    ]
    for col, (val, lbl, delta) in zip([c1,c2,c3,c4,c5], metrics):
        col.markdown(f"""
        <div class="metric-card">
          <div class="val">{val}</div>
          <div class="lbl">{lbl}</div>
          <div class="delta">{delta}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-title">📈 Quick Overview</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        yr = df.groupby('Year').size().reset_index(name='Count')
        fig = px.area(yr[yr['Year']>=1990], x='Year', y='Count',
            title='Movies Released per Year', template=TEMPLATE,
            color_discrete_sequence=['#415a77'],
            labels={'Count':'Movie Count'})
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
        vote_dist = df['Vote_Bucket'].value_counts().reset_index()
        vote_dist.columns = ['Category','Count']
        fig = px.pie(vote_dist, values='Count', names='Category',
            hole=0.4, title='Vote Category Distribution',
            color_discrete_sequence=PALETTE, template=TEMPLATE)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        lang_dist = df['Original_Language'].value_counts().head(8).reset_index()
        lang_dist.columns = ['Language','Count']
        fig = px.bar(lang_dist, x='Language', y='Count',
            color='Count', color_continuous_scale='Plasma',
            title='Top 8 Languages', template=TEMPLATE)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-title">💡 Quick Insights</div>', unsafe_allow_html=True)
    top_movie = df.loc[df['Popularity'].idxmax(), 'Title'] if len(df) > 0 else 'N/A'
    top_genre = exp_df['Genre'].value_counts().idxmax() if len(exp_df) > 0 else 'N/A'
    peak_year = df.groupby('Year').size().idxmax() if len(df) > 0 else 'N/A'

    st.markdown(f"""
    <div class="insight-box">
    🏆 <strong>Most Popular Movie:</strong> {top_movie}<br>
    🎭 <strong>Most Frequent Genre:</strong> {top_genre}<br>
    📅 <strong>Peak Release Year:</strong> {peak_year}<br>
    📊 <strong>Avg Vote Average:</strong> {df['Vote_Average'].mean():.2f} / 10<br>
    🔥 <strong>Top Popularity Score:</strong> {df['Popularity'].max():.1f}
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: UNIVARIATE
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📊 Univariate Analysis":
    st.markdown('<div class="section-title">📊 Univariate Analysis</div>', unsafe_allow_html=True)

    col = st.selectbox("Select column to analyse", ['Popularity','Vote_Count','Vote_Average','Overview_WC'])

    data = df[col].dropna()
    stats_dict = {
        'Count':   f'{len(data):,}',
        'Mean':    f'{data.mean():.2f}',
        'Std Dev': f'{data.std():.2f}',
        'Min':     f'{data.min():.2f}',
        '25%':     f'{data.quantile(0.25):.2f}',
        'Median':  f'{data.median():.2f}',
        '75%':     f'{data.quantile(0.75):.2f}',
        'Max':     f'{data.max():.2f}',
        'Skewness':f'{data.skew():.3f}',
        'Kurtosis':f'{data.kurtosis():.3f}',
    }
    cols_s = st.columns(5)
    for i, (k, v) in enumerate(stats_dict.items()):
        cols_s[i % 5].metric(k, v)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(df, x=col, nbins=60, marginal='box',
            title=f'Histogram + Box — {col}',
            template=TEMPLATE, color_discrete_sequence=['#415a77'])
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.violin(df.dropna(subset=['Vote_Bucket']), y=col, x='Vote_Bucket',
            box=True, points='outliers', color='Vote_Bucket',
            title=f'{col} by Vote Category',
            template=TEMPLATE, color_discrete_sequence=PALETTE)
        st.plotly_chart(fig, use_container_width=True)

    # Log scale toggle
    log_x = st.checkbox("Log scale X-axis")
    fig = px.histogram(df, x=col, nbins=80,
        title=f'{col} Distribution ({"log" if log_x else "linear"} scale)',
        template=TEMPLATE, color_discrete_sequence=['#e63946'],
        log_x=log_x)
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: GENRE INTELLIGENCE
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🎭 Genre Intelligence":
    st.markdown('<div class="section-title">🎭 Genre Intelligence</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Frequency", "📈 Performance", "🌳 Treemap", "🕸️ Radar"])

    genre_stats = exp_df.groupby('Genre').agg(
        Count=('Title','nunique'),
        Avg_Pop=('Popularity','mean'),
        Avg_Vote=('Vote_Average','mean'),
        Avg_VoteCount=('Vote_Count','mean'),
    ).reset_index().sort_values('Count', ascending=False)

    with tab1:
        n = st.slider("Top N genres", 5, len(genre_stats), 20)
        top_n = genre_stats.head(n)
        fig = px.bar(top_n, x='Count', y='Genre', orientation='h',
            color='Count', color_continuous_scale='Turbo',
            title=f'Top {n} Genres by Movie Count',
            template=TEMPLATE)
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=600)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        metric = st.selectbox("Metric", ['Avg_Pop','Avg_Vote','Avg_VoteCount'],
            format_func=lambda x: {'Avg_Pop':'Avg Popularity','Avg_Vote':'Avg Vote','Avg_VoteCount':'Avg Vote Count'}[x])
        sorted_gs = genre_stats.sort_values(metric, ascending=False).head(20)
        fig = px.bar(sorted_gs, x='Genre', y=metric,
            color=metric, color_continuous_scale='RdYlGn',
            title=f'Top 20 Genres — {metric}', template=TEMPLATE)
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
            mn, mx = top8[c].min(), top8[c].max()
            top8[c+'_n'] = (top8[c] - mn) / (mx - mn + 1e-9)

        metrics_r = ['Avg_Pop_n','Avg_Vote_n','Avg_VoteCount_n']
        labels_r  = ['Popularity','Vote Score','Vote Volume']

        fig = go.Figure()
        for _, row in top8.iterrows():
            vals = [row[m] for m in metrics_r] + [row[metrics_r[0]]]
            fig.add_trace(go.Scatterpolar(
                r=vals, theta=labels_r+[labels_r[0]],
                fill='toself', name=row['Genre'], opacity=0.6))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0,1])),
            title='Radar: Top 8 Genres across Metrics',
            template=TEMPLATE, height=520)
        st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: TEMPORAL TRENDS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📅 Temporal Trends":
    st.markdown('<div class="section-title">📅 Temporal Trends</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📈 Volume Over Time", "🎭 Genre Trends", "🗓️ Monthly Patterns"])

    with tab1:
        yr = df.groupby('Year').size().reset_index(name='Count')
        yr_avg = df.groupby('Year').agg(Avg_Vote=('Vote_Average','mean'), Avg_Pop=('Popularity','mean')).reset_index()

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
            subplot_titles=('Movies per Year','Avg Vote & Popularity per Year'))
        fig.add_trace(go.Bar(x=yr['Year'], y=yr['Count'], name='Count',
            marker_color='#415a77'), row=1, col=1)
        fig.add_trace(go.Scatter(x=yr_avg['Year'], y=yr_avg['Avg_Vote'],
            name='Avg Vote', line=dict(color='#e63946')), row=2, col=1)
        fig.add_trace(go.Scatter(x=yr_avg['Year'], y=yr_avg['Avg_Pop'],
            name='Avg Popularity', line=dict(color='#a8dadc', dash='dot')), row=2, col=1)
        fig.update_layout(template=TEMPLATE, height=600, title='Temporal Movie Metrics')
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        top_genres = exp_df['Genre'].value_counts().head(8).index.tolist()
        dec_g = exp_df[exp_df['Genre'].isin(top_genres)].groupby(
            ['Decade','Genre']).size().reset_index(name='Count')
        dec_g = dec_g[dec_g['Decade']>=1980]
        fig = px.bar(dec_g, x='Decade', y='Count', color='Genre', barmode='group',
            title='Top Genres per Decade', template=TEMPLATE,
            color_discrete_sequence=PALETTE)
        fig.update_layout(height=480)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        hm = df.groupby(['Year','Month']).size().reset_index(name='Count')
        hm = hm[hm['Year'] >= 1990]
        hm_pivot = hm.pivot(index='Year', columns='Month', values='Count').fillna(0)

        import plotly.figure_factory as ff
        month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        hm_pivot.columns = [month_names[m-1] for m in hm_pivot.columns]

        fig = px.imshow(hm_pivot, aspect='auto',
            color_continuous_scale='YlOrRd',
            title='Monthly Release Heatmap (Year × Month)',
            template=TEMPLATE, labels=dict(color='Movies'))
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: CORRELATION & STATS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🔗 Correlation & Stats":
    st.markdown('<div class="section-title">🔗 Correlation & Statistical Testing</div>', unsafe_allow_html=True)

    num_data = df[['Popularity','Vote_Count','Vote_Average']].dropna()
    corr = num_data.corr(method='spearman')

    c1, c2 = st.columns(2)
    with c1:
        fig = px.imshow(corr, text_auto='.3f', color_continuous_scale='RdBu_r',
            title='Spearman Correlation Matrix', template=TEMPLATE,
            zmin=-1, zmax=1)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.scatter(df.sample(min(3000,len(df)), random_state=42),
            x='Vote_Count', y='Popularity', color='Vote_Bucket',
            size='Vote_Average', hover_data=['Title'],
            title='Popularity vs Vote Count', template=TEMPLATE,
            color_discrete_sequence=PALETTE, opacity=0.6)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Spearman Pairwise p-values")
    cols_stat = ['Popularity','Vote_Count','Vote_Average']
    results = []
    for i in range(len(cols_stat)):
        for j in range(i+1, len(cols_stat)):
            r, p = spearmanr(num_data[cols_stat[i]], num_data[cols_stat[j]])
            results.append({'Pair': f'{cols_stat[i]} ↔ {cols_stat[j]}',
                'Spearman r': round(r,4), 'p-value': f'{p:.2e}',
                'Significance': '***' if p<0.001 else '**' if p<0.01 else '*' if p<0.05 else 'ns'})
    st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.markdown("#### Kruskal-Wallis Test: Popularity across top Genres")
    top10g = exp_df['Genre'].value_counts().head(10).index.tolist()
    groups = [exp_df[exp_df['Genre']==g]['Popularity'].dropna().values for g in top10g]
    H, p = kruskal(*groups)
    sig_label = "✅ Significant" if p < 0.05 else "❌ Not Significant"
    st.markdown(f"""
    <div class="insight-box">
    <strong>H statistic:</strong> {H:.2f} &nbsp;|&nbsp;
    <strong>p-value:</strong> {p:.2e} &nbsp;|&nbsp;
    <strong>Result:</strong> {sig_label} (α = 0.05)
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: LEADERBOARDS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🏆 Leaderboards":
    st.markdown('<div class="section-title">🏆 Leaderboards</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔥 Most Popular", "⭐ Best Rated", "🌍 Language Leaders"])

    with tab1:
        n = st.slider("Top N", 5, 50, 20, key='top_pop')
        top_pop = df.nlargest(n, 'Popularity')[['Title','Year','Popularity','Vote_Average','Vote_Count','Genre']]
        fig = px.bar(top_pop, x='Popularity', y='Title', orientation='h',
            color='Vote_Average', color_continuous_scale='RdYlGn',
            title=f'Top {n} Movies by Popularity', template=TEMPLATE)
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=max(400, n*22))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top_pop.reset_index(drop=True), use_container_width=True)

    with tab2:
        min_v = st.slider("Minimum votes", 100, 5000, 500, step=100)
        credible = df[df['Vote_Count'] >= min_v].copy()
        credible['Score'] = credible['Vote_Average'] * np.log1p(credible['Vote_Count'])
        top_rated = credible.nlargest(20, 'Score')[['Title','Year','Vote_Average','Vote_Count','Popularity','Score']]
        fig = px.scatter(top_rated, x='Vote_Count', y='Vote_Average',
            size='Score', color='Score', hover_data=['Title','Year'],
            color_continuous_scale='Viridis',
            title=f'Best Rated Movies (≥{min_v} votes)', template=TEMPLATE)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top_rated.reset_index(drop=True), use_container_width=True)

    with tab3:
        lang_perf = df.groupby('Original_Language').agg(
            Count=('Title','count'),
            Avg_Vote=('Vote_Average','mean'),
            Avg_Pop=('Popularity','mean'),
            Total_Votes=('Vote_Count','sum')
        ).reset_index().sort_values('Count', ascending=False).head(20)

        fig = px.scatter(lang_perf, x='Count', y='Avg_Vote',
            size='Total_Votes', color='Avg_Pop',
            hover_data=['Original_Language'],
            text='Original_Language',
            color_continuous_scale='Plasma',
            title='Language: Volume vs Quality (sized by Total Votes)',
            template=TEMPLATE)
        fig.update_traces(textposition='top center')
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: TEXT MINING
# ─────────────────────────────────────────────────────────────────────────────
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

    top_n = st.slider("Top N words", 10, 100, 30)
    top_words = pd.DataFrame(freq.most_common(top_n), columns=['Word','Frequency'])

    fig = px.bar(top_words, x='Frequency', y='Word', orientation='h',
        color='Frequency', color_continuous_scale='Cividis',
        title=f'Top {top_n} Words in Movie Overviews', template=TEMPLATE)
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=600)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Word Frequency Table")
    st.dataframe(top_words, use_container_width=True)

    st.markdown("#### Overview Word Count Distribution")
    fig = px.histogram(df, x='Overview_WC', nbins=50,
        title='How Long are Movie Overviews? (word count)',
        template=TEMPLATE, color_discrete_sequence=['#778da9'])
    st.plotly_chart(fig, use_container_width=True)

    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        import io as _io

        st.markdown("#### ☁️ Word Cloud")
        wc_col = st.color_picker("Background color", "#0d1b2a")
        wc = WordCloud(width=1200, height=500, background_color=wc_col,
            colormap='plasma', max_words=150, collocations=False
        ).generate(' '.join(filtered))

        fig_wc, ax = plt.subplots(figsize=(16,6))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        fig_wc.patch.set_facecolor(wc_col)
        st.pyplot(fig_wc)
    except ImportError:
        st.info("Install `wordcloud` (`pip install wordcloud`) to see the word cloud.")

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: CLUSTER ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🤖 Cluster Analysis":
    st.markdown('<div class="section-title">🤖 K-Means Cluster Analysis</div>', unsafe_allow_html=True)

    clust_input = df[['Popularity','Vote_Count','Vote_Average']].dropna()
    scaler = StandardScaler()
    X = scaler.fit_transform(clust_input)

    col_k, col_iter = st.columns(2)
    with col_k:
        k = st.slider("Number of Clusters (K)", 2, 10, 4)
    with col_iter:
        run_elbow = st.checkbox("Run Elbow + Silhouette analysis", value=True)

    if run_elbow:
        with st.spinner("Computing optimal K…"):
            inertias, silhs = [], []
            K_range = range(2, 9)
            for ki in K_range:
                km = KMeans(n_clusters=ki, random_state=42, n_init=10)
                lbl = km.fit_predict(X)
                inertias.append(km.inertia_)
                silhs.append(silhouette_score(X, lbl))

        fig = make_subplots(rows=1, cols=2,
            subplot_titles=('Elbow — Inertia','Silhouette Score'))
        fig.add_trace(go.Scatter(x=list(K_range), y=inertias,
            mode='lines+markers', line=dict(color='#e63946'), name='Inertia'), row=1, col=1)
        fig.add_trace(go.Scatter(x=list(K_range), y=silhs,
            mode='lines+markers', line=dict(color='#2a9d8f'), name='Silhouette'), row=1, col=2)
        fig.update_layout(template=TEMPLATE, height=360, title='Optimal K Selection')
        st.plotly_chart(fig, use_container_width=True)

        best_k = list(K_range)[silhs.index(max(silhs))]
        st.info(f"🔍 Best K by Silhouette Score: **{best_k}**")

    km_final = KMeans(n_clusters=k, random_state=42, n_init=10)
    clust_labels = km_final.fit_predict(X)

    clust_df = clust_input.copy()
    clust_df['Cluster'] = clust_labels.astype(str)
    clust_df['Title']   = df.loc[clust_input.index, 'Title'].values

    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X)
    clust_df['PC1'] = coords[:,0]
    clust_df['PC2'] = coords[:,1]

    fig = px.scatter(clust_df.sample(min(3000, len(clust_df)), random_state=42),
        x='PC1', y='PC2', color='Cluster',
        hover_data=['Title','Popularity','Vote_Average'],
        title=f'K={k} Clusters (PCA 2D Projection)',
        template=TEMPLATE, color_discrete_sequence=PALETTE, opacity=0.7)
    fig.update_layout(height=520)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Cluster Profiles")
    profiles = clust_df.groupby('Cluster')[['Popularity','Vote_Count','Vote_Average']].agg(['mean','median','count']).round(2)
    st.dataframe(profiles, use_container_width=True)

    fig2 = px.box(clust_df, x='Cluster', y='Popularity',
        color='Cluster', title='Popularity Distribution by Cluster',
        template=TEMPLATE, color_discrete_sequence=PALETTE)
    st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center; color:#415a77; font-size:0.82rem; padding:1rem 0'>
  🎬 CineScope Movie Intelligence Platform &nbsp;|&nbsp;
  Built with Python, Streamlit, Plotly, Scikit-learn &nbsp;|&nbsp;
  Advanced Analysis by Senior Data Scientist
</div>
""", unsafe_allow_html=True)
