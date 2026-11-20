import sqlite3 as sql
from contextlib import closing
from functools import lru_cache

DATABASE = "database/canteen.db"


@lru_cache(maxsize=8)
def menu_get(category):
    """Return the menu items in a category ("%" means every category).

    README Step 6 changes this function.
    """
    with closing(sql.connect(DATABASE)) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM menu WHERE category LIKE ?;", [category])
        return tuple(
            dict(
                itemID=row[0],
                name=row[1],
                description=row[2],
                price=row[3],
                category=row[4],
                emoji=row[5],
            )
            for row in cur.fetchall()
        )


def order_add(name, item_ids, total):
    """Save a placed order in the database and return its order number."""
    with closing(sql.connect(DATABASE)) as con:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO orders (name, items, total) VALUES (?, ?, ?);",
            [name, ",".join(str(item_id) for item_id in item_ids), total],
        )
        con.commit()
        return cur.lastrowid
