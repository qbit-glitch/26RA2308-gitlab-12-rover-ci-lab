from src.planner import straight_path


def test_straight_path_forward():
    assert straight_path(1, 4) == [1, 2, 3, 4]


def test_straight_path_backward():
    assert straight_path(3, 1) == [3, 2, 1]
