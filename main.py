import os
from langchain_google_genai import ChatGoogleGenerativeAI

# Set the API key directly in the script
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = "AIzaSyAqMFvXnZ4JLeYqySr1rkY5Ooc5pYdPmrc"  

# Retrieve the API key
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY is not set")

# Initialize Gemini model
gemini_model = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key=api_key
)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain import LLMChain
from langchain import PromptTemplate

# Create prompt template for generating tweets
tweet_template = "Give me {number} tweets on {topic}"

tweet_prompt = PromptTemplate(template = tweet_template, input_variables = ['number', 'topic'])

# Create LLM chain using the prompt template and model
tweet_chain = tweet_prompt | gemini_model


import streamlit as st

st.header("🐦 Tweet Generator")

st.subheader("Generate tweets using Generative AI 🤖")

topic = st.text_input("Topic")

number = st.number_input("Number of tweets", min_value = 1, max_value = 10, value = 1, step = 1)

if st.button("Generate"):
    tweets = tweet_chain.invoke({"number" : number, "topic" : topic})
    st.write(tweets.content)
    
