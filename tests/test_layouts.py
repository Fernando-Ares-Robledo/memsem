from memsem.models.layouts import Folded64Layout


def test_folded64_mapping_columns():
    expected_col0 = [48,49,50,51,52,53,54,55,63,62,61,60,59,58,57,56]
    expected_col1 = [32,33,34,35,36,37,38,39,47,46,45,44,43,42,41,40]
    expected_col2 = [16,17,18,19,20,21,22,23,31,30,29,28,27,26,25,24]
    expected_col3 = [0,1,2,3,4,5,6,7,15,14,13,12,11,10,9,8]
    columns = {0:[],1:[],2:[],3:[]}
    for i in range(64):
        r,c = Folded64Layout.position(i)
        columns[c].append((r,i))
    for c in columns:
        columns[c] = [i for _,i in sorted(columns[c])]
    assert columns[0] == expected_col0
    assert columns[1] == expected_col1
    assert columns[2] == expected_col2
    assert columns[3] == expected_col3
