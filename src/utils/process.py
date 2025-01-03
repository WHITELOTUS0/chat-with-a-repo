# src/utils/process.py

import deeplake
import openai
import os
import subprocess
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import DeepLake
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.utils.load_and_split import load_docs, split_docs # Updated import


def clone_repository(repo_url, local_path):
    """Clone the specified git repository to the given local path."""
    subprocess.run(["git", "clone", repo_url, local_path], check=True, capture_output=True)


def create_deeplake_dataset(activeloop_dataset_path, activeloop_token):
    """Create an empty DeepLake dataset with the specified path and token."""
    ds = deeplake.empty(
        activeloop_dataset_path,
        token=activeloop_token,
        overwrite=True,
    )

    ds.create_tensor("ids")
    ds.create_tensor("metadata")
    ds.create_tensor("embedding")
    ds.create_tensor("text")


def process(
    repo_url, include_file_extensions, activeloop_dataset_path, repo_destination
):
    """
    Process a git repository by cloning it, filtering files, splitting documents,
    creating embeddings, and storing everything in a DeepLake dataset.
    """
    activeloop_token = os.getenv("ACTIVELOOP_TOKEN")

    create_deeplake_dataset(activeloop_dataset_path, activeloop_token)

    clone_repository(repo_url, repo_destination)

    docs = load_docs(repo_destination, include_file_extensions)
    texts = split_docs(docs)

    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

    db = DeepLake(dataset_path=activeloop_dataset_path, embedding_function=embeddings)
    db.add_documents(texts)