"""Helper functions module"""

import pymupdf

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
