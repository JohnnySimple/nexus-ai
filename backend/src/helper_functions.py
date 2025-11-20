"""Helper functions module"""

import pymupdf
from spacy.lang.en import English
from sentence_transformers import SentenceTransformer, util
import tiktoken
import logging

from src.config import settings

def get_file_type(file_name: str) -> str:
    """Get file type based on extension"""
    if file_name.endswith('.txt'):
        return 'txt'
    elif file_name.endswith('.pdf'):
        return 'pdf'
    elif file_name.endswith('.docx'):
        return 'docx'
    else:
        return False

def save_file_to_permanent_location(temp_file_path: str, document_id: str, file_name: str) -> str:
    """Save file from temporary location to permanent location"""
    try:
        import os
        from pathlib import Path

        if os.name == 'nt':  # Windows
            documents_dir = Path(os.environ.get("USERPROFILE"), '') / 'Documents' / settings.LOCAL_DOCUMENT_DIRECTORY_NAME
        else:
            documents_dir = Path.home() / 'Documents' / settings.LOCAL_DOCUMENT_DIRECTORY_NAME

        # create directory if not exists
        documents_dir.mkdir(parents=True, exist_ok=True)

        permanent_file_path = documents_dir / f"{document_id}_{file_name}"
        os.rename(temp_file_path, permanent_file_path)

        return str(permanent_file_path)
    except Exception as e:
        logging.warning(f"Failed to save file to permanent location: {e}")
        permanent_file_path = temp_file_path  # fallback to temp path
        os.remove(temp_file_path)  # Clean up the temporary file

def get_document_file_path(document_id: str) -> str:
    """Get the file path of a document based on its ID"""
    import os
    from pathlib import Path

    if os.name == 'nt':  # Windows
        documents_dir = Path(os.environ.get("USERPROFILE"), '') / 'Documents' / settings.LOCAL_DOCUMENT_DIRECTORY_NAME
    else:
        documents_dir = Path.home() / 'Documents' / settings.LOCAL_DOCUMENT_DIRECTORY_NAME

    # Search for the file with the given document_id
    for file in documents_dir.iterdir():
        if file.is_file() and file.name.startswith(document_id + "_"):
            return str(file)
    
    raise FileNotFoundError(f"Document with ID {document_id} not found.")

def get_file_content(file_path: str) -> str:
    """Extract text content from a file based on its type"""

    file_type = get_file_type(file_path)
    
    if not file_type:
        raise ValueError("Unsupported file type")
    
    if file_type == 'txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    elif file_type == 'pdf':
        return open_and_read_pdf(file_path)
    
    elif file_type == 'docx':
        pass

def text_formatter(text: str) -> str:
    """
    Formats the extracted text by removing excessive whitespace.

    Args:
        text (str): The raw text extracted from a PDF page.
    Returns:
        str: The formatted text.
    """
    # Replace multiple spaces with a single space
    formatted_text = text.replace("\n", " ").strip()
    return formatted_text

def split_list(input_list: list[str], slice_size: int=10) -> list[list[str]]:
        """
        Splits a list into smaller lists of a specified size.
        For example, a list of 17 sentences would be split into two lists of [[10], [7]].
        Args:
            input_list (list): The list to be split.
            slice_size (int): The size of each smaller list.
        Returns:
            list: A list of smaller lists.
        """
        return [input_list[i:i+slice_size] for i in range(0, len(input_list), slice_size)]

def open_and_read_pdf(file_path: str) -> str:
    """
    Opens a PDF file and extracts text from each page.

    Args:
        file_path (str): The path to the PDF file.
    Returns:
        list: A list of dictionaries, each representing the text from a page.
    """

    document = pymupdf.open(file_path)

    pages_and_text = []
    for page_number, page in enumerate(document):
        text = page.get_text()
        text = text_formatter(text)
        pages_and_text.append({
            "page_number": page_number,
            "text": text,
            # "page_char_count": len(text),
            # "page_word_count": len(text.split(" ")),
            # "page_sentence_count_raw": len(text.split(", ")),
            # "page_token_count": len(text) / 4,  # rough estimate
        })
        
    # pages_and_text = self.add_sentences_to_pages(pages_and_text)

    # return self.add_sentence_chunks_to_pages(pages_and_text, chunk_size=10)
    return pages_and_text

def create_content_page_chunks_reload(pages_and_text: list[dict], max_tokens: int = 400, overlap_tokens: int = 50, min_sentence_length: int = 20) -> list[dict]:
    """
    Splits the text of each page into sentences and adds them to the page dictionary.

    Args:
        pages_and_text (list): A list of dictionaries, each representing the text from a page.
    Returns:
        list: The updated list of dictionaries with sentences added.
    """
    nlp = English()
    nlp.add_pipe("sentencizer")
    tokenizer = tiktoken.get_encoding("cl100k_base")

    def num_tokens(text):
        return len(tokenizer.encode(text))
    
    for item in pages_and_text:
        doc = nlp(item["text"])
        sentences = [s.text.strip() for s in doc.sents if s.text.strip()]
        chunks, current_chunk, current_tokens = [], [], 0

        for sent in sentences:
            tokens = num_tokens(sent)
            if len(sent) < min_sentence_length and not sent.endswith(('.', '?', '!')):
                continue
            if current_tokens + tokens > max_tokens:
                chunks.append(" ".join(current_chunk).strip())
                # add overlap
                overlap = " ".join(current_chunk[-overlap_tokens:])
                current_chunk, current_tokens = [overlap, sent], num_tokens(overlap + sent)
            else:
                current_chunk.append(sent)
                current_tokens += tokens
        
        if current_chunk:
            chunks.append(" ".join(current_chunk).strip())
        
        item["chunks"] = chunks
        item["page_chunk_count"] = len(chunks)

    return pages_and_text

def create_content_page_chunks(pages_and_text: list[dict], max_chunk_size: int = 800, min_sentence_length: int = 20) -> list[dict]:
    """
    Splits the text of each page into sentences and adds them to the page dictionary.

    Args:
        pages_and_text (list): A list of dictionaries, each representing the text from a page.
    Returns:
        list: The updated list of dictionaries with sentences added.
    """
    nlp = English()
    nlp.add_pipe("sentencizer")

    for item in pages_and_text:
        # item["sentences"] = list(nlp(item["text"]).sents)
        # item["sentences"] = [str(sentence) for sentence in item["sentences"]]
        # item["page_sentence_count_spacy"] = len(item["sentences"])

        doc = nlp(item["text"])
        sentences = [str(sent).strip() for sent in doc.sents if sent.text.strip()]

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # skip overly short or meaningless fragments
            if len(sentence) < min_sentence_length and not sentence.endswith(('.', '!', '?')):
                continue

            # if adding this sentence keeps chunk size reasonable, merge it
            if len(current_chunk) + len(sentence) <= max_chunk_size:
                current_chunk += " " + sentence
            else:
                # finalize current chunk
                chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        item["chunks"] = chunks
        item["page_chunk_count"] = len(chunks)
    
    return pages_and_text

def create_semantic_chunks(pages_and_text: list[dict],
                           model_name: str = settings.SENTENCE_TRANSFORMER_MODEL,
                           max_chunk_size: int = 800,
                           similarity_threshold: float = 0.6,
                           min_sentence_length: int = 20) -> list[dict]:
    """
    Create semantically coherent chunks per page using sentence embeddings.
    """

    nlp = English()
    nlp.add_pipe("sentencizer")

    model = SentenceTransformer(model_name)

    for item in pages_and_text:
        # sentence tokenize
        doc = nlp(item["text"])
        sentences = [str(sent).strip() for sent in doc.sents if sent.text.strip()]
        sentences = [s for s in sentences if len(s) > min_sentence_length]

        if not sentences:
            item["chunks"] = []
            item["page_chunk_count"] = 0
            continue

        # compute embeddings
        embeddings = model.encode(sentences, convert_to_tensor=True, show_progress_bar=False)

        chunks = []
        current_chunk = sentences[0]
        current_chunk_length = len(current_chunk)

        for i in range(1, len(sentences)):
            similarity = util.cos_sim(embeddings[i-1], embeddings[i]).item()

            # merge if semantically similar and within chunk size
            if similarity >= similarity_threshold and (current_chunk_length + len(sentences[i])) <= max_chunk_size:
                current_chunk += " " + sentences[i]
                current_chunk_length += len(sentences[i])
            else:
                # commit current chunk
                chunks.append(current_chunk.strip())
                current_chunk = sentences[i]
                current_chunk_length = len(sentences[i])
        
        # add the final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        item["chunks"] = chunks
        item["page_chunk_count"] = len(chunks)

        return pages_and_text

def add_sentence_chunks_to_pages(pages_and_text: list[dict], chunk_size: int=10) -> list[dict]:
        """
        Splits the sentences of each page into chunks and adds them to the page dictionary.

        Args:
            pages_and_text (list): A list of dictionaries, each representing the text from a page.
            chunk_size (int): The number of sentences per chunk.
        Returns:
            list: The updated list of dictionaries with sentence chunks added.
        """

        for item in pages_and_text:
            item["sentence_chunks"] = split_list(input_list=item["sentences"], slice_size=chunk_size)
            item["number_of_chunks"] = len(item["sentence_chunks"])
        
        return pages_and_text

def get_rag_prompt_template() -> str:
    """Get the RAG prompt template"""
    return """You are an assistant for question-answering tasks. Use both the following pieces of conversation history and retrieved context to answer the question. If you don't know the answer, just say that you don't know. Ask for clarification if unsure. Use three sentences maximum and keep the answer concise.
Conversation history:
{history}
Question: {question} 
Context: {context} 
Answer:"""
