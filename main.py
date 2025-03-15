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

import streamlit as st

# Create file uploader component
uploaded_file = st.file_uploader("Choose a file", 
                                 type=["csv", "txt", "xlsx", "pdf"],  # Specify allowed file types
                                 accept_multiple_files=False)  # Set to True if you want multiple files

# Check if a file was uploaded
if uploaded_file is not None:
    # Display file details
    file_details = {
        "Filename": uploaded_file.name,
        "File type": uploaded_file.type,
        "File size": f"{uploaded_file.size} bytes"
    }
    st.write("### File Details:")
    st.json(file_details)
    
    # Read and display file content based on type
    if uploaded_file.type == "text/plain":
        # For text files
        text_data = uploaded_file.read().decode("utf-8")
        st.text_area("File Content", text_data, height=300)
    elif uploaded_file.type == "text/csv":
        # For CSV files
        import pandas as pd
        df = pd.read_csv(uploaded_file)
        st.dataframe(df)
