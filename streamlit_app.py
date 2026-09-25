from pathlib import Path

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
        st.session_state[state_key] = "RQ2" if state_key == "selected_rq" else labels[0]
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

if selected_rq == "RQ2":
    csv_path = Path(__file__).parent / "data" / "rq2_results.csv"
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
