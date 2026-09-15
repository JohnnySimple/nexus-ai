"""File handling, text extraction, chunking and prompt templates."""
import logging
import os
import shutil
from functools import lru_cache
from pathlib import Path
from typing import Callable

import pymupdf
import tiktoken
from spacy.lang.en import English

from src.config import settings

logger = logging.getLogger(__name__)


def get_file_type(file_name: str) -> str | None:
    """Return the file extension if it is a supported type, otherwise None"""
    extension = Path(file_name).suffix.lower().lstrip(".")
    return extension if extension in settings.SUPPORTED_FILE_TYPES else None

def _documents_dir() -> Path:
    """Directory where uploaded source files are kept"""
    home = Path(os.environ["USERPROFILE"]) if os.name == "nt" else Path.home()
    return home / "Documents" / settings.LOCAL_DOCUMENT_DIRECTORY_NAME

def save_file_to_permanent_location(temp_file_path: str, document_id: str, file_name: str) -> str:
    """Move an uploaded file from its temporary location to permanent storage"""
    documents_dir = _documents_dir()
    documents_dir.mkdir(parents=True, exist_ok=True)

    permanent_file_path = documents_dir / f"{document_id}_{Path(file_name).name}"
    shutil.move(temp_file_path, permanent_file_path)
    return str(permanent_file_path)

def get_document_file_path(document_id: str) -> str:
    """Get the stored file path of a document; raises FileNotFoundError if missing"""
    documents_dir = _documents_dir()
    if documents_dir.is_dir():
        for file in documents_dir.iterdir():
            if file.is_file() and file.name.startswith(document_id + "_"):
                return str(file)

    raise FileNotFoundError(f"Document with ID {document_id} not found.")

def delete_document_file(document_id: str) -> None:
    """Remove a document's stored file if present"""
    try:
        Path(get_document_file_path(document_id)).unlink()
    except FileNotFoundError:
        pass

def get_file_content(file_path: str) -> list[dict]:
    """Extract text from a file as a list of {"page_number", "text"} pages"""
    file_type = get_file_type(file_path)

    if file_type == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return [{"page_number": 1, "text": f.read()}]
    if file_type == "pdf":
        return open_and_read_pdf(file_path)

    raise ValueError(f"Unsupported file type: {file_path}")

def text_formatter(text: str) -> str:
    """Collapse line breaks in text extracted from a PDF page"""
    return text.replace("\n", " ").strip()

def open_and_read_pdf(file_path: str) -> list[dict]:
    """Extract the text of each page of a PDF"""
    with pymupdf.open(file_path) as document:
        return [
            {"page_number": page_number + 1, "text": text_formatter(page.get_text())}
            for page_number, page in enumerate(document)
        ]

@lru_cache(maxsize=1)
def _sentencizer() -> English:
    nlp = English()
    nlp.add_pipe("sentencizer")
    return nlp

@lru_cache(maxsize=1)
def _tokenizer() -> tiktoken.Encoding:
    return tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(_tokenizer().encode(text))

def chunk_sentences(sentences: list[str], max_tokens: int, overlap_tokens: int,
                    count_tokens: Callable[[str], int] = count_tokens) -> list[str]:
    """
    Greedily pack sentences into chunks of at most max_tokens.

    Each new chunk starts with the trailing sentences of the previous chunk whose combined
    size is at most overlap_tokens, so context carries across boundaries. A sentence longer
    than max_tokens becomes its own chunk rather than being split mid-sentence.
    """
    chunks: list[str] = []
    current: list[tuple[str, int]] = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)

        if current and current_tokens + sentence_tokens > max_tokens:
            chunks.append(" ".join(text for text, _ in current))

            overlap: list[tuple[str, int]] = []
            overlap_total = 0
            for text, tokens in reversed(current):
                if overlap_total + tokens > overlap_tokens:
                    break
                overlap.insert(0, (text, tokens))
                overlap_total += tokens

            # Drop the overlap if the next sentence would not fit alongside it.
            if overlap_total + sentence_tokens > max_tokens:
                overlap, overlap_total = [], 0
            current, current_tokens = overlap, overlap_total

        current.append((sentence, sentence_tokens))
        current_tokens += sentence_tokens

    if current:
        chunks.append(" ".join(text for text, _ in current))
    return chunks

def create_page_chunks(pages: list[dict], max_tokens: int, overlap_tokens: int, min_sentence_length: int) -> list[dict]:
    """Split each page into sentences and pack them into overlapping token-bounded chunks"""
    nlp = _sentencizer()
    chunked_pages = []

    for page in pages:
        sentences = [s.text.strip() for s in nlp(page["text"]).sents if s.text.strip()]
        # Skip short fragments such as headers and page numbers, but keep short complete sentences.
        kept = [s for s in sentences if len(s) >= min_sentence_length or s.endswith((".", "?", "!"))]

        chunked_pages.append({
            "page_number": page["page_number"],
            "text": page["text"],
            "sentence_count": len(sentences),
            "chunks": chunk_sentences(kept, max_tokens, overlap_tokens),
        })

    return chunked_pages

def get_prompt_rewrite_template() -> str:
    return """You are a query optimizer. Your goal is to rewrite the user's conversational question into a standalone, keyword-rich query suitable for a search engine to retrieve documents. Only output the new query.

Example:
Input: I had a problem with my laptop. What do I do?
Output: warranty claim process for model xyz, technical support contact information
Input: {question}
Output:
"""

def get_rag_prompt_template() -> str:
    """Get the RAG prompt template"""
    return """
<SYSTEM_INSTRUCTION>
You are a highly reliable and professional Corporate Knowledge Assistant. Your primary function is to synthesize information **strictly** from the provided <CONTEXT> section to answer the user's question.

**CORE DIRECTIVES:**
1.  **Strictly Grounded:** Your answer MUST be based *only* on the text provided in the <CONTEXT> section. Do not use external, general, or assumed knowledge.
2.  **Conciseness & Clarity:** Provide a clear, direct, and professionally toned answer in **no more than three (3) sentences**.
3.  **Attribution:** Do not explicitly state "According to the context...". Integrate facts seamlessly.
4.  **Unknowns/Hallucination Prevention:** If the complete answer cannot be verifiably found within the provided <CONTEXT>, you MUST respond with the following standardized phrase: "The required information is not available in the current knowledge base."
5.  **History Use:** Utilize the <HISTORY> for conversational coherence and context, but the factual grounding for the current response *always* comes from the <CONTEXT>.
</SYSTEM_INSTRUCTION>

<HISTORY>
{history}
</HISTORY>

<CONTEXT>
{context}
</CONTEXT>

<QUESTION>
{question}
</QUESTION>

Answer:
"""
