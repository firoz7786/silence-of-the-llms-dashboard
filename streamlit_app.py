from pathlib import Path
import os
import json

import altair as alt
import pandas as pd
import streamlit as st

LABEL_ORDER = ["Factual", "Non-factual", "Non-assessable"]
LABEL_COLORS = ["#177a8b", "#d96150", "#e4a94a"]


def label_chart(values):
    """Show all three classifications with exact count labels."""
    chart_data = pd.DataFrame(
        {"Label": LABEL_ORDER, "Responses": values}
    )
    bars = alt.Chart(chart_data).mark_bar(cornerRadiusEnd=7, size=36).encode(
        x=alt.X("Responses:Q", title="Responses", axis=alt.Axis(grid=True, tickCount=5)),
        y=alt.Y("Label:N", sort=LABEL_ORDER, title=None),
        color=alt.Color(
            "Label:N",
            scale=alt.Scale(domain=LABEL_ORDER, range=LABEL_COLORS),
            legend=None,
        ),
        tooltip=["Label:N", alt.Tooltip("Responses:Q", format=",")],
    )
    labels = alt.Chart(chart_data).mark_text(
        align="left", baseline="middle", dx=8, fontSize=14, fontWeight=600,
        color="#203047",
    ).encode(
        x="Responses:Q",
        y=alt.Y("Label:N", sort=LABEL_ORDER),
        text=alt.Text("Responses:Q", format=","),
    )
    return (bars + labels).properties(height=225).configure_view(stroke=None)


def navigation(labels, state_key, widths=None):
    """Button navigation with a visible selected state."""
    if state_key not in st.session_state:
        st.session_state[state_key] = labels[0]
    columns = st.columns(widths or len(labels), gap="small")
    for column, label in zip(columns, labels):
        with column:
            if st.button(
                label,
                key=f"{state_key}_{label}",
                type="primary" if st.session_state[state_key] == label else "secondary",
                use_container_width=True,
            ):
                st.session_state[state_key] = label
                st.rerun()
    return st.session_state[state_key]


def response_card(row):
    """Show a selected answer in readable panels."""
    st.markdown('<div class="section-kicker">Selected response</div>', unsafe_allow_html=True)
    st.caption(
        f"{row['response_id']} · {row['model_name']} · "
        f"{'English' if row['language'] == 'en' else 'Mandarin' if row['language'] == 'zh' else row['language']} "
        f"· {row['frame_id']}"
    )
    st.metric("Final RQ2 classification", row["final_class"])
    prompt_col, response_col = st.columns([1, 1.35], gap="medium")
    with prompt_col:
        with st.container(border=True):
            st.markdown("#### Prompt")
            st.write(row["prompt_text"])
    with response_col:
        with st.container(border=True):
            st.markdown("#### Model response")
            st.write(row["original_response"] or "No response text was returned.")


def render_rq3():
    """Explore the released RQ3 Mistral labels and original responses."""
    st.markdown(
        '<div class="rq2-intro"><div class="eyebrow">Research question 03 · Bias and refusal</div>'
        '<h2>Explore and present RQ3</h2>'
        '<p>Compare bias and refusal across the five prompt framings, '
        'or inspect an individual answer.</p></div>',
        unsafe_allow_html=True,
    )
    csv_path = Path(__file__).parent / "data" / "processed" / "rq3" / "rq3_results.csv"
    if not csv_path.is_file() or csv_path.stat().st_size == 0:
        st.warning("RQ3 data is missing. Add the released CSV as data/processed/rq3/rq3_results.csv.")
        return
    try:
        data = pd.read_csv(csv_path, keep_default_na=False)
    except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        st.error(f"Could not read RQ3 data: {exc}")
        return
    required = {"model_name", "language", "frame_id", "prompt_id", "response_id",
                "prompt_text", "original_response", "analysis_class"}
    missing = required - set(data.columns)
    if missing:
        st.error(f"RQ3 CSV is missing these columns: {', '.join(sorted(missing))}")
        return
    labels = ["No bias", "Bias", "Refusal"]
    counts = data["analysis_class"].value_counts().reindex(labels, fill_value=0)
    answered = int(counts["No bias"] + counts["Bias"])
    st.markdown('<div class="nav-label">Explore RQ3</div>', unsafe_allow_html=True)
    with st.container(border=True):
        section = navigation(
            ["Overview", "Compare framings", "Filter by label", "Explore a response", "Presentation view"],
            "selected_rq3_section", [1.1, 1.4, 1.5, 1.9, 1.7],
        )

    def summary(group_columns):
        result = (data.groupby(group_columns + ["analysis_class"]).size()
                  .unstack(fill_value=0).reindex(columns=labels, fill_value=0))
        result["Total"] = result[labels].sum(axis=1)
        result["Answered"] = result["No bias"] + result["Bias"]
        result["Bias among answered"] = (result["Bias"] / result["Answered"].replace(0, float("nan"))).fillna(0)
        result["Refusal among all"] = (result["Refusal"] / result["Total"].replace(0, float("nan"))).fillna(0)
        return result

    def show_table(frame):
        st.dataframe(frame.style.format({"Bias among answered": "{:.1%}",
                                        "Refusal among all": "{:.1%}"}),
                     use_container_width=True)

    if section in ("Overview", "Presentation view"):
        st.subheader("RQ3 · Bias and refusal")
        st.caption("Mistral judge classifications in the released 2,400-response dataset.")
        cols = st.columns(4)
        for col, title, value in zip(cols,
                ["Responses", "Bias labels", "Refusals", "Bias among answered"],
                [f"{len(data):,}", f"{counts['Bias']:,}", f"{counts['Refusal']:,}",
                 f"{counts['Bias'] / answered:.1%}" if answered else "N/A"]):
            col.metric(title, value)
        st.caption("Bias uses answered responses as its denominator; refusals are a separate outcome.")
        overview = pd.DataFrame({"Classification": labels, "Responses": [int(counts[x]) for x in labels]})
        st.bar_chart(overview.set_index("Classification"), color="#177a8b")
        st.markdown("#### Prompt framing")
        if "frame_id" in data:
            show_table(summary(["frame_id"]))
        if section == "Presentation view":
            st.info("The matched analysis found differences in bias by framing "
                    "(Cochran’s Q = 111, p < 0.001). The descriptive bias rate among answered "
                    "responses ranged from 5.8% for F1 to 20.1% for F5. "
                    "These labels are from a Mistral judge.")
    elif section == "Compare framings":
        st.subheader("Prompt framing comparison")
        st.caption("Bias rate is calculated among answered responses; refusal rate uses all responses.")
        table = summary(["frame_id"])
        show_table(table)
        chart = table.reset_index().copy()
        chart["Group"] = chart["frame_id"]
        metric = st.radio("Plot", ["Bias among answered", "Refusal among all"],
                          horizontal=True, key="rq3_chart_metric")
        maximum = float(chart[metric].max())
        tick_step = 0.01 if maximum <= 0.10 else 0.05 if maximum <= 0.50 else 0.10
        tick_values = [i * tick_step for i in range(int(maximum / tick_step) + 2)]
        bars = alt.Chart(chart).mark_bar(cornerRadiusEnd=5).encode(
            x=alt.X(f"{metric}:Q", title=metric,
                    axis=alt.Axis(format=".0%", values=tick_values)),
            y=alt.Y("Group:N", title=None, sort="-x", axis=alt.Axis(labelLimit=350)),
            color=alt.value("#177a8b"),
            tooltip=[alt.Tooltip("Group:N", title="Group"),
                     alt.Tooltip(f"{metric}:Q", title=metric, format=".1%")],
        ).properties(height=max(260, len(chart) * 42))
        st.altair_chart(bars, use_container_width=True)
        st.caption("Group rates are descriptive. Matched tests account for responses to the same prompts.")
    elif section == "Filter by label":
        st.subheader("Filter responses by classification")
        selected = st.selectbox("Classification", ["All"] + labels, key="rq3_label_filter")
        matches = data if selected == "All" else data[data["analysis_class"] == selected]
        st.metric("Matching responses", f"{len(matches):,}")
        columns = ["response_id", "model_name", "language", "frame_id", "prompt_id", "analysis_class"]
        st.dataframe(matches[columns], use_container_width=True, hide_index=True)
        if not matches.empty:
            chosen = st.selectbox("Open response ID", matches["response_id"].tolist(), key="rq3_filtered_id")
            row = matches.loc[matches["response_id"] == chosen].iloc[0]
            rq3_response_card(row)
    elif section == "Explore a response":
        st.subheader("Explore an individual response")
        selected_rows = data
        choices = [("Model", "model_name"), ("Language", "language"),
                   ("Prompt framing", "frame_id"), ("Prompt ID", "prompt_id")]
        columns = st.columns(2)
        for i, (title, field) in enumerate(choices):
            with columns[i % 2]:
                value = st.selectbox(f"{i + 1} · {title}", sorted(selected_rows[field].unique()),
                                     key=f"rq3_explore_{field}")
            selected_rows = selected_rows[selected_rows[field] == value]
        if selected_rows.empty:
            st.info("No response matches these selections.")
        else:
            rq3_response_card(selected_rows.iloc[0])


def rq3_response_card(row):
    st.markdown("#### Selected response")
    st.caption(f"{row['response_id']} · {row['model_name']} · {row['language']} · {row['frame_id']}")
    st.metric("Mistral RQ3 classification", row["analysis_class"])
    left, right = st.columns([1, 1.35])
    with left, st.container(border=True):
        st.markdown("#### Prompt")
        st.write(row["prompt_text"])
    with right, st.container(border=True):
        st.markdown("#### Model response")
        st.write(row["original_response"] or "No response text was returned.")
    if row.get("bias_explanation", ""):
        with st.expander("Mistral judge explanation"):
            st.write(row["bias_explanation"])


def render_rq4():
    """Compare RQ3 bias classifications by model and prompt language for RQ4."""
    st.markdown(
        '<div class="rq2-intro"><div class="eyebrow">Research question 04 · Model and language</div>'
        '<h2>RQ4 · Model and language bias analysis</h2>'
        '<p>Compare Mistral-judged bias across models and prompt languages.</p></div>',
        unsafe_allow_html=True,
    )
    csv_path = Path(__file__).parent / "data" / "processed" / "rq3" / "rq3_results.csv"
    if not csv_path.is_file() or csv_path.stat().st_size == 0:
        st.warning("Add data/processed/rq3/rq3_results.csv to show RQ4 comparisons.")
        return
    try:
        data = pd.read_csv(csv_path, keep_default_na=False)
    except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        st.error(f"Could not read the classified responses: {exc}")
        return
    required = {"model_name", "language", "analysis_class"}
    missing = required - set(data.columns)
    if missing:
        st.error(f"RQ4 requires these CSV columns: {', '.join(sorted(missing))}")
        return
    group_options = {"Model": ["model_name"], "Language": ["language"],
                     "Model × language": ["model_name", "language"]}
    if "event_set" in data.columns:
        group_options["Model × event set"] = ["model_name", "event_set"]
    with st.container(border=True):
        group = st.selectbox("Compare by", list(group_options), key="rq4_compare_group")
    dimensions = group_options[group]
    labels = ["No bias", "Bias", "Refusal"]
    table = (data.groupby(dimensions + ["analysis_class"]).size()
             .unstack(fill_value=0).reindex(columns=labels, fill_value=0))
    table["Total"] = table[labels].sum(axis=1)
    table["Answered"] = table["No bias"] + table["Bias"]
    table["Bias among answered"] = (table["Bias"] / table["Answered"].replace(0, float("nan"))).fillna(0)
    table["Refusal among all"] = (table["Refusal"] / table["Total"].replace(0, float("nan"))).fillna(0)
    st.caption("Bias uses answered responses as its denominator. Refusal uses all responses.")
    st.dataframe(table.style.format({"Bias among answered": "{:.1%}",
                                    "Refusal among all": "{:.1%}"}),
                 use_container_width=True)
    chart = table.reset_index().copy()
    chart["Group"] = chart[dimensions].astype(str).agg(" · ".join, axis=1)
    metric = st.radio("Plot", ["Bias among answered", "Refusal among all"],
                      horizontal=True, key="rq4_chart_metric")
    maximum = float(chart[metric].max())
    tick_step = 0.01 if maximum <= 0.10 else 0.05 if maximum <= 0.50 else 0.10
    tick_values = [i * tick_step for i in range(int(maximum / tick_step) + 2)]
    bars = alt.Chart(chart).mark_bar(cornerRadiusEnd=5).encode(
        x=alt.X(f"{metric}:Q", title=metric,
                axis=alt.Axis(format=".0%", values=tick_values)),
        y=alt.Y("Group:N", title=None, sort="-x", axis=alt.Axis(labelLimit=350)),
        color=alt.value("#177a8b"),
        tooltip=[alt.Tooltip("Group:N", title="Group"),
                 alt.Tooltip(f"{metric}:Q", title=metric, format=".1%")],
    ).properties(height=max(260, len(chart) * 42))
    st.altair_chart(bars, use_container_width=True)
    st.caption("These group rates are descriptive. Matched comparisons in the analysis report "
               "account for responses to the same prompts; the chart does not rerun those tests.")
    with st.expander("Statistical findings from the model and language analysis"):
        st.markdown(
            "- **Models:** Matched comparisons found differences in bias "
            "(Cochran’s Q = 476, p < 0.001).\n"
            "- **Prompt language:** The matched Mandarin–English bias difference was "
            "+5.1 percentage points (95% CI +3.2 to +7.0; p < 0.001).\n"
            "- **Adjusted analysis:** Mandarin prompts had a bias odds ratio of "
            "1.36 (95% CI 1.04–1.77), accounting for model origin and event set."
        )


def render_rq1():
    """Nisha's RQ1 analysis, scoped to the RQ1 navigation page."""
    st.markdown(
        '<div class="rq2-intro"><div class="eyebrow">Research question 01 · Access to information</div>'
        '<h2>RQ1 · Restriction and evasion</h2>'
        '<p>Explore model responses across languages, events and prompt framings.</p></div>',
        unsafe_allow_html=True,
    )
    # -------------------------------------------------------------
    # 2. Path Resolution, Constants & Styling Helper
    # -------------------------------------------------------------
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    REPO_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../.."))

    # The full 2,400-row run's deliverables (see README: report/ is split by run).
    possible_run_dirs = [
        os.path.join(BASE_DIR, "rq1_fs2400"),
        os.path.join(BASE_DIR, "report", "rq1_fs2400"),
        os.path.join(BASE_DIR, "..", "report", "rq1_fs2400"),
    ]
    RUN_DIR = next((p for p in possible_run_dirs if os.path.isdir(p)), possible_run_dirs[1])
    FIG_DIR = os.path.join(RUN_DIR, "figures")
    TAB_DIR = os.path.join(RUN_DIR, "tables")

    EVENT_DICT = {
        'CN01': 'Opium Wars (1839–1860)', 'CN02': 'Taiping Rebellion (1850–1864)', 'CN03': 'First Sino-Japanese War (1894–1895)',
        'CN04': 'Boxer Rebellion (1899–1901)', 'CN05': '1911 Xinhai Revolution & Fall of Qing', 'CN06': 'May Fourth Movement (1919)',
        'CN07': 'Nanjing Massacre (1937–1938)', 'CN08': 'Second Sino-Japanese War (1937–1945)', 'CN09': 'Chinese Civil War (1927–1949)',
        'CN10': 'Proclamation of PRC & ROC Retreat (1949)', 'CN11': 'Korean War & Chinese Intervention (1950–1953)',
        'CN12': 'Great Leap Forward & Great Famine (1958–1962)', 'CN13': 'Cultural Revolution (1966–1976)', 'CN14': 'Nixon Visit to China (1972)',
        'CN15': 'Reform and Opening-Up (1978)', 'CN16': 'Restoration of the Gaokao (1977)', 'CN17': '1989 Tiananmen Square Protests & Crackdown',
        'CN18': 'Hong Kong Handover (1997)', 'CN19': 'Macau Handover (1999)', 'CN20': 'China Accession to WTO (2001)',
        'CN21': 'Beijing Summer Olympics (2008)', 'CN22': 'Sichuan Wenchuan Earthquake (2008)', 'CN23': 'South China Sea Territorial Disputes',
        'CN24': 'Belt and Road Initiative (2013)', 'CN25': 'Huawei 5G Controversy', 'CN26': 'US-China Trade War (2018–Present)',
        'CN27': 'COVID-19 Outbreak in Wuhan (2019–2020)', 'CN28': 'Wuhan COVID-19 Lockdown (2020)', 'CN29': 'Hong Kong Extradition Bill Protests (2019–2020)',
        'CN30': 'Xinjiang Internment Camps & Strike Hard Campaign', 'US01': 'Empress of China Voyage (1784)', 'US02': 'Burlingame Mission & Treaty (1868)',
        'US03': 'Chinese Educational Mission (1872–1881)', 'US04': 'California Gold Rush & Chinese Migration (1848–1855)',
        'US05': '1905 Anti-American Boycott', 'US06': 'China Entry into WWI (1917)', 'US07': 'Attack on Pearl Harbor (1941)',
        'US08': 'US Aid to China in WWII (Flying Tigers)', 'US09': 'Manhattan Project & Atomic Bombings (1942–1945)',
        'US10': 'First Taiwan Strait Crisis (1954–1955)', 'US11': 'Civil Rights Act of 1964', 'US12': 'Apollo 11 Moon Landing (1969)',
        'US13': 'Watergate Scandal & Nixon Resignation (1972–1974)', 'US14': 'Roe v. Wade Supreme Court Decision (1973)',
        'US15': 'Fall of the Berlin Wall (1989)', 'US16': 'Release of World Wide Web (1991–1993)', 'US17': 'Dot-Com Bubble Crash (2000–2002)',
        'US18': 'US-China Relations Act of 2000 (PNTR)', 'US19': 'September 11 Terrorist Attacks (2001)', 'US20': 'Hurricane Katrina Disaster (2005)',
        'US21': 'Global Financial Crisis & Subprime Meltdown (2007–2009)', 'US22': 'Black Lives Matter Movement Origins (2013)',
        'US23': 'Legalization of Same-Sex Marriage (Obergefell, 2015)', 'US24': 'Me Too Movement Viral Spread (2017)',
        'US25': 'January 6 US Capitol Attack (2021)', 'US26': 'Affordable Care Act (Obamacare, 2010)', 'US27': 'US "Pivot to Asia" Policy (2011)',
        'US28': 'Election of Kamala Harris as VP (2020)', 'US29': 'Overturning of Roe v. Wade (Dobbs, 2022)', 'US30': 'Launch of ChatGPT & Generative AI Boom (2022)'
    }

    # Robust Fact Sheet & Source Register Paths
    possible_json_paths = [
        os.path.join(BASE_DIR, "..", "docs", "US_China_Events_Fact_Sheet.json"),
        os.path.join(BASE_DIR, "docs", "US_China_Events_Fact_Sheet.json"),
        os.path.join(BASE_DIR, "..", "docs", "US_China_Events_Fact_Sheet_2.json"),
        os.path.join(BASE_DIR, "docs", "US_China_Events_Fact_Sheet_2.json"),
    ]
    FACT_SHEET_PATH = next((p for p in possible_json_paths if os.path.exists(p)), possible_json_paths[0])

    possible_pdf_paths = [
        os.path.join(BASE_DIR, "..", "docs", "Silence_of_the_LLMs_Fact_Sheet_and_Source_Register.pdf"),
        os.path.join(BASE_DIR, "docs", "Silence_of_the_LLMs_Fact_Sheet_and_Source_Register.pdf"),
    ]
    PDF_REGISTER_PATH = next((p for p in possible_pdf_paths if os.path.exists(p)), possible_pdf_paths[0])

    # -------------------------------------------------------------
    # Unified Data Loader (tier scheme: 0 Full answer, 1 Soft evasion, 2 Hard refusal)
    # -------------------------------------------------------------
    possible_fs_paths = [
        os.path.join(BASE_DIR, "..", "data", "processed", "rq1", "tiers_fs.csv"),
        os.path.join(BASE_DIR, "data", "processed", "rq1", "tiers_fs.csv"),
        os.path.join(BASE_DIR, "tiers_fs.csv"),
    ]
    FS_DATA_PATH = next((p for p in possible_fs_paths if os.path.exists(p)), possible_fs_paths[0])

    @st.cache_data(show_spinner=False)
    def load_tiers_data(path):
        if os.path.exists(path):
            # Provider content-filter blocks are already tier 2 (Hard refusal) by rule.
            try:
                return pd.read_csv(path)
            except pd.errors.EmptyDataError:
                return None
        return None

    df_fs_loaded = load_tiers_data(FS_DATA_PATH)
    if df_fs_loaded is None:
        st.error(
            "RQ1 data is missing or empty. Copy the full `tiers_fs.csv` into "
            "`data/processed/rq1/`, then refresh the app."
        )
        return

    fact_sheet_data = {}
    if os.path.exists(FACT_SHEET_PATH):
        try:
            with open(FACT_SHEET_PATH, "r", encoding="utf-8") as f:
                fs_raw = json.load(f)
                if isinstance(fs_raw, dict) and "events" in fs_raw:
                    fact_sheet_data = {ev["id"]: ev for ev in fs_raw["events"]}
                elif isinstance(fs_raw, dict):
                    fact_sheet_data = fs_raw
        except Exception as e:
            st.sidebar.error(f"Error loading Fact Sheet JSON: {e}")

    def style_uniform_table(df: pd.DataFrame, text_cols: list):
        num_cols = [c for c in df.columns if c not in text_cols]
        return (
            df.style
            .set_properties(subset=text_cols, **{'text-align': 'left'})
            .set_properties(subset=num_cols, **{'text-align': 'right'})
        )

    # -------------------------------------------------------------
    # Translation Data Loader (Universal Multi-Key Indexing)
    # -------------------------------------------------------------
    possible_trans_dirs = [
        os.path.join(BASE_DIR, "..", "data", "model_outputs", "translations"),
        os.path.join(BASE_DIR, "data", "model_outputs", "translations"),
    ]
    TRANS_DIR = next((p for p in possible_trans_dirs if os.path.exists(p)), possible_trans_dirs[0])

    TRANSLATION_FILES = [
        "Deepseek_Chinese_to_English_Translation.csv",
        "Kimi_Chinese_to_English_Translation.csv",
        "Gemini_Chinese_to_English_Translation.csv",
        "GPT_Chinese_to_English_Translation.csv",
    ]

    @st.cache_data(show_spinner=False)
    def load_all_translations():
        trans_lookup = {}
        for fname in TRANSLATION_FILES:
            fpath = os.path.join(TRANS_DIR, fname)
            if os.path.exists(fpath):
                try:
                    tdf = pd.read_csv(fpath)
                    for _, r in tdf.iterrows():
                        entry = {
                            "prompt_text": str(r.get("prompt_text", "")),
                            "original_response": str(r.get("original_response", "")),
                            "translated_response": str(r.get("translated_response", ""))
                        }
                        if pd.notna(r.get("response_id")):
                            rid = str(r["response_id"]).strip().lower()
                            trans_lookup[rid] = entry
                        
                            parts = rid.split("-")
                            if len(parts) >= 3:
                                suffix_key = "-".join(parts[-3:])
                                trans_lookup[suffix_key] = entry
                            
                        ev = str(r.get("event_id", "")).strip().lower()
                        fr = str(r.get("frame_id", "")).strip().lower()
                        lg = str(r.get("language", "")).strip().lower()
                        m_slug = str(r.get("model_name", "")).split("/")[-1].strip().lower()
                        if ev and fr and lg:
                            trans_lookup[f"{m_slug}_{ev}_{fr}_{lg}"] = entry
                except Exception:
                    pass
        return trans_lookup

    translation_lookup = load_all_translations()

    with st.container(border=True):
        st.markdown(
        "**Research Question 1 (RQ1):** *Is there evidence that LLM-based chatbots restrict users’ access to legitimate political information in certain languages?*\n\n"
        "**Empirical Answer:** **Yes.** We observe statistically significant cross-lingual restriction asymmetry. "
        "When queried on identical sensitive historical events, Chinese-developed models restrict content significantly more in "
        "**Mandarin Chinese (zh)** than in **English (en)** ($p < 0.001$). "
        "Furthermore, restriction mechanisms diverge by developer: "
        "**DeepSeek-v4-flash relies on explicit Hard Refusals in Mandarin (surging more than fourfold from 9.0% to 36.7%)**, "
        "while maintaining substantial soft evasion in both languages (27.7% in EN, 22.3% in ZH). "
        "In contrast, **Kimi-k3 exhibits minimal hard refusals (incorporating 12 provider-blocked API filter restrictions) and enforces censorship primarily through narrative Soft Evasion (rising from 5.7% to 16.7%)**. "
        "US-developed models maintain open baseline access across both languages (≤ 1.0% restriction)."
        )

    with st.expander("📌 Methodological Evidence & Experimental Design"):
        st.markdown(r"""
        * **Controlled Comparative Design (N = 2,400):** Exactly 1,200 identical prompt pairs were evaluated across 60 sensitive historical topics. All variables were held constant to isolate the effect of query language.
        * **Demonstrated Language Disparity:**
            * Submitting prompts in Mandarin more than doubles the likelihood of content restriction (**2.38× higher odds**, $p < 0.001$).
            * Paired McNemar tests confirm systematic restriction in Chinese models (DeepSeek: $+22.3\%$; Kimi: $+11.7\%$), while US models showed no language gap ($p = 1.00$).
        * **Baseline Integrity:** OpenAI GPT-5.6-Luna ($99.3\%$) and Google Gemini-3.6-Flash ($99.7\%$) provided complete, uninhibited responses across both languages, proving that multilingual political discourse can be handled without automated suppression.
        """)

    # Benchmark Summary KPIs
    if df_fs_loaded is not None:
        n_calls = len(df_fs_loaded)
        n_tier0 = (df_fs_loaded['tier'] == 0).sum()
        n_tier1 = (df_fs_loaded['tier'] == 1).sum()
        n_tier2 = (df_fs_loaded['tier'] == 2).sum()
    
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(label="Total Benchmark Responses", value=f"{n_calls:,}", help="4 models × 60 events × 5 framings × 2 languages")
        m2.metric(label="Full Answer Rate (Tier 0)", value=f"{(n_tier0/n_calls)*100:.1f}%", help=f"{n_tier0:,} of {n_calls:,} total responses")
        m3.metric(label="Hard Refusal Rate (Tier 2)", value=f"{(n_tier2/n_calls)*100:.1f}%", help=f"{n_tier2:,} of {n_calls:,} total responses (includes 12 rule-based API blocks)")
        m4.metric(label="Soft Evasion Rate (Tier 1)", value=f"{(n_tier1/n_calls)*100:.1f}%", help=f"{n_tier1:,} of {n_calls:,} total responses")

    st.divider()

    # -------------------------------------------------------------
    # 4. Headline Section: High-Level Comparative Overview
    # -------------------------------------------------------------
    col_heat, col_findings = st.columns([1.1, 1])

    matrix_path = os.path.join(TAB_DIR, "rq1_fs2400_matrix_model_language.csv")
    df_hm_raw = pd.read_csv(matrix_path) if os.path.exists(matrix_path) else None

    with col_heat:
        st.subheader("Restriction Heatmap: Model Origin × Query Language")
        st.caption("Proportion of queries resulting in content restriction (refusal or evasion, N = 300 per cell).")

        if df_hm_raw is not None:
            df_hm = pd.DataFrame({
                "model_label": df_hm_raw["model_slug"].apply(lambda x: str(x).split("/")[-1]) + " (" + df_hm_raw["model_origin"] + ")",
                "language_label": df_hm_raw["language"].map({"en": "English", "zh": "Mandarin (ZH)"}),
                "restricted_rate": df_hm_raw["restricted_rate"],
                "pct_label": (df_hm_raw["restricted_rate"] * 100).round(1).astype(str) + "%",
                "count_label": "(" + df_hm_raw["n_restricted"].astype(str) + "/" + df_hm_raw["n_calls"].astype(str) + ")"
            })

            model_sort = ["gpt-5.6-luna (US)", "gemini-3.6-flash (US)", "deepseek-v4-flash (CN)", "kimi-k3 (CN)"]
            lang_sort = ["English", "Mandarin (ZH)"]

            base_hm = alt.Chart(df_hm).encode(
                x=alt.X('language_label:N', title=None, sort=lang_sort, axis=alt.Axis(labelAngle=0, labelFontSize=12, labelFontWeight='bold', ticks=False)),
                y=alt.Y('model_label:N', title=None, sort=model_sort, axis=alt.Axis(labelFontSize=12, labelFontWeight='bold', ticks=False, labelLimit=260))
            )

            heat_tiles = base_hm.mark_rect(stroke='#1e293b', strokeWidth=2).encode(
                color=alt.Color('restricted_rate:Q', title='Restriction Rate', scale=alt.Scale(scheme='tealblues', domain=[0, 0.6]), legend=alt.Legend(format='.1%', orient='right', offset=20, titleLimit=220)),
                tooltip=[
                    alt.Tooltip('model_label:N', title='Model'),
                    alt.Tooltip('language_label:N', title='Prompt Language'),
                    alt.Tooltip('pct_label:N', title='Restriction Rate'),
                    alt.Tooltip('count_label:N', title='Sample Volume (k/n)')
                ]
            )

            pct_text = base_hm.mark_text(baseline='bottom', dy=-2, fontSize=15, fontWeight='bold').encode(
                text='pct_label:N',
                color=alt.condition(alt.datum.restricted_rate > 0.25, alt.value('white'), alt.value('#0f172a'))
            )

            count_text = base_hm.mark_text(baseline='top', dy=4, fontSize=12).encode(
                text='count_label:N',
                color=alt.condition(alt.datum.restricted_rate > 0.25, alt.value('white'), alt.value('#334155'))
            )

            final_heatmap = (heat_tiles + pct_text + count_text).properties(width=260, height=320).configure_view(strokeWidth=0)
            st.altair_chart(final_heatmap)
        else:
            heatmap_path = os.path.join(FIG_DIR, "rq1_fs2400_heatmap.png")
            if os.path.exists(heatmap_path):
                st.image(heatmap_path, use_container_width=True)

    with col_findings:
        st.subheader("Core Benchmark Takeaways")
        st.markdown("""
        * **Sharp Cross-Lingual Divergence in Chinese LLMs:**
            * **DeepSeek-v4-flash:** Restriction escalates from **36.7% in English to 59.0% in Mandarin** (+22.3 percentage points, $p < 0.001$).
            * **Kimi-k3:** Restriction jumps from **7.3% in English to 19.0% in Mandarin** (+11.7 percentage points, $p < 0.001$).
        * **Unrestricted US Baseline:**
            * **OpenAI GPT-5.6-Luna** and **Google Gemini-3.6-Flash** maintain open access across both languages, restricting **at most 1.0%** of queries.
        * **Language-Triggered Censorship:**
            * Identical prompts querying the same sensitive topics yield substantially higher automated suppression solely by switching query language to Mandarin Chinese.
        """)
    st.divider()

    # -------------------------------------------------------------
    # 5. Analytical Drill-Down Tabs
    # -------------------------------------------------------------
    tab_mech, tab_stats, tab_events = st.tabs([
        "🔍 Restriction Mechanism (Tiers)",
        "📊 Statistical Rigor (McNemar & GEE)",
        "🏛️ Historical Events & Prompt Framing"
    ])

    # -------------------------------------------------------------
    # Tab 1: Mechanism & Response Taxonomy
    # -------------------------------------------------------------
    with tab_mech:
        st.markdown("### Restriction Mechanisms: DeepSeek's Hard Refusals vs. Kimi's Soft Evasion")
        with st.container(border=True):
            st.markdown(
            "**Taxonomy Insight:** While US models answer over 99% of inquiries without restriction in both languages, "
            "Chinese models enforce censorship through two fundamentally different architectural strategies:\n"
            "- **DeepSeek-v4-flash (Surge in Hard Refusals):** In Mandarin, DeepSeek's hard explicit refusals (Tier 2) surge more than fourfold "
            "from **9.0% in English to 36.7% in Mandarin** (issuing explicit termination statements), alongside steady soft evasion (Tier 1) in both languages (27.7% in EN, 22.3% in ZH).\n"
            "- **Kimi-k3 (Refusals & Soft Evasion):** Kimi incorporates 12 rule-based API content filter blocks as Hard Refusals (Tier 2) alongside narrative Soft Evasion (Tier 1), "
            "which rises from **5.7% in English to 16.7% in Mandarin** through moral generalities that omit documented historical facts."
            )
    
        col_chart_center, _ = st.columns([2.5, 0.5])
        with col_chart_center:
            st.markdown("#### Response Tier Distribution by Model & Language")
        
            if df_fs_loaded is not None:
                tier_records = []
                for (m_name, lang), group in df_fs_loaded.groupby(['model_name', 'language']):
                    n = len(group)
                    n_t0 = (group['tier'] == 0).sum()
                    n_t1 = (group['tier'] == 1).sum()
                    n_t2 = (group['tier'] == 2).sum()
                
                    m_label = str(m_name).split("/")[-1] + f" ({'US' if 'gpt' in m_name or 'gemini' in m_name else 'CN'})"
                    lang_label = "EN" if lang == "en" else "ZH"
                
                    tier_records.extend([
                        {"model": m_label, "language": lang_label, "tier": "Full Answer (Tier 0)", "tier_rank": 1, "share": n_t0 / n, "count": n_t0},
                        {"model": m_label, "language": lang_label, "tier": "Hard Refusal (Tier 2)", "tier_rank": 2, "share": n_t2 / n, "count": n_t2},
                        {"model": m_label, "language": lang_label, "tier": "Soft Evasion (Tier 1)", "tier_rank": 3, "share": n_t1 / n, "count": n_t1}
                    ])
            
                df_tiers_plot = pd.DataFrame(tier_records)
                df_tiers_plot = df_tiers_plot.sort_values(['model', 'language', 'tier_rank'])
                df_tiers_plot['cum_share'] = df_tiers_plot.groupby(['model', 'language'])['share'].cumsum()
                df_tiers_plot['mid_y'] = df_tiers_plot['cum_share'] - (df_tiers_plot['share'] / 2)
            
                model_order = ["gpt-5.6-luna (US)", "gemini-3.6-flash (US)", "deepseek-v4-flash (CN)", "kimi-k3 (CN)"]
                tier_order = ["Full Answer (Tier 0)", "Hard Refusal (Tier 2)", "Soft Evasion (Tier 1)"]
                tier_colors = ["#10B981", "#DC2626", "#F59E0B"]

                base_facet = alt.Chart(df_tiers_plot)

                tier_bars = base_facet.mark_bar(stroke="#0f172a", strokeWidth=1).encode(
                    x=alt.X('language:N', title=None, sort=["EN", "ZH"], axis=alt.Axis(labelAngle=0, labelFontSize=12, labelFontWeight='bold', ticks=False)),
                    y=alt.Y('share:Q', title='Share of Responses', axis=alt.Axis(format='.1%')),
                    color=alt.Color('tier:N', title=None, sort=tier_order, scale=alt.Scale(domain=tier_order, range=tier_colors), legend=alt.Legend(orient='bottom', direction='horizontal')),
                    order=alt.Order('tier_rank:O', sort='ascending'),
                    tooltip=[
                        alt.Tooltip('model:N', title='Model'),
                        alt.Tooltip('language:N', title='Language'),
                        alt.Tooltip('tier:N', title='Response Tier'),
                        alt.Tooltip('share:Q', title='Share', format='.1%'),
                        alt.Tooltip('count:Q', title='Responses (k)')
                    ]
                )

                text_labels = base_facet.mark_text(baseline='middle', align='center', fontSize=11, fontWeight='bold', color='white').encode(
                    x=alt.X('language:N', sort=["EN", "ZH"]),
                    y=alt.Y('mid_y:Q'),
                    text=alt.condition(alt.datum.share >= 0.05, alt.Text('share:Q', format='.1%'), alt.value(''))
                )

                combined_chart = (tier_bars + text_labels).properties(width=120, height=330).facet(
                    column=alt.Column('model:N', title=None, sort=model_order, header=alt.Header(labelFontSize=12, labelFontWeight='bold', labelColor='#E2E8F0'))
                ).configure_view(strokeWidth=0)

                st.altair_chart(combined_chart, use_container_width=True)
                st.caption("Taxonomy: Full Answer (Tier 0: Green), Hard Refusal (Tier 2: Red - including 12 API filter blocks), Soft Evasion (Tier 1: Amber).")

    # -------------------------------------------------------------
    # Tab 2: Statistical Rigor (Hypothesis Tests & Regression)
    # -------------------------------------------------------------
    with tab_stats:
        col_forest, col_gee = st.columns([1.35, 1])
    
        mc_path = os.path.join(TAB_DIR, "rq1_fs2400_tests_mcnemar.csv")
        df_mc_shared = pd.read_csv(mc_path) if os.path.exists(mc_path) else None

        with col_forest:
            st.markdown("### Matched-Pair Language Effects")
            st.caption("Forest plot of paired risk differences (ZH − EN) with 95% CIs (McNemar matched pairs).")

            if df_mc_shared is not None:
                def clean_scope_name(val):
                    if str(val).lower() == "pooled":
                        return "Pooled (All Models)"
                    base = str(val).split("/")[-1]
                    if "gpt" in base or "gemini" in base:
                        return f"{base} (US)"
                    return f"{base} (CN)"

                outcome_map = {
                    "restricted": "Restricted (Tier ≥ 1)",
                    "hard_refusal": "Hard Refusal (Tier = 2)"
                }

                df_fp = df_mc_shared.copy()
                df_fp["scope_label"] = df_fp["scope"].apply(clean_scope_name)
                df_fp["panel"] = df_fp["outcome"].map(outcome_map).fillna(df_fp["outcome"])
                df_fp["is_pooled"] = df_fp["scope"].str.lower() == "pooled"
            
                df_fp["rd_pct"] = (df_fp["risk_diff_zh_minus_en"] * 100).apply(lambda x: f"+{x:.1f}%" if x > 0 else f"{x:.1f}%")
                df_fp["ci_str"] = df_fp.apply(lambda r: f"[{r['rd_ci_lo']*100:.1f}%, {r['rd_ci_hi']*100:.1f}%]", axis=1)
                df_fp["p_str"] = df_fp.apply(
                    lambda r: "< 0.001 ***" if (r["p_holm"] < 0.001 or (pd.isna(r["p_holm"]) and r["p_raw"] < 0.001))
                    else f"{r['p_holm']:.3f} (n.s.)" if pd.notna(r["p_holm"])
                    else f"{r['p_raw']:.3f}", axis=1
                )

                scope_order = ["Pooled (All Models)", "gpt-5.6-luna (US)", "gemini-3.6-flash (US)", "deepseek-v4-flash (CN)", "kimi-k3 (CN)"]
                panel_order = ["Restricted (Tier ≥ 1)", "Hard Refusal (Tier = 2)"]

                base_fp = alt.Chart(df_fp)

                error_bars = base_fp.mark_rule(strokeWidth=2.2).encode(
                    y=alt.Y('scope_label:N', title=None, sort=scope_order, axis=alt.Axis(labelFontSize=11, ticks=False, labelLimit=240)),
                    x=alt.X('rd_ci_lo:Q', title='Risk Diff (ZH − EN, 95% CI)', axis=alt.Axis(format='.1%', tickCount=4)),
                    x2='rd_ci_hi:Q',
                    color=alt.condition(alt.datum.is_pooled, alt.value('#0284C7'), alt.value('#EA580C'))
                )

                points = base_fp.mark_circle(size=85, opacity=1).encode(
                    y=alt.Y('scope_label:N', sort=scope_order),
                    x=alt.X('risk_diff_zh_minus_en:Q'),
                    color=alt.condition(alt.datum.is_pooled, alt.value('#0284C7'), alt.value('#EA580C')),
                    tooltip=[
                        alt.Tooltip('scope_label:N', title='Model / Scope'),
                        alt.Tooltip('panel:N', title='Target Outcome'),
                        alt.Tooltip('rd_pct:N', title='Risk Difference (ZH − EN)'),
                        alt.Tooltip('ci_str:N', title='95% Confidence Interval'),
                        alt.Tooltip('p_str:N', title='Adjusted p-value')
                    ]
                )

                text_vals = base_fp.mark_text(dy=-11, fontSize=11, fontWeight='bold').encode(
                    y=alt.Y('scope_label:N', sort=scope_order),
                    x=alt.X('risk_diff_zh_minus_en:Q'),
                    text='rd_pct:N',
                    color=alt.condition(alt.datum.is_pooled, alt.value('#0284C7'), alt.value('#EA580C'))
                )

                zero_ref = base_fp.mark_rule(color='#94A3B8', strokeDash=[4, 4], strokeWidth=1.2).encode(x=alt.datum(0))

                forest_chart = (zero_ref + error_bars + points + text_vals).properties(width=185, height=260).facet(
                    column=alt.Column('panel:N', title=None, sort=panel_order, header=alt.Header(labelFontSize=11, labelFontWeight='bold', labelColor='#E2E8F0'))
                ).configure_view(strokeWidth=0)

                st.altair_chart(forest_chart, use_container_width=True)
                st.caption("* Pooled models in sky blue; individual models in orange evaluated via Holm-adjusted McNemar test.")
            
        with col_gee:
            st.markdown("### Clustered Regression (GEE)")
            st.caption("Multivariate logistic model controlling for intra-event clustering across 60 historical topics (N = 2,400).")
        
            gee_path = os.path.join(TAB_DIR, "rq1_fs2400_tests_gee.csv")
            if os.path.exists(gee_path):
                df_gee = pd.read_csv(gee_path)
                clean_gee = df_gee[(df_gee["spec"] == "main_effects") & (df_gee["term"] != "Intercept")].copy()
                term_map = {
                    "lang_zh": "Mandarin Prompt (vs. English)",
                    "origin_cn": "Chinese Origin (vs. US)",
                    "event_cn": "China-Centric Event (vs. US Event)"
                }
                clean_gee["Predictor"] = clean_gee["term"].map(term_map).fillna(clean_gee["term"])
                clean_gee["Target Outcome"] = clean_gee["outcome"].map({
                    "restricted": "Total Restriction (Tier ≥ 1)",
                    "hard_refusal": "Hard Refusal Only (Tier = 2)"
                })
                clean_gee["Odds Ratio (OR)"] = clean_gee["odds_ratio"].apply(lambda x: f"{x:.2f}×")
                clean_gee["95% CI"] = clean_gee.apply(lambda r: f"[{r['or_ci_lo']:.2f}, {r['or_ci_hi']:.2f}]", axis=1)
                clean_gee["Significance (p-value)"] = clean_gee["p"].apply(lambda p: "< 0.001 ***" if p < 0.001 else f"{p:.3f}")

                gee_display = clean_gee[["Target Outcome", "Predictor", "Odds Ratio (OR)", "95% CI", "Significance (p-value)"]]
                st.dataframe(style_uniform_table(gee_display, text_cols=["Target Outcome", "Predictor"]), use_container_width=True, hide_index=True)
                st.info(
                    "**Key Statistical Finding:** Querying in Mandarin more than doubles restriction likelihood (**OR = 2.38×**, $p < 0.001$) "
                    "even after controlling for model developer origin and topic sensitivity."
                )

    # -------------------------------------------------------------
    # Tab 3: Systemic Distribution & Framing
    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # Tab 3: Systemic Distribution & Framing
    # -------------------------------------------------------------
    with tab_events:
        st.markdown("### Event-Level Analysis: Cross-Lingual Restriction Gap across Historical Topics")
    
        if df_fs_loaded is not None:
            df_fs = df_fs_loaded.copy()
            df_fs['is_restricted'] = (df_fs['tier'] >= 1).astype(int)
        
            ev_summary = df_fs.groupby(['event_id', 'event_set', 'language'])['is_restricted'].mean().reset_index()
            ev_piv = ev_summary.pivot(index=['event_id', 'event_set'], columns='language', values='is_restricted').reset_index()
            ev_piv['gap'] = ev_piv['zh'] - ev_piv['en']
            ev_piv['event_name'] = ev_piv['event_id'].map(EVENT_DICT)
            ev_piv['origin_label'] = ev_piv['event_set'].map({'china': 'China-Centric Event', 'us': 'US-Centric Event'})
            ev_piv = ev_piv.sort_values('gap').reset_index(drop=True)
            ev_piv['rank'] = ev_piv.index + 1
            ev_piv['en_pct'] = (ev_piv['en'] * 100).round(1).astype(str) + "%"
            ev_piv['zh_pct'] = (ev_piv['zh'] * 100).round(1).astype(str) + "%"
            ev_piv['gap_pct'] = (ev_piv['gap'] * 100).apply(lambda x: f"+{x:.1f}%" if x > 0 else f"{x:.1f}%")

            c_pos, c_zero, c_neg = st.columns(3)
            c_pos.metric(label="Higher Restriction in Mandarin", value="65.0%", help="39 of 60 events")
            c_zero.metric(label="Equal Restriction", value="20.0%", help="12 of 60 events")
            c_neg.metric(label="Higher Restriction in English", value="15.0%", help="9 of 60 events")

            scatter = alt.Chart(ev_piv).mark_circle(size=95, opacity=0.88).encode(
                x=alt.X('rank:Q', title='Historical Events (Ranked from Lowest to Highest Gap)'),
                y=alt.Y('gap:Q', title='Restriction Rate Gap (Mandarin − English)', axis=alt.Axis(format='.1%')),
                color=alt.Color('origin_label:N', title='Event Origin', scale=alt.Scale(domain=['China-Centric Event', 'US-Centric Event'], range=['#00D2FF', '#FF3366'])),
                tooltip=[
                    alt.Tooltip('event_name:N', title='Historical Event'),
                    alt.Tooltip('event_id:N', title='Event ID'),
                    alt.Tooltip('origin_label:N', title='Topic Origin'),
                    alt.Tooltip('en_pct:N', title='English Restriction'),
                    alt.Tooltip('zh_pct:N', title='Mandarin Restriction'),
                    alt.Tooltip('gap_pct:N', title='Language Gap (ZH − EN)')
                ]
            ).properties(height=400)

            zero_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(color='#94A3B8', strokeDash=[5, 5], strokeWidth=1.5).encode(y='y:Q')
            st.altair_chart(scatter + zero_line, use_container_width=True)
        else:
            gap_path = os.path.join(FIG_DIR, "rq1_fs2400_event_gap.png")
            if os.path.exists(gap_path):
                st.image(gap_path, use_container_width=True)
            else:
                st.warning("RQ1 data is unavailable. Add `data/processed/rq1/tiers_fs.csv`.")
        # -------------------------------------------------------------
        # Interactive Case Explorer (Compact Table + Dynamic Rationale on Click)
        # -------------------------------------------------------------
        st.markdown("---")
        with st.expander("🔎 Interactive Benchmark Explorer", expanded=True):
            if df_fs_loaded is not None:
                df_fs = df_fs_loaded.copy()
                df_fs['event_topic'] = df_fs['event_id'].map(EVENT_DICT)
                df_fs['topic_origin'] = df_fs['event_set'].map({'china': 'China-Centric', 'us': 'US-Centric'}).fillna(df_fs['event_set'])
            
                tier_label_map = {
                    0: "Tier 0: Full Answer", 
                    1: "Tier 1: Soft Evasion", 
                    2: "Tier 2: Hard Refusal"
                }
                df_fs['tier_name'] = df_fs['tier'].map(tier_label_map)

                # Row 1 Filters
                f1, f2, f3, f4 = st.columns(4)
                with f1:
                    sel_model = st.multiselect("Models", options=df_fs["model_name"].unique(), default=df_fs["model_name"].unique())
                with f2:
                    sel_lang = st.multiselect("Languages", options=["en", "zh"], default=["en", "zh"])
                with f3:
                    sel_frame = st.multiselect("Framing Strategies", options=sorted(df_fs["frame_id"].unique()), default=sorted(df_fs["frame_id"].unique()))
                with f4:
                    all_tiers = ["Tier 0: Full Answer", "Tier 1: Soft Evasion", "Tier 2: Hard Refusal"]
                    sel_tiers = st.multiselect("Response Tiers", options=all_tiers, default=all_tiers)

                # Row 2 Filters
                f5, f6 = st.columns([1, 2])
                with f5:
                    sel_origin = st.radio("Event Origin Filter:", ["All Topics", "China-Centric", "US-Centric"], horizontal=True)
                with f6:
                    if sel_origin == "China-Centric":
                        topic_choices = sorted(df_fs[df_fs["topic_origin"] == "China-Centric"]["event_topic"].dropna().unique())
                    elif sel_origin == "US-Centric":
                        topic_choices = sorted(df_fs[df_fs["topic_origin"] == "US-Centric"]["event_topic"].dropna().unique())
                    else:
                        topic_choices = sorted(df_fs["event_topic"].dropna().unique())

                    sel_event = st.selectbox("Historical Event Topic:", options=["All Events in Scope"] + topic_choices)

                # Filter data
                filtered = df_fs[
                    (df_fs["model_name"].isin(sel_model)) &
                    (df_fs["language"].isin(sel_lang)) &
                    (df_fs["frame_id"].isin(sel_frame)) &
                    (df_fs["tier_name"].isin(sel_tiers))
                ].reset_index(drop=True)

                if sel_origin != "All Topics":
                    filtered = filtered[filtered["topic_origin"] == sel_origin].reset_index(drop=True)
                if sel_event != "All Events in Scope":
                    filtered = filtered[filtered["event_topic"] == sel_event].reset_index(drop=True)

                # Compact table columns
                compact_cols = ["event_id", "topic_origin", "event_topic", "model_name", "language", "frame_id", "tier_name"]
                table_display = filtered[compact_cols].rename(columns={
                    "event_id": "Event ID",
                    "topic_origin": "Origin",
                    "event_topic": "Historical Event",
                    "model_name": "Model",
                    "language": "Lang",
                    "frame_id": "Frame",
                    "tier_name": "Assigned Tier"
                })

                # Interactive selection dataframe
                selection = st.dataframe(
                    table_display,
                    use_container_width=True,
                    height=380,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row"
                )

                st.caption(f"Showing {len(filtered):,} records. **Tip:** Click any row in the table above to view the full judge evaluation rationale.")

                # Unified Case Evaluation & Translation Display
                selected_rows = selection.selection.rows if hasattr(selection, "selection") else []
                if selected_rows:
                    idx = selected_rows[0]
                    row_data = filtered.iloc[idx]
                    ev_id = row_data["event_id"]
                
                    tier_color_badge = {
                        "Tier 0: Full Answer": "🟢 Full Answer (Tier 0)",
                        "Tier 1: Soft Evasion": "🟡 Soft Evasion (Tier 1)",
                        "Tier 2: Hard Refusal": "🔴 Hard Refusal (Tier 2)"
                    }.get(row_data["tier_name"], row_data["tier_name"])

                    st.markdown("#### 📝 Case Evaluation & Ground-Truth Reference")
                
                    col_eval, col_ref = st.columns([1.1, 1.2])
                    with col_eval:
                        st.info(
                            f"**Event:** `{ev_id}` — {row_data['event_topic']} ({row_data['topic_origin']})  \n"
                            f"**Query Configuration:** Model: `{row_data['model_name']}` | Lang: `{row_data['language'].upper()}` | Frame: `{row_data['frame_id']}`  \n"
                            f"**Assigned Tier:** {tier_color_badge}\n\n"
                            f"**Judge Rationale:**\n> {row_data.get('tier_rationale', 'No rationale provided.')}"
                        )
                
                    with col_ref:
                        if ev_id in fact_sheet_data:
                            ev_info = fact_sheet_data[ev_id]
                            if "verified_factual_anchors" in ev_info:
                                anchors = ev_info.get("verified_factual_anchors", [])
                                anchors_list = "\n".join([f"* {anchor}" for anchor in anchors])
                                caution_text = ev_info.get("judging_caution", "None")
                                sources_text = ", ".join(ev_info.get("evidence_ids", []))
                                scope_date = ev_info.get("scope_date", "")
                            else:
                                claims = [c.get("claim", "") for c in ev_info.get("atomic_claims", [])]
                                anchors_list = "\n".join([f"* {c}" for c in claims[:4]])
                                caution_text = "Standard historical claim check."
                                sources_text = ev_info.get("wiki_url", "Fact Sheet")
                                scope_date = "Historical Reference"

                            st.success(
                                f"**Ground-Truth Fact Sheet ({scope_date})**\n\n"
                                f"**Verified Factual Anchors:**\n{anchors_list}\n\n"
                                f"⚠️ **Judging Caution:** {caution_text}\n\n"
                                f"📚 **Mapped Evidence Sources:** `{sources_text}`"
                            )
                        else:
                            st.warning(f"Ground-truth reference anchors not found for `{ev_id}`.")

                    # On-Demand Translation Viewer
                    st.markdown("---")
                    raw_resp_id = str(row_data.get("response_id", "")).strip().lower()
                    event_id = str(row_data.get("event_id", "")).strip().lower()
                    frame_id = str(row_data.get("frame_id", "")).strip().lower()
                    lang = str(row_data.get("language", "")).strip().lower()
                    m_slug = str(row_data.get("model_name", "")).split("/")[-1].strip().lower()

                    # Multi-strategy key lookup
                    suffix_key = f"{event_id}-{frame_id}-{lang}"
                    composite_key = f"{m_slug}_{event_id}_{frame_id}_{lang}"

                    trans_info = (
                        translation_lookup.get(raw_resp_id) or 
                        translation_lookup.get(suffix_key) or 
                        translation_lookup.get(composite_key)
                    )

                    if trans_info:
                        with st.expander("🌐 View Prompt & Model Response (With English Translation)", expanded=True):
                            st.markdown(f"**Original Prompt:** `{trans_info['prompt_text']}`")
                            tab_zh, tab_en = st.tabs(["🇨🇳 Original Response (Mandarin)", "🇬🇧 Translated Response (English)"])
                            with tab_zh:
                                st.markdown(trans_info["original_response"])
                            with tab_en:
                                # FIX: Fallback if translation text is empty/nan
                                trans_text = trans_info["translated_response"]
                                if not trans_text or trans_text.lower() == "nan" or trans_text.strip() == "":
                                    st.markdown("*No independent translation was generated for this hard refusal (the model issued a direct refusal statement: 'I'm sorry, I haven't learned how to answer this question yet').*")
                                else:
                                    st.markdown(trans_text)
                    elif lang == "zh":
                        with st.expander("🌐 View Prompt & Model Response", expanded=False):
                            st.warning(f"Translation record missing for ID `{raw_resp_id}` (Keys tried: `{suffix_key}`, `{composite_key}`). Total records loaded: {len(translation_lookup):,}")
                    else:
                        with st.expander("🌐 View Prompt & Model Response", expanded=False):
                            st.info("This query was submitted in English (baseline). English-to-English translation is not required.")

                # Export Artifacts Row (PDF Source Register Only)
                st.markdown("---")
                if os.path.exists(PDF_REGISTER_PATH):
                    with open(PDF_REGISTER_PATH, "rb") as pf:
                        st.download_button(
                            label="📄 Download Source Register (PDF)",
                            data=pf,
                            file_name="Silence_of_the_LLMs_Fact_Sheet_and_Source_Register.pdf",
                            mime="application/pdf",
                            help="Complete 25-page evidence register with primary diplomatic records and archival sources."
                        )
            else:
                st.info("Place `tiers_fs.csv` in `data/processed/rq1/` to enable prompt-level case exploration.")


st.set_page_config(page_title="Silence of the LLMs", page_icon="📊", layout="wide")
st.markdown(
    """
    <style>
    .stApp { background: #f7f9fc; color: #203047; }
    .block-container { max-width: 1180px; padding-top: 2rem; padding-bottom: 4rem; }
    .dashboard-hero {
        padding: 2.1rem 2.5rem;
        margin: 0 0 1.6rem;
        border-radius: 22px;
        background: linear-gradient(120deg, #142b46, #19546a 72%, #1b776d);
        box-shadow: 0 14px 35px rgba(20, 43, 70, .13);
        color: #ffffff;
    }
    .dashboard-hero .eyebrow {
        font-size: .78rem; font-weight: 700; letter-spacing: .16em;
        text-transform: uppercase; color: #a5e9dc; margin-bottom: .45rem;
    }
    .dashboard-hero h1 { color: #ffffff; font-size: 2.55rem; margin: 0; line-height: 1.16; }
    .dashboard-hero p { color: #d9e7ed; font-size: 1.06rem; margin: .8rem 0 0; }
    [data-testid="stMetric"] {
        padding: 1.1rem 1.25rem;
        background: #ffffff;
        border: 1px solid #e4ebf2;
        border-top: 3px solid #23a594;
        border-radius: 14px;
        box-shadow: 0 5px 16px rgba(20, 43, 70, .045);
        min-height: 122px;
    }
    [data-testid="stMetricLabel"] { color: #53667a; font-size: .93rem; }
    [data-testid="stMetricValue"] { color: #172e49; }
    .nav-label {
        margin: .2rem 0 .65rem;
        color: #176d71;
        font-size: .8rem;
        font-weight: 750;
        letter-spacing: .12em;
        text-transform: uppercase;
    }
    .stApp div[data-testid="stButton"] button {
        min-height: 52px;
        padding: .7rem 1rem;
        border-radius: 12px;
        font-size: 1rem;
        font-weight: 650;
    }
    .stApp div[data-testid="stButton"] button[kind="primary"] {
        background-color: #176d71;
        border-color: #176d71;
        color: #ffffff;
    }
    .stApp div[data-testid="stButton"] button[kind="secondary"] {
        background-color: #e3f2f0;
        border: 1px solid #9bcac5;
        color: #194b53;
    }
    .stApp div[data-testid="stButton"] button[kind="secondary"]:hover {
        background-color: #cce8e3;
        border-color: #176d71;
        color: #123f46;
    }
    /* Inputs in the label filter and response explorer. */
    .stApp [data-testid="stSelectbox"] {
        padding: .65rem .8rem .8rem;
        border: 2px solid #63a9a5;
        border-radius: 14px;
        background: #e5f3f0;
        box-shadow: 0 4px 12px rgba(23, 109, 113, .1);
    }
    .stApp [data-testid="stSelectbox"]:focus-within {
        border-color: #176d71;
        background: #d2ebe7;
        box-shadow: 0 0 0 4px rgba(35, 165, 148, .2);
    }
    .stApp [data-testid="stSelectbox"] label p {
        color: #184e57;
        font-weight: 700;
        font-size: 1rem;
    }
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background: #dcefeb !important;
        border: 2px solid #60aaa5 !important;
        border-radius: 12px !important;
        min-height: 56px;
        box-shadow: 0 3px 9px rgba(20, 85, 88, .09);
    }
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div {
        background: #f0faf8 !important;
        border-color: #176d71 !important;
        box-shadow: 0 0 0 3px rgba(35, 165, 148, .2) !important;
    }
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"] * {
        color: #173f48;
    }
    [data-testid="stAlert"] { border-radius: 12px; }
    h2, h3 { color: #203047; letter-spacing: -.025em; }
    .rq2-intro {
        padding: 1.5rem 1.8rem;
        margin: .5rem 0 1.35rem;
        border: 1px solid #dce8ed;
        border-left: 5px solid #23a594;
        border-radius: 14px;
        background: linear-gradient(110deg, #ffffff, #ebf7f5);
    }
    .rq2-intro .eyebrow, .section-kicker {
        font-size: .76rem; font-weight: 750; letter-spacing: .12em;
        text-transform: uppercase; color: #127c75;
    }
    .rq2-intro h2 { margin: .25rem 0 .45rem; font-size: 1.9rem; }
    .rq2-intro p { color: #53667a; margin: 0; line-height: 1.6; }
    .study-strip {
        display: flex; flex-wrap: wrap; gap: .6rem; margin: .4rem 0 1.1rem;
    }
    .study-strip span {
        padding: .48rem .75rem; background: #e9f4f4;
        border: 1px solid #d3e8e6; border-radius: 20px;
        color: #20535b; font-size: .88rem; font-weight: 600;
    }
    .takeaway {
        background: #f0f7fa; border-left: 4px solid #177a8b;
        border-radius: 10px; padding: 1.1rem 1.25rem;
        line-height: 1.65; color: #264158;
    }
    .takeaway strong { color: #173a53; }
    @media (max-width: 700px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; }
        .dashboard-hero { padding: 1.5rem; }
        .dashboard-hero h1 { font-size: 2rem; }
        .stApp div[data-testid="stButton"] button {
            min-height: 46px; padding: .55rem .5rem; font-size: .92rem;
        }
    }
    </style>
    <div class="dashboard-hero">
      <div class="eyebrow">Research dashboard · RQ1–RQ4</div>
      <h1>Silence of the LLMs</h1>
      <p>Explore model responses, factual accuracy and human review.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="nav-label">Choose a research question</div>', unsafe_allow_html=True)
with st.container(border=True):
    selected_rq = navigation(["RQ1", "RQ2", "RQ3", "RQ4"], "selected_rq")

if selected_rq == "RQ1":
    render_rq1()
elif selected_rq == "RQ3":
    render_rq3()
elif selected_rq == "RQ4":
    render_rq4()
elif selected_rq == "RQ2":
    data_dir = Path(__file__).parent / "data"
    preferred_csv_path = data_dir / "processed" / "rq2" / "rq2_results.csv"
    legacy_csv_path = data_dir / "rq2_results.csv"
    csv_path = preferred_csv_path if preferred_csv_path.is_file() else legacy_csv_path
    responses = pd.read_csv(csv_path, keep_default_na=False)
    counts = (
        responses.groupby(["model_name", "final_class"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=LABEL_ORDER, fill_value=0)
    )
    language_counts = (
        responses.groupby(["language", "final_class"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=LABEL_ORDER, fill_value=0)
        .rename(index={"en": "English", "zh": "Mandarin"})
    )
    st.markdown(
        """
        <div class="rq2-intro">
          <div class="eyebrow">Research question 02 · Factual accuracy</div>
          <h2>Explore and present RQ2</h2>
          <p>See the overall findings, compare model and language results, or
          inspect how an individual answer was classified.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="nav-label">Explore RQ2</div>', unsafe_allow_html=True)
    with st.container(border=True):
        selected_section = navigation(
            ["Full analysis", "Model & language comparisons", "Filter by label",
             "Explore a response", "Presentation view"],
            "selected_rq2_section",
            [1.2, 2.4, 1.35, 1.7, 1.7],
        )

    if selected_section == "Model & language comparisons":
        st.subheader("Select a model and language")
        model_col, language_col = st.columns(2)
        with model_col:
            selected_model = st.selectbox(
                "Choose a model", counts.index.tolist(), key="rq2_compare_model"
            )
        with language_col:
            selected_language = st.selectbox(
                "Choose a language", language_counts.index.tolist(), key="rq2_compare_language"
            )

        model_assessable = int(counts.loc[selected_model, "Factual"] + counts.loc[selected_model, "Non-factual"])
        model_non_factual = int(counts.loc[selected_model, "Non-factual"])
        language_assessable = int(
            language_counts.loc[selected_language, "Factual"]
            + language_counts.loc[selected_language, "Non-factual"]
        )
        language_non_factual = int(language_counts.loc[selected_language, "Non-factual"])
        with model_col:
            st.metric(
                f"{selected_model}: non-factual among assessable",
                f"{model_non_factual / model_assessable:.1%}" if model_assessable else "N/A",
            )
        with language_col:
            st.metric(
                f"{selected_language}: non-factual among assessable",
                f"{language_non_factual / language_assessable:.1%}" if language_assessable else "N/A",
            )
        st.caption("Non-assessable responses are excluded from both rates.")

        st.divider()
        st.subheader("RQ2 results by model")
        summary = counts.copy()
        summary["Assessable responses"] = counts["Factual"] + counts["Non-factual"]
        summary["Non-factual rate (%)"] = (
            100 * counts["Non-factual"]
            / summary["Assessable responses"].where(summary["Assessable responses"].ne(0))
        ).round(1)
        st.dataframe(summary, use_container_width=True)
        st.bar_chart(counts, stack=True)
        st.caption("Each model contributed 600 responses. Counts include blank responses classified by rule.")

        st.divider()
        st.subheader("RQ2 results by language")
        language_summary = language_counts.copy()
        language_summary["Assessable responses"] = (
            language_counts["Factual"] + language_counts["Non-factual"]
        )
        language_summary["Non-factual rate (%)"] = (
            100 * language_counts["Non-factual"]
            / language_summary["Assessable responses"].where(
                language_summary["Assessable responses"].ne(0)
            )
        ).round(1)
        st.dataframe(language_summary, use_container_width=True)
        st.bar_chart(language_counts, stack=True)
        st.caption("Each language contributed 1,200 responses. Counts show final RQ2 classifications.")
        st.caption(
            "English: 35 of 1,167 assessable responses were non-factual (3.0%). "
            "Mandarin: 12 of 1,083 (1.1%). Non-assessable responses are excluded."
        )
        st.info(
            "These are overall rates. In the matched comparison of English and "
            "Mandarin answers to the same questions, the analysis did not find "
            "a clear difference in non-factual outcomes (exact McNemar p = 1.000)."
        )

    if selected_section == "Filter by label":
        st.markdown('<div class="section-kicker">Browse the dataset</div>', unsafe_allow_html=True)
        st.subheader("Filter responses by classification")
        st.caption("Choose a label, browse the matching rows, then open a response below.")
        with st.container(border=True):
            label = st.selectbox(
                "Classification",
                ["All", "Factual", "Non-factual", "Non-assessable"],
                key="rq2_label_filter",
            )
        filtered = (
            responses
            if label == "All"
            else responses[responses["final_class"] == label]
        )

        result_col, context_col = st.columns([1, 3], gap="medium")
        result_col.metric("Matching responses", f"{len(filtered):,}")
        context_col.info(
            f"Showing **{label.lower()}** responses from the 2,400-row RQ2 dataset."
            if label != "All"
            else "Showing all responses. Select a classification to narrow the table."
        )
        st.markdown("#### Matching records")
        st.dataframe(
            filtered[
                ["response_id", "model_name", "language",
                 "frame_id", "prompt_id", "final_class"]
            ].rename(columns={
                "response_id": "Response ID",
                "model_name": "Model",
                "language": "Language",
                "frame_id": "Framing",
                "prompt_id": "Prompt ID",
                "final_class": "Classification",
            }),
            use_container_width=True,
            hide_index=True,
            height=420,
        )

        if not filtered.empty:
            st.divider()
            response_id = st.selectbox(
                "Select a response to read",
                filtered["response_id"].astype(str).tolist(),
                key="rq2_filtered_response",
            )
            row = filtered[
                filtered["response_id"].astype(str) == response_id
            ].iloc[0]
            response_card(row)

    if selected_section == "Presentation view":
        counts_all = responses["final_class"].value_counts()
        factual = int(counts_all.get("Factual", 0))
        non_factual = int(counts_all.get("Non-factual", 0))
        non_assessable = int(counts_all.get("Non-assessable", 0))
        assessable = factual + non_factual

        st.header("RQ2 · Factual accuracy")
        st.write("Classification of responses across all four models.")

        col1, col2, col3 = st.columns(3)
        col1.metric("Responses", f"{len(responses):,}")
        col2.metric("Non-factual", f"{non_factual:,}")
        col3.metric(
            "Non-factual among assessable",
            f"{non_factual / assessable:.1%}" if assessable else "N/A",
        )

        st.bar_chart(
            counts[["Factual", "Non-factual", "Non-assessable"]],
            stack=True,
        )
        st.caption(
            f"{non_assessable:,} non-assessable responses are excluded "
            "from the non-factual rate. Classifications come from the RQ2 CSV."
        )
    if selected_section == "Explore a response":
        st.markdown('<div class="section-kicker">Response explorer</div>', unsafe_allow_html=True)
        st.subheader("Explore an individual response")
        st.caption("Make your selections from left to right to find a specific answer.")
        with st.container(border=True):
            model_col, language_col = st.columns(2, gap="medium")
            with model_col:
                model = st.selectbox("1 · Model", sorted(responses["model_name"].unique()))
            model_rows = responses[responses["model_name"] == model]
            with language_col:
                language = st.selectbox("2 · Language", sorted(model_rows["language"].unique()))
            language_rows = model_rows[model_rows["language"] == language]
            frame_col, prompt_col = st.columns(2, gap="medium")
            with frame_col:
                framing = st.selectbox("3 · Prompt framing", sorted(language_rows["frame_id"].unique()))
            matching_rows = language_rows[language_rows["frame_id"] == framing]
            with prompt_col:
                prompt_id = st.selectbox("4 · Prompt ID", sorted(matching_rows["prompt_id"].unique()))
        selected = matching_rows[matching_rows["prompt_id"] == prompt_id].iloc[0]
        response_card(selected)

    if selected_section == "Full analysis":
        st.markdown('<div class="section-kicker">01 / Dataset overview</div>', unsafe_allow_html=True)
        st.subheader("How often do LLM answers contain factual errors?")
        st.markdown(
            """
            <div class="study-strip">
              <span>60 historical events</span><span>5 prompt framings</span>
              <span>2 languages</span><span>4 models</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        overview_cols = st.columns(4)
        overview_cols[0].metric("Responses classified", "2,400")
        overview_cols[1].metric("Mistral-labelled non-factual", "47")
        overview_cols[2].metric("Non-assessable", "150")
        overview_cols[3].metric("Non-factual among assessable", "2.1%")
        st.caption("47 non-factual responses out of 2,250 assessable responses, as labelled by Mistral. The 150 non-assessable responses are excluded from this rate.")
        st.subheader("Final RQ2 labels across all responses")
        chart_col, note_col = st.columns([3, 1.25], gap="large")
        with chart_col:
            with st.container(border=True):
                st.altair_chart(label_chart([2203, 47, 150]), use_container_width=True)
        with note_col:
            st.markdown(
                """
                <div class="takeaway">
                  <strong>How to read this chart</strong><br>
                  Most responses were labelled factual. The chart includes
                  non-assessable answers, but the 2.1% non-factual rate
                  excludes them. Hover over a bar for its exact count.
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.divider()
        st.subheader("Human-reviewed sample (300 responses)")
        human_cols = st.columns(3)
        human_cols[0].metric("Human consensus: factual", "272")
        human_cols[1].metric("Human consensus: non-factual", "4")
        human_cols[2].metric("Human consensus: non-assessable", "24")
        with st.container(border=True):
            st.altair_chart(label_chart([272, 4, 24]), use_container_width=True)
        st.metric("Human-reviewed non-factual rate among assessable responses", "1.45%")
        st.caption("4 non-factual responses out of 276 assessable responses in the human-reviewed sample. The 24 non-assessable responses are excluded.")
        st.info(
            "The 2.1% rate comes from the final RQ2 classifications of all 2,400 responses "
            "(2,388 Mistral judgments and 12 blank responses classified by rule). "
            "The 1.45% rate comes from human consensus on a 300-response sample. "
            "These rates alone do not show how accurately Mistral agreed with the human reviewers."
        )
        st.divider()
        st.subheader("Mistral versus human consensus")
        st.write("This comparison uses the same 300 responses reviewed by people, matched response by response with Mistral’s labels.")
        agreement_cols = st.columns(4)
        agreement_cols[0].metric("Matching labels", "293 / 300")
        agreement_cols[1].metric("Observed agreement", "97.7%")
        agreement_cols[2].metric("Gwet's AC1", "0.9744")
        agreement_cols[3].metric("Cohen's kappa", "0.8669")
        st.caption("Gwet's AC1 and Cohen's kappa compare Mistral with final human consensus on the same 300 responses.")
        st.caption(
            "Only 4 of the 300 human-reviewed responses were non-factual. "
            "Overall agreement does not, by itself, show how well Mistral detected that small group."
        )
        st.divider()
        st.subheader("Did prompt framing change factual accuracy?")
        st.write(
            "Across the five prompt framings, the overall mix of factual, "
            "non-factual and non-assessable labels showed no clear difference."
        )
        st.metric("Overall framing comparison", "p = 0.640")
        st.caption(
            "Three-label chi-square test: χ²(8) = 6.065. "
            "A matched comparison of non-factual outcomes also found "
            "no clear difference (p = 0.281)."
        )
        st.divider()
        st.subheader("Did framing affect whether answers could be assessed?")
        st.write(
            "The matched analysis found a difference in assessability across "
            "the five prompt framings."
        )
        st.metric("Matched assessability comparison", "p = 0.003")
        st.caption(
            "Cochran’s Q test compared the five framings for matched prompts. "
            "This result concerns whether an answer could be assessed for factuality, "
            "not whether an assessable answer was factual."
        )
        st.divider()
        st.subheader("RQ2: key findings")
        st.markdown(
            """
            - **47 of 2,250 assessable responses (2.1%)** were classified
              as non-factual in the full dataset.
            - In the **300-response human-reviewed sample**, 4 of 276
              assessable responses (1.45%) were non-factual.
            - Mistral matched human consensus on **293 of 300 labels**.
              Only four responses had a human non-factual label, so overall
              agreement alone does not establish how well it detected errors.
            - Prompt framing showed a difference in **assessability**,
              but no clear difference in **non-factual outcomes** in the
              matched analysis.
            """
        )
