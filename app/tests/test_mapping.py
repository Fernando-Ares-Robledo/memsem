from app.core.mapping import paper_word_index


def test_paper_word_index_mapping():
    assert paper_word_index(0, 0) == 0
    assert paper_word_index(1, 0) == 256
    assert paper_word_index(15, 255) == 4095
