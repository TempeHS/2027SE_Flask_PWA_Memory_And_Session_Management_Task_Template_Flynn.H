"""A simple server-side session store.

Each visitor's browser holds a session ID in a cookie. The ID is the key to a
small dictionary of that visitor's data in SESSIONS. Everything in SESSIONS
lives in the server's memory until it is removed, and it is shared by the
whole server, so every byte stored here is multiplied by the number of users.
"""

import time

import database_manager as dbHandler

SESSIONS = {}
next_id = 1


def create_session():
    """Create a session for a new visitor and return its session ID.

    README Steps 4, 5 and 11 change this function.
    """
    global next_id
    session_id = str(next_id)
    next_id += 1
    SESSIONS[session_id] = {
        "name": None,
        "order": [],
        "created": time.time(),
        "last_seen": time.time(),
    }
    return session_id


def get_session(session_id):
    """Return the data for a session ID, or None if there is no such session.

    It also records the time so the session's idle timer starts again.
    README Step 12 makes expired sessions return None too.
    """
    data = SESSIONS.get(session_id)
    if data is not None:
        data["last_seen"] = time.time()
    return data
