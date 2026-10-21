
# Silence of the LLMs – AI Evaluation Dashboard

An interactive Data Science and AI research dashboard built using Python and Streamlit to explore large language model (LLM) behaviour across languages, models and prompt framings.

**[Launch Live Dashboard](https://silence-of-llms.streamlit.app/)**

## Project Overview

This dashboard is based on *Silence of the LLMs*, a collaborative Industry Development Project undertaken at La Trobe University.

The research dataset comprises 2,400 LLM responses generated from:
- 60 historical events
- 5 prompt framings
- 2 languages: English and Mandarin Chinese
- 4 large language models

The project examines differences in information restrictions, factual accuracy and response bias, with a focus on responsible AI and multilingual model evaluation.

## Dashboard Features

The Streamlit application provides interactive visualisations and analyses across four research questions:

- **RQ1 – Restriction and Evasion:** Explore refusal and evasion patterns across models, languages and prompt framings.
- **RQ2 – Factual Accuracy:** Examine factual, non-factual and non-assessable responses, including classification quality.
- **RQ3 – Prompt-Framing Bias:** Investigate how different prompt framings influence response bias and refusal.
- **RQ4 – Model and Language Bias:** Compare bias patterns across AI models, languages and event sets.

Features include interactive charts, comparative tables, statistical evidence and individual response exploration.

## Technologies Used

- **Python** – Data processing and application development
- **Streamlit** – Interactive dashboard framework
- **Pandas** – Data loading, manipulation and analysis
- **Altair** – Data visualisation
- **Git and GitHub** – Version control and project management

The dashboard uses processed research datasets and selected statistical results from the collaborative research project.

## Live Application

Explore the dashboard:

https://silence-of-llms.streamlit.app/

## Published Research

The research is associated with the following peer-reviewed journal publication:

**Mapping the Silence: Cross-Lingual Asymmetries in Large Language Model Refusal and Evasion on Sensitive History**

*Journal of East Asia Security*, 2026.

[Read the Published Article](https://easc.scholasticahq.com/article/172485-mapping-the-silence-cross-lingual-asymmetries-in-large-language-model-refusal-and-evasion-on-sensitive-history)

## Run Locally

This repository uses a Streamlit application entry point named `streamlit_app.py`.

Clone the repository:

```bash
git clone https://github.com/firoz7786/silence-of-the-llms-dashboard.git
cd silence-of-the-llms-dashboard
```

With Python 3.14 and `uv` available, launch the application with the required data-analysis packages:

```bash
uv run --with pandas --with altair streamlit run streamlit_app.py
```

The application requires its processed research CSV files for the corresponding analysis sections.

## Project Attribution

This repository presents a personal portfolio implementation of the dashboard associated with the La Trobe University collaborative Industry Development Project.

The underlying research, data preparation, evaluation and statistical analyses were collaborative team contributions. Individual project contributions should be attributed to their respective team members.

**Portfolio maintained by:** Firoz Noorbasha

**Academic institution:** La Trobe University

## Portfolio

- [GitHub Profile](https://github.com/firoz7786)
- [LinkedIn Profile](https://www.linkedin.com/in/firoz-noorbasha-04275b445)

This dashboard demonstrates practical applications of Python, data analysis, visualisation and AI research evaluation.
