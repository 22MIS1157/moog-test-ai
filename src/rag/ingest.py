"""
MoogTestAI — Document Ingestion Pipeline

Reads design documents (datasheets, schematics, BOMs) from the pilot design
directory and stores them as vector embeddings in ChromaDB for semantic
retrieval by the AI agents.

Supported formats:
  - Markdown / Text (.md, .txt)
  - JSON (.json) — schematic data, parsed into readable text
  - CSV (.csv) — BOM files, parsed row-by-row
"""

import json
import os
from pathlib import Path

import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    PILOT_DESIGN_DIR,
    TEST_RESULTS_DIR,
    get_embeddings,
)


def _load_markdown_files(directory: str) -> list[Document]:
    """Load .md and .txt files as LangChain Documents."""
    docs = []
    for path in Path(directory).glob("*.md"):
        text = path.read_text(encoding="utf-8")
        docs.append(Document(page_content=text, metadata={"source": path.name, "type": "datasheet"}))
    for path in Path(directory).glob("*.txt"):
        text = path.read_text(encoding="utf-8")
        docs.append(Document(page_content=text, metadata={"source": path.name, "type": "datasheet"}))
    return docs


def _load_json_schematic(directory: str) -> list[Document]:
    """Parse JSON schematic files into readable text documents."""
    docs = []
    for path in Path(directory).glob("*.json"):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Convert the structured schematic into human-readable text
        lines = [f"Design: {data.get('design_name', 'Unknown')}"]
        lines.append(f"Revision: {data.get('revision', 'N/A')}")
        lines.append("")

        for block in data.get("blocks", []):
            lines.append(f"## Block: {block['name']} (ID: {block['id']}, Type: {block['type']})")
            lines.append(f"Components: {', '.join(block.get('components', []))}")
            lines.append(f"Critical Signals: {', '.join(block.get('critical_signals', []))}")

            if "input_voltage" in block:
                iv = block["input_voltage"]
                lines.append(f"Input Voltage Range: {iv['min']}-{iv['max']} {iv['unit']}")
            if "output_rails" in block:
                for rail in block["output_rails"]:
                    lines.append(f"Output Rail: {rail['voltage']}V, Max {rail['current_max']}A")
            if "max_current_continuous" in block:
                lines.append(f"Max Continuous Current: {block['max_current_continuous']}A")
                lines.append(f"Max Peak Current: {block.get('max_current_peak', 'N/A')}A")
            if "threshold_warning" in block:
                lines.append(f"Thermal Warning: {block['threshold_warning']}C")
                lines.append(f"Thermal Shutdown: {block['threshold_shutdown']}C")
            lines.append("")

        # Net connections
        lines.append("## Net Connections")
        for net in data.get("net_connections", []):
            lines.append(f"  {net['from']} --> {net['to']}")

        text = "\n".join(lines)
        docs.append(Document(page_content=text, metadata={"source": path.name, "type": "schematic"}))

    return docs


def _load_bom_csv(directory: str) -> list[Document]:
    """Parse BOM CSV files into readable text documents."""
    docs = []
    for path in Path(directory).glob("*.csv"):
        df = pd.read_csv(path)
        lines = [f"Bill of Materials: {path.name}", ""]

        # Summary statistics
        total_components = len(df)
        critical_count = len(df[df.get("Critical", pd.Series(dtype=str)) == "Yes"]) if "Critical" in df.columns else 0
        lines.append(f"Total Components: {total_components}")
        lines.append(f"Critical Components: {critical_count}")
        lines.append("")

        # Each component as a line
        for _, row in df.iterrows():
            parts = []
            for col in df.columns:
                parts.append(f"{col}: {row[col]}")
            lines.append(" | ".join(parts))

        text = "\n".join(lines)
        docs.append(Document(page_content=text, metadata={"source": path.name, "type": "bom"}))

    return docs


def _load_test_results(directory: str) -> list[Document]:
    """Load test result files (CSV and log) for the debug agent."""
    docs = []

    # CSV test results
    for path in Path(directory).glob("*.csv"):
        df = pd.read_csv(path)
        lines = [f"Test Results File: {path.name}", ""]
        for _, row in df.iterrows():
            parts = [f"{col}: {row[col]}" for col in df.columns]
            lines.append(" | ".join(parts))
        text = "\n".join(lines)
        docs.append(Document(page_content=text, metadata={"source": path.name, "type": "test_results"}))

    # Log test results
    for path in Path(directory).glob("*.log"):
        text = path.read_text(encoding="utf-8")
        docs.append(Document(page_content=text, metadata={"source": path.name, "type": "test_log"}))

    return docs


def ingest_documents() -> Chroma:
    """
    Main ingestion function. Reads all design documents and test results,
    splits them into chunks, and stores them in ChromaDB.

    Returns the Chroma vector store instance.
    """
    print("[*] Starting document ingestion pipeline...")

    # Collect all documents
    all_docs = []

    if os.path.exists(PILOT_DESIGN_DIR):
        all_docs.extend(_load_markdown_files(PILOT_DESIGN_DIR))
        all_docs.extend(_load_json_schematic(PILOT_DESIGN_DIR))
        all_docs.extend(_load_bom_csv(PILOT_DESIGN_DIR))
        print(f"[+] Loaded {len(all_docs)} design documents from {PILOT_DESIGN_DIR}")

    if os.path.exists(TEST_RESULTS_DIR):
        test_docs = _load_test_results(TEST_RESULTS_DIR)
        all_docs.extend(test_docs)
        print(f"[+] Loaded {len(test_docs)} test result files from {TEST_RESULTS_DIR}")

    if not all_docs:
        print("[!] No documents found. Check data directories.")
        return None

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(all_docs)
    print(f"[+] Split into {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

    # Create vector store
    embeddings = get_embeddings()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=CHROMA_COLLECTION_NAME,
        persist_directory=CHROMA_PERSIST_DIR,
    )
    print(f"[+] Stored {len(chunks)} chunks in ChromaDB at {CHROMA_PERSIST_DIR}")
    print("[*] Ingestion complete.")

    return vectorstore


if __name__ == "__main__":
    ingest_documents()
