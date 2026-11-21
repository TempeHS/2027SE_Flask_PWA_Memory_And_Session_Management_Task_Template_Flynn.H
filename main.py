"""School Canteen: a Flask PWA for ordering lunch from the school canteen.

This is the file you will change most. Each function's docstring tells you
which README steps change it. The Memory & Session Lab dashboard is attached
with two lines (the attach_lab import and the attach_lab(app) call). It lives
in the memory_lab folder, which you do not need to edit.
"""

from collections import deque
import re
import time

from flask import Flask
from flask import g
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import send_from_directory
from flask import url_for
from flask_wtf import CSRFProtect

from memory_lab import attach_lab
import database_manager as dbHandler
import session_store

app = Flask(__name__)
app.secret_key = b"6HlQfWhu03PttohW;apl"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
csrf = CSRFProtect(app)
attach_lab(app)

COOKIE_NAME = "session_id"
CATEGORIES = ["HOT FOOD", "SANDWICHES", "SNACKS", "DRINKS"]
NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z '-]{0,19}$")
MAX_ORDER_ITEMS = 20
CSP = (
    "default-src 'self'; img-src 'self'; object-src 'none'; "
    "base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
)

REQUEST_LOG = deque(maxlen=100)


@app.before_request
def log_request():
    """Record every request in REQUEST_LOG before Flask runs the route.

    README Step 7 limits how much this log can hold.
    """
    REQUEST_LOG.append((time.time(), request.method, request.path))


def current_session():
    """Return the session data for this request, creating a session if needed.

    Every route that needs to know who the user is calls this first. It looks
    for the session ID in the browser's cookie. If there is no session yet, it
    creates one and saves the new ID in g (Flask's notepad for the current
    request) so add_headers() can send it back to the browser as a cookie.
    README Step 12 adds the clean-up of expired sessions.
    """
    session_store.remove_expired_sessions()
    session_id = request.cookies.get(COOKIE_NAME)
    data = session_store.get_session(session_id)
    if data is None:
        session_id = session_store.create_session()
        data = session_store.get_session(session_id)
        g.new_session_id = session_id
    g.session_id = session_id
    return data


@app.after_request
def add_headers(response):
    """Add the session cookie and security headers to every response.

    Flask runs this after every route, just before the response is sent to the
    browser. README Steps 13 and 15 change how the session cookie is sent and
    deleted.
    """
    if "new_session_id" in g:
        response.set_cookie(
            COOKIE_NAME,
            g.new_session_id,
            max_age=session_store.ABSOLUTE_TIMEOUT,
            httponly=True,
            secure=True,
            samesite="Lax",
        )
    if g.get("end_session"):
        response.delete_cookie(COOKIE_NAME, httponly=True, secure=True, samesite="Lax")
    response.headers["Content-Security-Policy"] = CSP
    return response


def selected_category():
    """Return the menu category the user chose, or "%" for every category.

    "%" is the SQL wildcard: it matches any category in a LIKE query.
    """
    category = request.values.get("category", "").upper()
    return category if category in CATEGORIES else "%"


def back_to_menu():
    """Redirect to the menu page, keeping the category the user had chosen."""
    category = selected_category()
    if category == "%":
        return redirect(url_for("index"))
    return redirect(url_for("index", category=category))


def order_details(order):
    """Turn a list of item IDs into menu items and work out the total price.

    Prices are stored in cents (750 means $7.50) so they add up exactly.
    """
    menu = {item["itemID"]: item for item in dbHandler.menu_get("%")}
    items = [menu[item_id] for item_id in order if item_id in menu]
    return items, sum(item["price"] for item in items)


@app.route("/", methods=["GET"])
def index():
    """Show the canteen menu and the user's current order.

    README Steps 4 and 5 change where the menu comes from.
    """
    data = current_session()
    category = selected_category()
    menu = dbHandler.menu_get(category)
    items, total = order_details(data["order"])
    return render_template(
        "index.html",
        data=data,
        menu=menu,
        categories=CATEGORIES,
        category=category,
        items=items,
        total=total,
        placed=request.args.get("placed", type=int),
    )


@app.route("/add", methods=["POST"])
def add_item():
    """Add one menu item to the user's order."""
    data = current_session()
    item_id = request.form.get("itemID", type=int)
    menu_ids = [item["itemID"] for item in dbHandler.menu_get("%")]
    if item_id in menu_ids and len(data["order"]) < MAX_ORDER_ITEMS:
        data["order"].append(item_id)
    return back_to_menu()


@app.route("/remove", methods=["POST"])
def remove_item():
    """Remove one of an item from the user's order."""
    data = current_session()
    item_id = request.form.get("itemID", type=int)
    if item_id in data["order"]:
        data["order"].remove(item_id)
    return back_to_menu()


@app.route("/place-order", methods=["POST"])
def place_order():
    """Save the user's order in the database, then empty their order.

    Only signed-in users can place an order, so the canteen knows whose it is.
    """
    data = current_session()
    items, total = order_details(data["order"])
    if not data["name"] or not items:
        return back_to_menu()
    order_number = dbHandler.order_add(data["name"], data["order"], total)
    data["order"] = []
    return redirect(url_for("index", placed=order_number))


@app.route("/login", methods=["POST"])
def login():
    """Sign the user in with their first name (no password, to keep it simple).

    README Step 14 gives the user a new session ID when they sign in.
    """
    data = current_session()
    name = request.form.get("name", "").strip()
    if NAME_PATTERN.match(name):
        data["name"] = name
        g.new_session_id = session_store.regenerate_session(g.session_id)
    return redirect(url_for("index"))


@app.route("/logout", methods=["POST"])
def logout():
    """Sign the user out.

    README Step 15 makes this destroy the whole session.
    """
    session_store.destroy_session(request.cookies.get(COOKIE_NAME))
    g.end_session = True
    return redirect(url_for("index"))


@app.route("/my-order.json", methods=["GET"])
def my_order():
    """Return a short summary of the user's order as JSON.

    Every open tab asks for this every 2 seconds (see static/js/app.js), which
    keeps the order count the same in every tab.
    """
    data = current_session()
    items, total = order_details(data["order"])
    return jsonify(name=data["name"], count=len(items), total=total)


@app.route("/privacy.html", methods=["GET"])
def privacy():
    """Show the privacy policy, which lists the cookies and storage the app uses."""
    data = current_session()
    return render_template("privacy.html", data=data)


@app.route("/offline.html", methods=["GET"])
def offline():
    """Show the page the service worker displays when there is no internet."""
    return render_template("offline.html")


@app.route("/serviceWorker.js", methods=["GET"])
def service_worker():
    """Serve the service worker from the site root (/) so it can control every page.

    A service worker only controls pages in its own folder and below it.
    """
    return send_from_directory("static/js", "serviceWorker.js")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
