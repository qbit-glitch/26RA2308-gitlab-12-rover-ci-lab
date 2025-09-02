"""Path planner for the Kestrel-1 rover."""


def straight_path(start, goal):
    """Return the cells from start to goal along one row, both included."""
    step = 1 if goal >= start else -1
    return list(range(start, goal + step, step))
