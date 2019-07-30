from enum import Enum
POS = 0
TIME_STEP = 1

class MoveDirection(Enum):
    WAIT = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

def in_visibility_range(range, pos, cell):
    x_pos, y_pos = pos
    x_cell, y_cell = cell
    return abs(x_pos - x_cell) <= range and abs(y_pos - y_cell) <= range

def straight_line_path(origin, destination):
    # Inclusive

    if origin[POS] == destination[POS]:
        return origin


    x1, y1 = origin[POS]
    x2, y2 = destination[POS]
    VERTICAL = x1 == x2
    HORIZONTAL = y1 == y2
    if VERTICAL is False and HORIZONTAL is False:
        return []
    path = []
    step_counter = origin[TIME_STEP]

    if VERTICAL:
        m = -1 if y1 > y2 else 1
        for i in range(y1, y2 + m, m):
            path.append(((x1, i), step_counter))
            step_counter += 1
    else:
        m = -1 if x1 > x2 else 1
        for i in range(x1, x2 + m, m):
            path.append(((i, y1), step_counter))
            step_counter += 1
    return path

def find_conflicts_between_paths(path_a, path_b, first_n_cells):
    i = 0
    for cell in path_a:
        i += 1
        if i > first_n_cells:
            return None
        if cell in path_b:
            return cell
    return None

def illegal_position_swap(path_a, path_b, first_n_cells):
    if len(path_a) < first_n_cells:
        first_n_cells = len(path_a)
    if len(path_b) < first_n_cells:
        first_n_cells = len(path_b)
    if first_n_cells < 2:
        return None
    for i in range(first_n_cells - 1):
        previous_position_a = (path_a[i][POS], path_a[i][TIME_STEP] + 1)
        previous_position_b = (path_b[i][POS], path_b[i][TIME_STEP] + 1)
        if path_b[i + 1] == previous_position_a and path_a[i + 1] == previous_position_b:
            return path_a[i][TIME_STEP]
    return None

def is_agent(cell_value):
    return cell_value > 0