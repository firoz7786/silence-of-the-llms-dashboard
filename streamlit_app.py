import streamlit as st

st.title("Silence of the LLMs")
st.write("Explore results for RQ1, RQ2, RQ3 and RQ4.")

rq1, rq2, rq3, rq4 = st.tabs(["RQ1", "RQ2", "RQ3", "RQ4"])

with rq2:
    st.subheader("RQ2 · Factual accuracy")
    st.write("How often do LLM answers contain factual errors?")
    st.metric("Responses assessed by Mistral", "2,400")
    st.metric("Mistral-labelled non-factual", "47")