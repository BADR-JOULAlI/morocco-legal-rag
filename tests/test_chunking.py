import pytest

from morocco_legal_rag.chunking import chunk_page


def test_chunking_preserves_page_and_overlap() -> None:
    chunks = chunk_page(
        document_id="D1",
        title="Test",
        page=7,
        text="un deux trois quatre cinq six sept huit neuf dix",
        size=5,
        overlap=2,
    )
    assert len(chunks) == 4
    assert chunks[0].page == 7
    assert chunks[0].text.split()[-2:] == chunks[1].text.split()[:2]
    assert chunks[0].id.startswith("D1:p7:c0:")


def test_chunking_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError):
        chunk_page(document_id="D", title="T", page=1, text="abc", size=5, overlap=5)
