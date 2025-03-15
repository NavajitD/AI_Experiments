from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import streamlit as st

st.header("🐦 Tweet Generator")
st.subheader("Generate tweets using Generative AI 🤖")

# Initialize model securely
gemini_model = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0.7,
    google_api_key=st.secrets["AIzaSyAqMFvXnZ4JLeYqySr1rkY5Ooc5pYdPmrc"]
)

# Create chat-optimized prompt
tweet_template = ChatPromptTemplate.from_messages([
    ("human", "Generate {number} engaging tweets about {topic}")
])

tweet_chain = tweet_template | gemini_model

# UI Components
topic = st.text_input("Topic")
number = st.number_input("Number of tweets", 1, 10)

if st.button("Generate"):
    response = tweet_chain.invoke({"number": number, "topic": topic})
    st.write("### Generated Tweets")
    st.write(response.content)
