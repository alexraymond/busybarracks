from enum import Enum
POS = 0
TIME_STEP = 1
HUMAN = 1

class MoveDirection(Enum):
    WAIT = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

class SpecialCellType(Enum):
    PLAYER_GOAL = 0

def in_visibility_range(range, pos, cell):
    x_pos, y_pos = pos
    x_cell, y_cell = cell
    return abs(x_pos - x_cell) <= range and abs(y_pos - y_cell) <= range

def straight_line_path(origin, destination):
    # Inclusive

    if origin[POS] == destination[POS]:
        return [origin]


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

def grow_path(path, difference):
    last_pos = path[-1][POS]
    last_time_step = path[-1][TIME_STEP]
    for i in range(1, difference + 1):
        path.append((last_pos, last_time_step + i))
    return path

def find_conflicts_between_paths(path_a, path_b, current_time_step, first_n_cells):
    first_time_step_a = path_a[0][TIME_STEP]

    last_time_step_a = path_a[-1][TIME_STEP]
    last_time_step_b = path_b[-1][TIME_STEP]

    if last_time_step_a < last_time_step_b:
        difference = last_time_step_b - last_time_step_a
        path_a = grow_path(path_a, difference)
    elif last_time_step_b < last_time_step_a:
        difference = last_time_step_a - last_time_step_b
        path_b = grow_path(path_b, difference)
    i = first_time_step_a
    for cell in path_a:
        i += 1
        if i > first_n_cells + current_time_step:
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