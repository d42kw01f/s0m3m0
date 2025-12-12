# dashboard.py
import os
from datetime import timezone
from typing import Dict, List, Any

import numpy as np
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
import streamlit as st

# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="Esana — Political Pulse",
    page_icon="📊",
    layout="wide",
)

# =========================
# Constants & Env
# =========================
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB", "esana_scraper")
COLL_NAME = os.getenv("MONGO_COLL", "news_articles")

CANDIDATES = ["anura", "sajith", "ranil", "other", "no_one"]
REACTION_KEYS = ["like", "love", "haha", "wow", "sad", "angry"]
LOCAL_TZ = "Asia/Colombo"

# =========================
# Helpers
# =========================
def to_dt(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return pd.NaT
    dt = pd.to_datetime(x, utc=True, errors="coerce")
    return dt

def safe_candidate_weights(doc: Dict[str, Any]) -> Dict[str, float]:
    # Prefer model's total_candidate_weights, fallback to pt_the_candi probs
    weights = (
        doc.get("pt_the_waiter", {}).get("total_candidate_weights", {})
        or doc.get("pt_the_candi", {})
        or {}
    )
    return {c: float(weights.get(c, 0.0)) for c in CANDIDATES}

def safe_sentiment(doc: Dict[str, Any]) -> float:
    return float(doc.get("pt_the_senti", {}).get("sentiment_score", np.nan))

def safe_reactions(doc: Dict[str, Any]) -> Dict[str, int]:
    rx = doc.get("reactions", {}) or {}
    return {k: int(rx.get(k, 0)) for k in REACTION_KEYS}

def doc_title(doc: Dict[str, Any]) -> str:
    return doc.get("newsTitleEn") or doc.get("newsTitleLl") or f"News #{doc.get('newsId', '—')}"

def doc_lang(doc: Dict[str, Any]) -> str:
    if doc.get("newsTitleLl") or doc.get("newsContentLl"):
        return "si"
    if doc.get("newsTitleEn") or doc.get("newsContentEn"):
        return "en"
    return "unknown"

def top_candidate_from_weights(weights: Dict[str, float]) -> str:
    if not weights:
        return "none"
    return max(weights.items(), key=lambda kv: kv[1])[0]

def flatten_comments(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for c in doc.get("top_comments", []) or []:
        prow = {
            "newsId": doc.get("newsId"),
            "title": doc_title(doc),
            "publishedAt_article": to_dt(doc.get("publishedAt")),
            "comment_text": c.get("commentText"),
            "comment_publishedAt": to_dt(c.get("publishedAt")),
            "comment_like": int(c.get("commentReaction", {}).get("like", 0)),
            "comment_love": int(c.get("commentReaction", {}).get("love", 0)),
            "comment_haha": int(c.get("commentReaction", {}).get("haha", 0)),
            "comment_wow": int(c.get("commentReaction", {}).get("wow", 0)),
            "comment_sad": int(c.get("commentReaction", {}).get("sad", 0)),
            "comment_angry": int(c.get("commentReaction", {}).get("angry", 0)),
            "comment_replies": int(c.get("commentReplyCount", 0)),
            "comment_sentiment": float(c.get("pt_the_senti", {}).get("sentiment_score", np.nan)),
        }
        cand = {k: float(c.get("pt_the_candi", {}).get(k, np.nan)) for k in CANDIDATES}
        rows.append({**prow, **{f"cand_{k}": v for k, v in cand.items()}})
    return rows

# =========================
# Data Access
# =========================
@st.cache_data(show_spinner=False, ttl=300)
def load_raw() -> List[Dict[str, Any]]:
    client = MongoClient(MONGO_URI)
    coll = client[DB_NAME][COLL_NAME]
    return list(coll.find())

# =========================
# Load & Normalize
# =========================
raw = load_raw()
if not raw:
    st.title("Esana — Political Pulse")
    st.info("No data found in MongoDB. Check your connection or collection.")
    st.stop()

rows = []
for d in raw:
    weights = safe_candidate_weights(d)
    reactions = safe_reactions(d)
    published = to_dt(d.get("publishedAt"))
    row = {
        "newsId": d.get("newsId"),
        "title": doc_title(d),
        "lang": doc_lang(d),
        "publishedAt": published,
        "scrapedAt": to_dt(d.get("scrapedAt")),
        "predictedAt": to_dt(d.get("predictedAt")),
        "sentiment": safe_sentiment(d),
        "commentCount": int(d.get("commentCount", 0)),
        **{f"w_{c}": weights.get(c, 0.0) for c in CANDIDATES},
        **{f"rx_{k}": reactions.get(k, 0) for k in REACTION_KEYS},
    }
    row["rx_total"] = sum(reactions.values())
    row["top_candidate"] = top_candidate_from_weights(weights)
    # Local date-only column (crucial for filtering w/ st.date_input)
    if pd.notna(published):
        try:
            row["published_local"] = published.tz_convert(LOCAL_TZ).date()
        except Exception:
            # If tz-naive slipped through, coerce to UTC then convert
            row["published_local"] = pd.to_datetime(published, utc=True).tz_convert(LOCAL_TZ).date()
    else:
        row["published_local"] = pd.NaT
    rows.append(row)

df = pd.DataFrame(rows)

# Comments dataframe
comments_df = pd.DataFrame([r for doc in raw for r in flatten_comments(doc)]) if any(d.get("top_comments") for d in raw) else pd.DataFrame()

# =========================
# Sidebar Filters
# =========================
st.sidebar.header("Filters")

# Determine min/max date from local date column
if df["published_local"].notna().any():
    min_date = pd.to_datetime(df["published_local"].dropna().min()).date()
    max_date = pd.to_datetime(df["published_local"].dropna().max()).date()
else:
    # Fallback range
    min_date = pd.Timestamp.utcnow().date()
    max_date = pd.Timestamp.utcnow().date()

date_range = st.sidebar.date_input(
    "Published date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

# st.date_input can return a single date or a tuple
if isinstance(date_range, tuple):
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

lang_sel = st.sidebar.multiselect(
    "Language",
    sorted(df["lang"].dropna().unique().tolist()),
    default=sorted(df["lang"].dropna().unique().tolist()),
)
min_rx = st.sidebar.number_input("Minimum total reactions", min_value=0, value=0, step=10)
focus_candidate = st.sidebar.selectbox("Focus candidate (some views)", ["all"] + CANDIDATES, index=0)

# >>> FIXED: Compare date-to-date (no Timestamp vs date mismatch)
mask = (
    df["published_local"].notna()
    & df["published_local"].between(start_date, end_date)  # both are datetime.date
    & df["lang"].isin(lang_sel)
    & (df["rx_total"] >= min_rx)
)
fdf = df.loc[mask].copy()

# =========================
# KPI Header
# =========================
st.title("Esana — Political Pulse Dashboard")

total_articles = int(fdf.shape[0])
avg_sent = float(fdf["sentiment"].mean()) if fdf["sentiment"].notna().any() else np.nan
total_rx = int(fdf["rx_total"].sum())
total_comments = int(fdf["commentCount"].sum())

cand_cols = [f"w_{c}" for c in CANDIDATES]
leader = "—"
if not fdf.empty:
    sums = fdf[cand_cols].sum().rename(lambda c: c.replace("w_", ""))
    leader = sums.idxmax() if (sums.max() != 0 and not sums.isna().all()) else "—"

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Articles", f"{total_articles:,}")
k2.metric("Avg Sentiment", f"{avg_sent:.2f}" if not np.isnan(avg_sent) else "—")
k3.metric("Total Reactions", f"{total_rx:,}")
k4.metric("Total Comments", f"{total_comments:,}")
k5.metric("Leading Candidate (weights)", leader.capitalize() if leader != "—" else "—")

st.caption("Tip: Use the sidebar to slice by time, language, and engagement.")

# =========================
# Tabs
# =========================
tab_overview, tab_candidates, tab_sentiment, tab_reactions, tab_articles, tab_comments = st.tabs(
    ["Overview", "Candidates", "Sentiment", "Reactions", "Articles", "Comments Explorer"]
)

# -------- Overview --------
with tab_overview:
    if fdf.empty:
        st.info("No articles match your filters.")
    else:
        # Candidate share over time (stacked area) using local date
        daily = fdf.groupby("published_local")[cand_cols].sum().reset_index()
        share = daily.copy()
        total = share[cand_cols].sum(axis=1).replace(0, np.nan)
        for c in cand_cols:
            share[c] = share[c] / total
        share = share.fillna(0.0)
        share.rename(columns={f"w_{c}": c.capitalize() for c in CANDIDATES}, inplace=True)

        st.subheader("Candidate Share Over Time")
        fig_area = px.area(
            share,
            x="published_local",
            y=[c.capitalize() for c in CANDIDATES],
            title="Daily normalized candidate weight share",
        )
        fig_area.update_layout(xaxis_title="Date (local)", yaxis_title="Share")
        st.plotly_chart(fig_area, use_container_width=True)

        c1, c2 = st.columns([1.2, 1])
        with c1:
            st.subheader("Sentiment Over Time")
            s_daily = (
                fdf[["published_local", "sentiment"]]
                .dropna()
                .groupby("published_local")["sentiment"]
                .mean()
                .reset_index()
            )
            fig_sent = px.line(s_daily, x="published_local", y="sentiment", markers=True, title="Avg sentiment by day")
            st.plotly_chart(fig_sent, use_container_width=True)

        with c2:
            st.subheader("Publishing Cadence (Hour × Weekday)")
            tmp = fdf.dropna(subset=["publishedAt"]).copy()
            if not tmp.empty and tmp["publishedAt"].notna().any():
                local = tmp["publishedAt"].dt.tz_convert(LOCAL_TZ)
                tmp["hour"] = local.dt.hour
                tmp["weekday"] = local.dt.day_name()
                heat = tmp.groupby(["weekday", "hour"]).size().reset_index(name="count")
                cats = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
                heat["weekday"] = pd.Categorical(heat["weekday"], ordered=True, categories=cats)
                heat = heat.sort_values(["weekday","hour"])
                fig_heat = px.density_heatmap(
                    heat, x="hour", y="weekday", z="count", nbinsx=24, histfunc="avg", title="Posts by hour and weekday"
                )
                st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.write("No timestamp data available.")

# -------- Candidates --------
with tab_candidates:
    if fdf.empty:
        st.info("No articles match your filters.")
    else:
        st.subheader("Total & Normalized Candidate Weights")
        totals = fdf[cand_cols].sum().rename(lambda c: c.replace("w_", ""))
        norm = (totals / totals.sum()).fillna(0)

        cA, cB = st.columns(2)
        with cA:
            fig_tot = px.bar(
                totals.reset_index().rename(columns={"index": "candidate", 0: "weight"}),
                x="candidate", y="weight", title="Total weights"
            )
            st.plotly_chart(fig_tot, use_container_width=True)
        with cB:
            fig_norm = px.pie(
                norm.reset_index().rename(columns={"index": "candidate", 0: "share"}),
                names="candidate", values="share", title="Normalized weight share"
            )
            st.plotly_chart(fig_norm, use_container_width=True)

        st.subheader("Top Candidate Frequency (who tops per-article?)")
        top_counts = (
            fdf["top_candidate"]
            .value_counts()
            .reindex(CANDIDATES, fill_value=0)
            .reset_index()
        )
        top_counts.columns = ["candidate", "count"]  # <- key line: unique names

        fig_top = px.bar(
            top_counts,
            x="candidate",
            y="count",
            title="Articles where candidate has the highest weight"
        )
        st.plotly_chart(fig_top, use_container_width=True)

        if focus_candidate != "all":
            st.subheader(f"Top Articles for {focus_candidate.capitalize()} (by weight)")
            colname = f"w_{focus_candidate}"
            topn = fdf.sort_values(colname, ascending=False).head(10)[
                ["newsId", "title", "publishedAt", "published_local", colname, "rx_total", "commentCount", "sentiment"]
            ]
            st.dataframe(topn, use_container_width=True, hide_index=True)

# -------- Sentiment --------
with tab_sentiment:
    if fdf.empty:
        st.info("No articles match your filters.")
    else:
        st.subheader("Sentiment Distribution")
        fig_hist = px.histogram(fdf.dropna(subset=["sentiment"]), x="sentiment", nbins=30, title="Distribution")
        st.plotly_chart(fig_hist, use_container_width=True)

        st.subheader("Sentiment by Candidate (per-article)")
        long = fdf[["newsId", "sentiment"] + cand_cols].melt(
            id_vars=["newsId", "sentiment"], var_name="candidate", value_name="weight"
        )
        long["candidate"] = long["candidate"].str.replace("w_", "", regex=False)
        fig_box = px.box(long.dropna(subset=["sentiment"]), x="candidate", y="sentiment", points="outliers")
        st.plotly_chart(fig_box, use_container_width=True)

# -------- Reactions --------
with tab_reactions:
    if fdf.empty:
        st.info("No articles match your filters.")
    else:
        st.subheader("Reaction Totals")
        rx_totals = fdf[[f"rx_{k}" for k in REACTION_KEYS]].sum()
        fig_rx = px.bar(
            rx_totals.reset_index().rename(columns={"index": "reaction", 0: "count"}),
            x="reaction", y="count", title="Totals"
        )
        st.plotly_chart(fig_rx, use_container_width=True)

        st.subheader("Reaction Mix (%)")
        rx_sum = rx_totals.sum()
        if rx_sum > 0:
            mix = (rx_totals / rx_sum * 100.0).round(2)
            fig_mix = px.pie(
                mix.reset_index().rename(columns={"index": "reaction", 0: "pct"}),
                names="reaction", values="pct", title="Mix"
            )
            st.plotly_chart(fig_mix, use_container_width=True)
        else:
            st.write("No reaction data.")

        st.subheader("Top Reacted Articles")
        top_rx = fdf.sort_values("rx_total", ascending=False).head(10)[
            ["newsId", "title", "publishedAt", "published_local", "rx_total", "commentCount", "sentiment"] + cand_cols
        ]
        st.dataframe(top_rx, use_container_width=True, hide_index=True)

# -------- Articles --------
with tab_articles:
    st.subheader("Articles Table")
    show_cols = [
        "newsId", "title", "publishedAt", "published_local", "lang",
        "sentiment", "rx_total", "commentCount", "top_candidate"
    ] + cand_cols
    st.dataframe(
        fdf[show_cols].sort_values(["published_local", "publishedAt"], ascending=False),
        use_container_width=True,
        hide_index=True
    )

# -------- Comments Explorer --------
with tab_comments:
    if comments_df.empty:
        st.info("No comment data available.")
    else:
        st.subheader("Top Comments")
        left, right = st.columns([1, 1])
        with left:
            mode = st.radio("Order by", ["Highest sentiment", "Most reactions"], horizontal=True)
        with right:
            n_show = st.slider("How many to show", 5, 50, 15, step=5)

        cdf = comments_df.copy()
        # Localized comment date (optional)
        if cdf["comment_publishedAt"].notna().any():
            try:
                cdf["comment_local"] = cdf["comment_publishedAt"].dt.tz_convert(LOCAL_TZ)
            except Exception:
                cdf["comment_local"] = pd.to_datetime(cdf["comment_publishedAt"], utc=True).dt.tz_convert(LOCAL_TZ)
        else:
            cdf["comment_local"] = pd.NaT

        cdf["total_rx"] = cdf[["comment_like","comment_love","comment_haha","comment_wow","comment_sad","comment_angry"]].sum(axis=1)

        if mode == "Highest sentiment":
            cdf = cdf.sort_values("comment_sentiment", ascending=False, na_position="last")
        else:
            cdf = cdf.sort_values("total_rx", ascending=False, na_position="last")

        show = cdf.head(n_show)[[
            "newsId", "title", "comment_text", "comment_sentiment", "total_rx",
            "comment_replies", "comment_local",
            "cand_anura","cand_sajith","cand_ranil","cand_other","cand_no_one"
        ]]
        st.dataframe(show, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Built with ❤️ Streamlit + Plotly • Robust to missing fields • Mongo URI via env `MONGO_URI`")
