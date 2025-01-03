# src/utils/chat.py
import os
import tempfile
import streamlit as st
from langchain_community.vectorstores import DeepLake
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
import openai
from streamlit_chat import message
from src.utils.process import process
from src.utils.load_and_split import load_docs, split_docs
import shutil
from langchain.cache import InMemoryCache
from langchain.globals import set_llm_cache
set_llm_cache(InMemoryCache())


def run_chat_app():
    """Run the chat application using the Streamlit framework."""
    st.title("Code Weaver")  # App title

    # Initialize session state variables if they don't exist
    if "generated" not in st.session_state:
        st.session_state["generated"] = ["I am ready to help you!"]
    if "past" not in st.session_state:
        st.session_state["past"] = ["Hello"]

    # Initialize data and status in the session
    if "data" not in st.session_state:
            st.session_state["data"] = {
                "repo_url": None,
                "include_file_extensions": None,
                "activeloop_dataset_path": None,
                "repo_destination": None,
                "status": "Please Provide Data"
            }
    # Sidebar for API keys and data
    with st.sidebar:
        st.header("Configuration")
        # Open AI key
        openai_api_key = st.text_input("OpenAI API Key", type="password")
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        #activeloop key
        activeloop_token = st.text_input("Activeloop Token", type="password")
        if activeloop_token:
            os.environ["ACTIVELOOP_TOKEN"] = activeloop_token
        # activeloop username
        activeloop_username = st.text_input("Activeloop Username")
        if activeloop_username:
            os.environ["ACTIVELOOP_USERNAME"] = activeloop_username


        st.session_state["data"]["repo_url"] = st.text_input("GitHub Repository URL")
        file_extensions_input = st.text_input("File Extensions (comma-separated, e.g., .py,.js)").strip()
        st.session_state["data"]["include_file_extensions"] = [ext.strip() for ext in file_extensions_input.split(",")] if file_extensions_input else None

        dataset_name = st.text_input("Dataset Name")
        if dataset_name:
              st.session_state["data"]["activeloop_dataset_path"] = f"hub://{os.environ.get('ACTIVELOOP_USERNAME')}/{dataset_name}"
        else:
           st.session_state["data"]["activeloop_dataset_path"] = None
        
        st.session_state["data"]["repo_destination"] = "repos"
        
        if st.button("Process Repository"):
            if st.session_state["data"]["repo_url"] and st.session_state["data"]["activeloop_dataset_path"] and os.environ.get("OPENAI_API_KEY") and os.environ.get("ACTIVELOOP_TOKEN") and os.environ.get("ACTIVELOOP_USERNAME") :
                st.session_state["data"]["status"] = "Processing Data"
                with st.spinner("Processing the repository, please wait"):
                    process_repo()
                st.session_state["data"]["status"] = "Ready to Chat!"
            else :
              st.session_state["data"]["status"] = "Missing Data"


    # Chat input and display area
    st.write(st.session_state["data"]["status"])
    if  st.session_state["data"]["status"] == "Ready to Chat!":
        user_input = get_text()
        if user_input:
            output = search_db(user_input)
            st.session_state.past.append(user_input)
            st.session_state.generated.append(output)
        if st.session_state["generated"]:
            for i in range(len(st.session_state["generated"])):
                message(st.session_state["past"][i], is_user=True, key=str(i) + "_user")
                message(st.session_state["generated"][i], key=str(i))
    # Footer
    st.markdown(
    """
    <br><hr style="border:2px solid gray">
    <p style="text-align:center; font-size: 12px;">
        Made with ❤️ by <a href="https://www.linkedin.com/in/glorry-sibomana/">Glorry Sibomana</a>
    </p>
    """,
    unsafe_allow_html=True,
)



def get_text():
    """Create a Streamlit input field and return the user's input."""
    input_text = st.text_input("Enter your query:", key="input", label_visibility="hidden")
    return input_text


def search_db(query):
    """Search for a response to the query in the DeepLake database."""
    # Set up embeddings and database
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    db = DeepLake(
       dataset_path=st.session_state["data"]["activeloop_dataset_path"],
       read_only=True,
       embedding_function=embeddings,
    )

    # Set up retriever with custom search parameters
    retriever = db.as_retriever()
    retriever.search_kwargs["distance_metric"] = "cos"
    retriever.search_kwargs["fetch_k"] = 100
    retriever.search_kwargs["k"] = 10

    # Initialize chat model
    model = ChatOpenAI(model="gpt-3.5-turbo")

    # Set up RetrievalQA chain
    qa = RetrievalQA.from_llm(model, retriever=retriever)
    return qa.run(query)




def process_repo():
  """Process the repository and save embeddings into Deep Lake dataset."""

  with tempfile.TemporaryDirectory() as temp_dir:
    repo_destination = os.path.join(temp_dir, "repo_clone")

    repo_url = st.session_state["data"]["repo_url"]
    include_file_extensions = st.session_state["data"]["include_file_extensions"]
    activeloop_dataset_path = st.session_state["data"]["activeloop_dataset_path"]

    process(
        repo_url,
        include_file_extensions,
        activeloop_dataset_path,
        repo_destination,
        )


if __name__ == "__main__":
    run_chat_app()