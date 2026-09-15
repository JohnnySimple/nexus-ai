from src.helper_functions import chunk_sentences, create_page_chunks


def word_count(text: str) -> int:
    return len(text.split())


def sentence(label: str, words: int) -> str:
    return " ".join([label] * words)


def joined(sentences: list[str], indexes: range) -> str:
    return " ".join(sentences[i] for i in indexes)


def test_empty_input_produces_no_chunks():
    assert chunk_sentences([], max_tokens=10, overlap_tokens=5, count_tokens=word_count) == []


def test_chunks_stay_within_max_tokens_and_overlap_by_one_sentence():
    sentences = [sentence(f"s{i}", 10) for i in range(4)]

    chunks = chunk_sentences(sentences, max_tokens=25, overlap_tokens=10, count_tokens=word_count)

    assert chunks == [joined(sentences, range(0, 2)), joined(sentences, range(1, 3)), joined(sentences, range(2, 4))]
    assert all(word_count(chunk) <= 25 for chunk in chunks)


def test_overlap_is_bounded_by_tokens_not_sentence_count():
    # Regression: overlap used to be the last `overlap_tokens` sentences, which is usually the whole chunk.
    sentences = [sentence(f"s{i}", 5) for i in range(10)]

    chunks = chunk_sentences(sentences, max_tokens=20, overlap_tokens=5, count_tokens=word_count)

    assert chunks == [joined(sentences, range(0, 4)), joined(sentences, range(3, 7)), joined(sentences, range(6, 10))]


def test_zero_overlap_produces_disjoint_chunks():
    sentences = [sentence(f"s{i}", 5) for i in range(4)]

    chunks = chunk_sentences(sentences, max_tokens=10, overlap_tokens=0, count_tokens=word_count)

    assert chunks == [joined(sentences, range(0, 2)), joined(sentences, range(2, 4))]


def test_oversized_sentence_becomes_its_own_chunk():
    short_a, long_sentence, short_b = sentence("a", 3), sentence("long", 30), sentence("b", 3)

    chunks = chunk_sentences([short_a, long_sentence, short_b], max_tokens=10, overlap_tokens=5, count_tokens=word_count)

    assert chunks == [short_a, long_sentence, short_b]


def test_page_chunks_drop_fragments_and_keep_page_metadata():
    pages = [
        {"page_number": 3, "text": "Revenue grew twelve percent in fiscal 2025. 42"},
        {"page_number": 4, "text": ""},
    ]

    first, empty = create_page_chunks(pages, max_tokens=400, overlap_tokens=50, min_sentence_length=20)

    assert first["page_number"] == 3
    assert first["chunks"] == ["Revenue grew twelve percent in fiscal 2025."]
    assert empty["chunks"] == [] and empty["sentence_count"] == 0
