from pathlib import Path

import pandas as pd
import streamlit as st

st.title("Silence of the LLMs")
st.write("Explore results for RQ1, RQ2, RQ3 and RQ4.")

rq1, rq2, rq3, rq4 = st.tabs(["RQ1", "RQ2", "RQ3", "RQ4"])

with rq2:
    csv_path = Path(__file__).parent / "data" / "rq2_results.csv"
    responses = pd.read_csv(csv_path, keep_default_na=False)
    st.subheader("Explore and present RQ2")

    full_tab, compare_tab, filter_tab, explore_tab, present_tab = st.tabs(
        ["Full analysis", "Model & language comparisons", "Filter by label", "Explore a response", "Presentation view"]
    )

    with compare_tab:
        counts = (
            responses.groupby(["model_name", "final_class"])
            .size()
            .unstack(fill_value=0)
            .reindex(columns=["Factual", "Non-factual", "Non-assessable"], fill_value=0)
        )
        language_counts = (
            responses.groupby(["language", "final_class"])
            .size()
            .unstack(fill_value=0)
            .reindex(columns=["Factual", "Non-factual", "Non-assessable"], fill_value=0)
            .rename(index={"en": "English", "zh": "Mandarin"})
        )

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

    with filter_tab:
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

        st.write(f"**{len(filtered):,} matching responses**")
        st.dataframe(
            filtered[
                ["response_id", "model_name", "language",
                 "frame_id", "prompt_id", "final_class"]
            ],
            use_container_width=True,
            hide_index=True,
        )

        if not filtered.empty:
            response_id = st.selectbox(
                "Read a matching response",
                filtered["response_id"].astype(str).tolist(),
                key="rq2_filtered_response",
            )
            row = filtered[
                filtered["response_id"].astype(str) == response_id
            ].iloc[0]
            st.write("**Prompt:**", row["prompt_text"])
            st.write(
                "**Response:**",
                row["original_response"] or "No response text was returned.",
            )
            st.write("**Classification:**", row["final_class"])

    with present_tab:
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
    with explore_tab:
        st.subheader("Explore an individual response")
        model = st.selectbox("Model", sorted(responses["model_name"].unique()))
        model_rows = responses[responses["model_name"] == model]

        language = st.selectbox("Language", sorted(model_rows["language"].unique()))
        language_rows = model_rows[model_rows["language"] == language]

        framing = st.selectbox("Prompt framing", sorted(language_rows["frame_id"].unique()))
        matching_rows = language_rows[language_rows["frame_id"] == framing]

        prompt_id = st.selectbox("Prompt ID", sorted(matching_rows["prompt_id"].unique()))
        selected = matching_rows[matching_rows["prompt_id"] == prompt_id].iloc[0]

        st.write("**Prompt:**", selected["prompt_text"])
        st.write("**Response:**", selected["original_response"] or "No response text was returned.")
        st.metric("Final RQ2 classification", selected["final_class"])

    with full_tab:
        st.subheader("RQ2 · Factual accuracy")
        st.write("How often do LLM answers contain factual errors?")
        st.metric("Responses classified in RQ2", "2,400")
        st.metric("Mistral-labelled non-factual", "47")
        st.metric("Responses classified non-assessable", "150")
        st.metric("Non-factual rate among assessable responses", "2.1%")
        st.caption("47 non-factual responses out of 2,250 assessable responses, as labelled by Mistral. The 150 non-assessable responses are excluded from this rate.")
        st.subheader("Final RQ2 labels across all responses")
        st.bar_chart(
            {
                "Label": ["Factual", "Non-factual", "Non-assessable"],
                "Responses": [2203, 47, 150],
            },
            x="Label",
            y="Responses",
        )
        st.divider()
        st.subheader("Human-reviewed sample (300 responses)")
        st.metric("Human consensus: factual", "272")
        st.metric("Human consensus: non-factual", "4")
        st.metric("Human consensus: non-assessable", "24")
        st.bar_chart(
            {
                "Label": ["Factual", "Non-factual", "Non-assessable"],
                "Responses": [272, 4, 24],
            },
            x="Label",
            y="Responses",
        )
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
        st.metric("Matching labels in the 300-response sample", "293 / 300")

        st.metric("Observed agreement", "97.7%")
        ac1_col, kappa_col = st.columns(2)
        ac1_col.metric("Gwet's AC1: Mistral vs human consensus", "0.9744")
        kappa_col.metric("Cohen's kappa: Mistral vs human consensus", "0.8669")
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
