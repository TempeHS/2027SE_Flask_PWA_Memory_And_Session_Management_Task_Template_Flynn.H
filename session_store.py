"""A simple server-side session store.

Each visitor's browser holds a session ID in a cookie. The ID is the key to a
small dictionary of that visitor's data in SESSIONS. Everything in SESSIONS
lives in the server's memory until it is removed, and it is shared by the
whole server, so every byte stored here is multiplied by the number of users.
"""

import secrets
import time

IDLE_TIMEOUT = 120  # seconds without a request before a session expires
ABSOLUTE_TIMEOUT = 1800  # maximum life of any session in seconds

SESSIONS = {}


def create_session():
    """Create a session for a new visitor and return its session ID.

    README Steps 4, 5 and 11 change this function.
    """
    session_id = secrets.token_urlsafe(32)
    now = time.time()
    SESSIONS[session_id] = {
        "name": None,
        "order": [],
        "created": now,
        "last_seen": now,
    }
    return session_id


def is_expired(data, now):
    """Return True if a session has been idle, or alive, for too long.

    Added in README Step 12.
    """
    idle = now - data["last_seen"]
    age = now - data["created"]
    return idle > IDLE_TIMEOUT or age > ABSOLUTE_TIMEOUT


def get_session(session_id):
    """Return the data for a session ID, or None if there is no such session.

    It also records the time so the session's idle timer starts again.
    README Step 12 makes expired sessions return None too.
    """
    data = SESSIONS.get(session_id)
    if data is None:
        return None
    now = time.time()
    if is_expired(data, now):
        destroy_session(session_id)
        return None
    data["last_seen"] = now
    return data


def remove_expired_sessions():
    """Delete every expired session so its memory can be freed.

    Added in README Step 12.
    """
    now = time.time()
    for session_id, data in list(SESSIONS.items()):
        if is_expired(data, now):
            destroy_session(session_id)


def regenerate_session(session_id):
    """Move a session's data to a brand-new random ID and return the new ID.

    Used when a user signs in. Added in README Step 14.
    """
    new_session_id = secrets.token_urlsafe(32)
    SESSIONS[new_session_id] = SESSIONS.pop(session_id)
    return new_session_id


def destroy_session(session_id):
    """Delete a session and all of its data from server memory.

    Added in README Step 12 and used again in README Step 15.
    """
    SESSIONS.pop(session_id, None)
