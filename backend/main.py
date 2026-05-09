"""CineScope FastAPI Backend  —  uvicorn main:app --reload --port 8000"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import pandas as pd, numpy as np, re, warnings
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
from collections import Counter
warnings.filterwarnings("ignore")

store: dict = {}

def build_features(df):
    genres = df["Genre"].str.split(", ")
    all_g  = sorted({g.strip() for gs in genres.dropna() for g in gs})
    rows   = []
    for _, row in df.iterrows():
        gl = [g.strip() for g in str(row["Genre"]).split(", ")]
        rows.append([1 if g in gl else 0 for g in all_g])
    gm = np.array(rows, dtype=np.float32)
    nm = StandardScaler().fit_transform(
        df[["Popularity","Vote_Count","Vote_Average"]].fillna(0).values.astype(np.float32))
    return np.hstack([gm * 2, nm])

def load_data():
    df = pd.read_csv("../dataset/mymoviedb.csv", lineterminator="\n")
    df["Release_Date"]      = pd.to_datetime(df["Release_Date"], errors="coerce")
    df["Year"]              = df["Release_Date"].dt.year.astype("Int64")
    df["Month"]             = df["Release_Date"].dt.month
    df["Decade"]            = (df["Year"] // 10 * 10).astype("Int64")
    df["Original_Language"] = df["Original_Language"].str.strip().str.upper()
    df["Overview_WC"]       = df["Overview"].fillna("").apply(lambda x: len(str(x).split()))
    df["Overview"]          = df["Overview"].fillna("No overview available.")
    df["Poster_Url"]        = df.get("Poster_Url", pd.Series(dtype=str)).fillna("")

    def cat(s, lbls):
        q = s.quantile([0,.25,.5,.75,1.0]).values
        return pd.cut(s, bins=np.unique(q), labels=lbls, include_lowest=True)

    df["Vote_Bucket"] = cat(df["Vote_Average"],["Not Popular","Below Avg","Average","Popular"]).astype(str)
    df["Pop_Tier"]    = cat(df["Popularity"],  ["Low","Medium","High","Viral"]).astype(str)
    df["Era"]         = pd.cut(df["Year"].astype(float),
        bins=[1900,1980,1990,2000,2010,2015,2020,2030],
        labels=["Pre-80s","80s","90s","2000s","2010-14","2015-19","2020+"],right=False).astype(str)

    df_exp = df.copy()
    df_exp["Genre"] = df_exp["Genre"].str.split(", ")
    df_exp = df_exp.explode("Genre").reset_index(drop=True)
    df_exp["Genre"] = df_exp["Genre"].str.strip()

    store.update(df=df, df_exp=df_exp, sim_mat=cosine_similarity(build_features(df)))
    print(f"✅ {len(df):,} movies loaded")

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_data(); yield

app = FastAPI(title="CineScope API", version="2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:3000"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"])

def sv(v):
    if pd.isna(v) or v is None: return None
    if isinstance(v, np.integer):  return int(v)
    if isinstance(v, np.floating): return float(v)
    return v

def td(row): return {k: sv(v) for k,v in row.items()}

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/api/stats")
def stats():
    df = store["df"]
    return dict(
        total_movies=int(len(df)), unique_genres=int(store["df_exp"]["Genre"].nunique()),
        avg_vote=round(float(df["Vote_Average"].mean()),2),
        median_popularity=round(float(df["Popularity"].median()),2),
        max_popularity=round(float(df["Popularity"].max()),2),
        latest_year=sv(df["Year"].max()), languages=int(df["Original_Language"].nunique()),
        top_movie=str(df.loc[df["Popularity"].idxmax(),"Title"]),
        top_genre=str(store["df_exp"]["Genre"].value_counts().idxmax()),
        peak_year=sv(df.groupby("Year").size().idxmax()),
    )

@app.get("/api/movies-per-year")
def movies_per_year(from_year: int=1990):
    yr = store["df"].groupby("Year").size().reset_index(name="count")
    return yr[yr["Year"]>=from_year].to_dict(orient="records")

@app.get("/api/genres")
def genres(top: int=20):
    c = store["df_exp"]["Genre"].value_counts().head(top).reset_index()
    c.columns=["genre","count"]; return c.to_dict(orient="records")

@app.get("/api/genre-stats")
def genre_stats():
    gs = store["df_exp"].groupby("Genre").agg(
        count=("Title","nunique"),avg_pop=("Popularity","mean"),
        avg_vote=("Vote_Average","mean"),avg_vote_count=("Vote_Count","mean")
    ).reset_index().rename(columns={"Genre":"genre"})
    for c in ["avg_pop","avg_vote","avg_vote_count"]: gs[c]=gs[c].round(2)
    return gs.sort_values("count",ascending=False).to_dict(orient="records")

@app.get("/api/languages")
def languages(top: int=10):
    lc=store["df"]["Original_Language"].value_counts().head(top).reset_index()
    lc.columns=["language","count"]; return lc.to_dict(orient="records")

@app.get("/api/vote-distribution")
def vote_dist():
    vd=store["df"]["Vote_Bucket"].value_counts().reset_index()
    vd.columns=["category","count"]; return vd.to_dict(orient="records")

@app.get("/api/top-popular")
def top_popular(n: int=20, min_votes: int=0):
    df=store["df"]
    return [td(r) for _,r in df[df["Vote_Count"]>=min_votes].nlargest(n,"Popularity").iterrows()]

@app.get("/api/best-rated")
def best_rated(n: int=20, min_votes: int=500):
    df=store["df"]; c=df[df["Vote_Count"]>=min_votes].copy()
    c["score"]=c["Vote_Average"]*np.log1p(c["Vote_Count"])
    return [td(r) for _,r in c.nlargest(n,"score").iterrows()]

@app.get("/api/search")
def search(q:str="", genre:str="", language:str="", year_from:int=1900,
           year_to:int=2030, min_vote:float=0, sort_by:str="Popularity",
           sort_asc:bool=False, page:int=1, page_size:int=20):
    df=store["df"].copy()
    if q:
        ql=q.lower()
        df=df[df["Title"].str.lower().str.contains(ql,na=False)|
              df["Genre"].str.lower().str.contains(ql,na=False)|
              df["Overview"].str.lower().str.contains(ql,na=False)]
    if genre:    df=df[df["Genre"].str.contains(genre,case=False,na=False)]
    if language: df=df[df["Original_Language"]==language.upper()]
    df=df[(df["Year"].fillna(0).astype(float)>=year_from)&
          (df["Year"].fillna(0).astype(float)<=year_to)&
          (df["Vote_Average"]>=min_vote)]
    df=df.sort_values(sort_by if sort_by in df.columns else "Popularity", ascending=sort_asc)
    total=len(df); s=(page-1)*page_size
    return dict(total=total,page=page,pages=(total+page_size-1)//page_size,
                results=[td(r) for _,r in df.iloc[s:s+page_size].iterrows()])

@app.get("/api/movie/{title}")
def get_movie(title:str):
    rows=store["df"][store["df"]["Title"].str.lower()==title.lower()]
    if rows.empty: raise HTTPException(404,"Not found")
    return td(rows.iloc[0])

@app.get("/api/recommend/{title}")
def recommend(title:str, n:int=8):
    df=store["df"]; sm=store["sim_mat"]
    m=df[df["Title"].str.lower()==title.lower()]
    if m.empty: raise HTTPException(404,"Not found")
    scores=sorted(enumerate(sm[m.index[0]]),key=lambda x:x[1],reverse=True)
    recs=df.iloc[[i for i,_ in scores[1:n+1]]]
    return [td(r) for _,r in recs.iterrows()]

@app.get("/api/mood/{mood}")
def mood_picks(mood:str, n:int=12):
    df=store["df"]
    mp={"comedy":"Comedy","thriller":"Thriller","action":"Action","drama":"Drama",
        "scifi":"Science Fiction","horror":"Horror","romance":"Romance","animation":"Animation"}
    gf=mp.get(mood.lower())
    sub=df[df["Genre"].str.contains(gf,na=False)] if gf else \
        (df[~df["Original_Language"].isin(["EN"])] if mood.lower()=="world" else None)
    if sub is None: raise HTTPException(400,"Unknown mood")
    return [td(r) for _,r in sub[sub["Vote_Count"]>=200].nlargest(n,"Vote_Average").iterrows()]

@app.get("/api/clusters")
def clusters(k:int=4):
    df=store["df"]; cols=["Popularity","Vote_Count","Vote_Average"]
    sub=df[cols].dropna(); X=StandardScaler().fit_transform(sub)
    lbs=KMeans(n_clusters=k,random_state=42,n_init=10).fit_predict(X)
    coords=PCA(n_components=2,random_state=42).fit_transform(X)
    idx=np.random.choice(len(sub),min(2000,len(sub)),replace=False)
    return {"points":[{"title":str(df.loc[sub.index[i],"Title"]),"cluster":int(lbs[i]),
        "pc1":round(float(coords[i,0]),3),"pc2":round(float(coords[i,1]),3),
        "popularity":round(float(sub.iloc[i]["Popularity"]),2),
        "vote_avg":round(float(sub.iloc[i]["Vote_Average"]),2)} for i in idx],"k":k}

@app.get("/api/word-freq")
def word_freq(top:int=40):
    SW={"the","a","an","in","of","to","and","is","are","he","she","his","her","they","their",
        "with","on","for","as","at","but","from","by","was","it","be","this","that","have",
        "has","who","when","after","into","its","not","or","about","one","two","him","them",
        "also","all","which","will","been","more","new"}
    words=re.findall(r"\b[a-z]{4,}\b"," ".join(store["df"]["Overview"].dropna().str.lower()))
    freq=Counter(w for w in words if w not in SW)
    return [{"word":w,"count":c} for w,c in freq.most_common(top)]

@app.get("/api/yearly-trend")
def yearly_trend():
    df=store["df"]
    yt=df.groupby("Year").agg(avg_vote=("Vote_Average","mean"),
        avg_pop=("Popularity","mean"),count=("Title","count")).reset_index()
    yt=yt[yt["Year"]>=1990]
    for c in ["avg_vote","avg_pop"]: yt[c]=yt[c].round(2)
    return yt.astype(object).where(yt.notna(),None).to_dict(orient="records")

@app.get("/api/decade-genre")
def decade_genre():
    dg=store["df_exp"][store["df_exp"]["Decade"]>=1980].groupby(
        ["Decade","Genre"]).size().reset_index(name="count")
    return dg.astype(object).where(dg.notna(),None).to_dict(orient="records")

@app.get("/api/titles")
def titles():
    return store["df"]["Title"].dropna().sort_values().tolist()