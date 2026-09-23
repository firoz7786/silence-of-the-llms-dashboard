import streamlit as st

st.title("Silence of the LLMs")
st.write("Explore results for RQ1, RQ2, RQ3 and RQ4.")

rq1, rq2, rq3, rq4 = st.tabs(["RQ1", "RQ2", "RQ3", "RQ4"])

with rq2:
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

    st.metric("Agreement with human consensus", "97.7%")
    st.metric("Cohen's kappa: Mistral vs human consensus", "0.867")
    st.caption(
        "Only 4 of the 300 human-reviewed responses were non-factual. "
        "Overall agreement does not, by itself, show how well Mistral detected that small group."
    )
    st.divider()
    st.subheader("RQ2 results by model")
    model_results = {
        "Model": ["GPT", "Gemini", "DeepSeek", "Kimi"],
        "Factual": [600, 599, 430, 574],
        "Non-factual": [0, 1, 33, 13],
        "Non-assessable": [0, 0, 137, 13],
    }

    st.bar_chart(
        model_results,
        x="Model",
        y=["Factual", "Non-factual", "Non-assessable"],
    )
    st.caption("Each model contributed 600 responses. These are final RQ2 classifications, including blank responses classified by rule.")
    selected_model = st.selectbox("Choose a model", model_results["Model"])
    i = model_results["Model"].index(selected_model)
    assessable = model_results["Factual"][i] + model_results["Non-factual"][i]
    non_factual_rate = model_results["Non-factual"][i] / assessable

    st.metric(
        f"{selected_model}: non-factual rate among assessable responses",
        f"{non_factual_rate:.1%}",
    )

    st.divider()
    st.subheader("RQ2 results by language")

    language_results = {
        "Language": ["English", "Mandarin"],
        "Factual": [1132, 1071],
        "Non-factual": [35, 12],
        "Non-assessable": [33, 117],
    }

    st.bar_chart(
        language_results,
        x="Language",
        y=["Factual", "Non-factual", "Non-assessable"],
    )
    st.caption("Each language contributed 1,200 responses. The chart shows final RQ2 classifications.")
    selected_language = st.selectbox("Choose a language", language_results["Language"])
    j = language_results["Language"].index(selected_language)
    language_assessable = language_results["Factual"][j] + language_results["Non-factual"][j]

    st.metric(
        f"{selected_language}: non-factual rate among assessable responses",
        f"{language_results['Non-factual'][j] / language_assessable:.1%}",
    )
    st.caption(
        "English: 35 of 1,167 assessable responses were non-factual (3.0%). "
        "Mandarin: 12 of 1,083 (1.1%). Non-assessable responses are excluded."
    )
    st.info(
        "These are overall rates. In the matched comparison of English and "
        "Mandarin answers to the same questions, the analysis did not find "
        "a clear difference in non-factual outcomes (exact McNemar p = 1.000)."
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
