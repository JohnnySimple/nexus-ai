"""Helper functions module"""

import pymupdf
from spacy.lang.en import English

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

def create_content_page_chunks(pages_and_text: list[dict]) -> list[dict]:
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
        item["sentences"] = list(nlp(item["text"]).sents)
        item["sentences"] = [str(sentence) for sentence in item["sentences"]]
        item["page_sentence_count_spacy"] = len(item["sentences"])
    
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
    return """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
Question: {question} 
Context: {context} 
Answer:"""
