import json
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter


def read_doc_file(path):
    doc_list = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            # skip empty lines
            if line:
                doc_list.append(json.loads(line))
    return doc_list


def create_chunks(doc_list, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = []

    for doc in doc_list:
        for chunk in splitter.split_text(doc["content"]):
            chunk_id = str(uuid.uuid4())
            chunks.append(
                {
                    "id": chunk_id,
                    "content": chunk,
                    "metadata": {
                        "title": doc["title"],
                        "url": doc["url"],
                    },
                }
            )
    return chunks


def run_chunking_pipeline():
    path = "data/raw/policies.jsonl"
    policy_doc_list = read_doc_file(path=path)
    chunks = create_chunks(
        doc_list=policy_doc_list,
    )
    return chunks
