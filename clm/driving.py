"""A deterministic, discrete toy driving environment for local rule testing.

This module models grid cells only; it makes no continuous-physics or real-road
claims.  All public data and returned states are JSON-serializable.
"""

from collections import deque


ACTIONS = {
    "left": "Shift one lane left, then move at the resulting speed.",
    "right": "Shift one lane right, then move at the resulting speed.",
    "accelerate": "Increase speed by one (maximum two), then move.",
    "brake": "Decrease speed by one (minimum zero), then move.",
    "hold": "Keep lane and speed, then move.",
}
ACTION_ORDER = ("left", "right", "accelerate", "brake", "hold")
FINISH = 20
TICK_BUDGET = 40


def _road(lanes_after_12=(0, 1, 2)):
    return [[0, 1, 2] if row <= 12 else list(lanes_after_12)
            for row in range(FINISH + 1)]


ROUTES = {
    "straight": {
        "road": _road(),
        "obstacles": [[1, 7]],
    },
    "slalom": {
        "road": _road(),
        "obstacles": [[1, 3], [0, 5], [2, 7], [1, 9]],
    },
    "narrowing": {
        "road": _road((1, 2)),
        "obstacles": [[1, 6], [2, 10]],
    },
}


def initial(route):
    """Return the fixed initial state after validating the named route."""
    _get_route(route)
    return {
        "lane": 1,
        "progress": 0,
        "speed": 1,
        "ticks": 0,
        "stalled": 0,
        "status": "active",
        "event": "initial",
    }


def observe(state, route):
    """Return complete geometry and the visible state, without mutating either."""
    spec = _get_route(route)
    return {
        "route": route,
        "road": [list(lanes) for lanes in spec["road"]],
        "obstacles": [list(cell) for cell in spec["obstacles"]],
        "lane": state["lane"],
        "progress": state["progress"],
        "speed": state["speed"],
        "ticks": state["ticks"],
        "stalled": state["stalled"],
        "status": state["status"],
        "event": state.get("event", ""),
    }


def step(state, action, route):
    """Apply one discrete control step and return a fresh next-state dictionary."""
    spec = _get_route(route)
    if action not in ACTIONS:
        raise ValueError("unknown action: %s" % action)
    _validate_state(state)
    if state["status"] != "active":
        rejected = dict(state)
        rejected["event"] = "terminal_rejected"
        return rejected

    lane = state["lane"]
    progress = state["progress"]
    speed = state["speed"]
    ticks = state["ticks"] + 1
    stalled = state["stalled"]

    # The lane-change origin is explicitly checked before any directional move.
    failure = _cell_failure(spec, lane, progress)
    if failure:
        return _terminal(lane, progress, speed, ticks, stalled, failure)

    if action == "left":
        lane -= 1
    elif action == "right":
        lane += 1
    elif action == "accelerate":
        speed = min(2, speed + 1)
    elif action == "brake":
        speed = max(0, speed - 1)

    # A lane change traverses its target cell at the current progress row.
    if action in ("left", "right"):
        failure = _cell_failure(spec, lane, progress)
        if failure:
            return _terminal(lane, progress, speed, ticks, stalled, failure)

    for row in range(progress + 1, min(FINISH, progress + speed) + 1):
        failure = _cell_failure(spec, lane, row)
        if failure:
            return _terminal(lane, row, speed, ticks, stalled, failure)

    progress = min(FINISH, progress + speed)
    if progress >= FINISH:
        return _terminal(lane, progress, speed, ticks, stalled, "finish", "finished")
    if ticks >= TICK_BUDGET:
        return _terminal(lane, progress, speed, ticks, stalled, "tick_budget", "budget_exhausted")
    if speed == 0:
        stalled += 1
        event = "stalled"
    else:
        event = "moved"
    return {
        "lane": lane, "progress": progress, "speed": speed, "ticks": ticks,
        "stalled": stalled, "status": "active", "event": event,
    }


def rule_action(state, route):
    """Return the first action of a shortest safe BFS path, or ``None`` if absent.

    The search consults only the explicit route and discrete state transition.
    It has no model-output input or inspection path.
    """
    _get_route(route)
    _validate_state(state)
    if state["status"] != "active":
        return None
    queue = deque([(dict(state), [])])
    seen = {_key(state)}
    while queue:
        current, path = queue.popleft()
        for action in ACTION_ORDER:
            nxt = step(current, action, route)
            candidate = path + [action]
            if nxt["status"] == "finished":
                return candidate[0]
            if nxt["status"] != "active":
                continue
            key = _key(nxt)
            if key not in seen:
                seen.add(key)
                queue.append((nxt, candidate))
    return None


def _get_route(route):
    if route not in ROUTES:
        raise ValueError("unknown route: %s" % route)
    return ROUTES[route]


def _validate_state(state):
    required = {"lane", "progress", "speed", "ticks", "stalled", "status"}
    if not required.issubset(state):
        raise ValueError("state is missing required fields")


def _cell_failure(spec, lane, row):
    if row < 0 or row > FINISH or lane not in spec["road"][row]:
        return "off_road"
    if [lane, row] in spec["obstacles"]:
        return "collision"
    return None


def _terminal(lane, progress, speed, ticks, stalled, event, status=None):
    if status is None:
        status = event
    return {
        "lane": lane, "progress": progress, "speed": speed, "ticks": ticks,
        "stalled": stalled, "status": status, "event": event,
    }


def _key(state):
    return (state["lane"], state["progress"], state["speed"],
            state["ticks"], state["stalled"], state["status"])
