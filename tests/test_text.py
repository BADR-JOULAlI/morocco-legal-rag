from morocco_legal_rag.text import detect_script, normalize_text, tokenize


def test_normalize_text_removes_noise_without_translating() -> None:
    assert normalize_text("  مَــرْحَبًا   بالعالم  ") == "مرحبا بالعالم"


def test_detect_script() -> None:
    assert detect_script("مرحبا") == "arabic"
    assert detect_script("Bonjour") == "latin"
    assert detect_script("Bonjour مرحبا") == "mixed"


def test_tokenize_removes_common_stopwords() -> None:
    assert tokenize("Quel est le délai de traitement ?") == ["délai", "traitement"]
