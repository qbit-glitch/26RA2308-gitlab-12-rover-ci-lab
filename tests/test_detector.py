from src.detector import detect_obstacle


def test_close_obstacle_is_detected():
    assert detect_obstacle(10) is True


def test_far_obstacle_is_ignored():
    assert detect_obstacle(100) is False
