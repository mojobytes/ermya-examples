from documents import DOCUMENTS, Document, ALICE, BOB, owners


def test_has_eleven_documents():
    assert len(DOCUMENTS) == 11
    assert all(isinstance(d, Document) for d in DOCUMENTS)


def test_ownership_split_is_disjoint_5_and_6():
    alice_docs = [d for d in DOCUMENTS if d.owner == ALICE]
    bob_docs = [d for d in DOCUMENTS if d.owner == BOB]
    assert len(alice_docs) == 5
    assert len(bob_docs) == 6
    # every doc owned by exactly one of the two
    assert {d.owner for d in DOCUMENTS} == {ALICE, BOB}


def test_filenames_unique():
    names = [d.filename for d in DOCUMENTS]
    assert len(names) == len(set(names))


def test_owners_helper():
    assert owners() == {ALICE, BOB}
