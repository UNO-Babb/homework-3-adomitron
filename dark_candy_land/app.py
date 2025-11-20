from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from random import choice
from uuid import uuid4

app = Flask(__name__)
app.secret_key = "change-this-in-production"

COLORS = ["red", "blue", "green", "yellow", "purple"]
SPECIALS = {
    "brush": "Brush Square",
    "licorice": "Licorice Snare",
    "lollipop": "Lollipop Woods",
    "gumdrop": "Sugar Surge Pass",
    "cavity": "Cavity Crawl",
    "castle": "Dark King Kandy’s Castle"
}

def generate_board(length=40):
    board = []
    special_indices = {1: "cavity",2: "licorice",3: "gumdrop", 4: "gumdrop",5: "gumdrop", 6: "brush", 7: "gumdrop", 8: "lollipop",
    9: "licorice", 10: "gumdrop", 11: "licorice", 12: "brush", 13: "lollipop", 14: "licorice", 15: "gumdrop", 16: "lollipop",
    17: "gumdrop", 18: "brush", 19: "gumdrop", 20: "cavity", 21: "lollipop", 22: "gumdrop", 23: "licorice", 24: "brush",
    25: "gumdrop", 26: "licorice", 27: "gumdrop", 28: "licorice", 29: "lollipop", 30: "gumdrop", 31: "brush",
    32: "cavity", 33: "gumdrop", 34: "lollipop", 35: "gumdrop",36: "brush", 37: "gumdrop", 38: "lollipop", 39: "castle"}
    for i in range(length):
        tile = {
            "index": i,
            "color": choice(COLORS),
            "special": special_indices.get(i)
        }
        board.append(tile)
    board[-1]["special"] = "castle"
    board[-1]["color"] = "purple"
    return board

def new_deck():
    deck = []
    for c in COLORS:
        deck += [{"type": "color", "color": c, "double": False} for _ in range(2)]
        deck += [{"type": "color", "color": c, "double": True} for _ in range(2)]
    deck += [{"type": "special", "name": "Rainbow Rot"} for _ in range(2)]
    deck += [{"type": "special", "name": "Candy Cane Shortcut"} for _ in range(2)]
    return deck

def create_game_state():
    board = generate_board()
    state = {
        "id": str(uuid4()),
        "board": board,
        "deck": new_deck(),
        "turn": 0,
        "players": [
            {"name": "Player 1", "pos": 0, "teeth": 32, "candy": 0, "skip": False},
            {"name": "Player 2", "pos": 0, "teeth": 32, "candy": 0, "skip": False},
        ],
        "log": []
    }
    return state

def draw_card(state):
    return choice(state["deck"])

def next_color_index(board, start_idx, color, steps=1):
    idx = start_idx
    found = 0
    while idx < len(board) - 1:
        idx += 1
        if board[idx]["color"] == color:
            found += 1
            if found == steps:
                return idx
    return start_idx

def apply_specials(state, player):
    tile = state["board"][player["pos"]]
    special = tile.get("special")

    if special == "gumdrop":
        player["pos"] = min(player["pos"] + 4, len(state["board"]) - 1)
        player["candy"] += 13
        player["teeth"] = max(player["teeth"] - 4, 0)
        state["log"].append("Sugar Surge Pass: +3 candy, -4 teeth.")

    elif special == "lollipop":
        player["pos"] = max(player["pos"] - 4, 0)
        player["teeth"] = max(player["teeth"] - 3, 0)
        player["candy"] += 15
        state["log"].append("Rot Return: back 4, -3 teeth.")

    elif special == "licorice":
        player["skip"] = True
        player["teeth"] = max(player["teeth"] - 2, 0)
        player["candy"] += 7
        state["log"].append("Gingivitis Monster: skip next draw, -2 teeth.")

    elif special == "cavity":
        player["pos"] = max(player["pos"] - 2, 0)
        player["teeth"] = max(player["teeth"] - 8, 0)
        player["candy"] += 37
        state["log"].append("Cavity Crawl: back 2, -8 teeth.")

    elif special == "brush":
        player["teeth"] = min(player["teeth"] + 20, 32)
        player["candy"] += -25
        state["log"].append("Brush Square: +20 tooth.")


def apply_special_card(state, player, card):
    if card["name"] == "Rainbow Rot":
        player["pos"] = min(player["pos"] + 3, len(state["board"]) - 1)
        player["candy"] += 14
        player["teeth"] = max(player["teeth"] - 4, 0)
        state["log"].append("Rainbow Rot: tooth decay (-4 teeth).")

    elif card["name"] == "Candy Cane Shortcut":
        player["pos"] = min(player["pos"] + 2, len(state["board"]) - 1)
        player["candy"] += 55
        player["teeth"] = max(player["teeth"] - 3, 0)
        state["log"].append("Candy Cane Shortcut: gums are bleeding (-3 teeth).")


def check_collapse(player):
    if player["teeth"] <= 0:
        player["skip"] = True
        return True
    return False

def check_win(state, player):
    at_castle = state["board"][player["pos"]].get("special") == "castle"
    return at_castle and player["teeth"] >= 1

@app.route("/", methods=["GET"])
def index():
    session["game"] = create_game_state()
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start():
    session["game"] = create_game_state()
    return redirect(url_for("game"))

@app.route("/game", methods=["GET"])
def game():
    state = session.get("game")
    if not state:
        state = create_game_state()
        session["game"] = state
    return render_template("game.html", state=state)

@app.route("/draw", methods=["POST"])
def draw():
    state = session.get("game")
    current = state["players"][state["turn"]]

    if current["skip"]:
        current["skip"] = False
        state["log"].append(f"{current['name']} was snared; turn skipped.")
        state["turn"] = 1 - state["turn"]
        session["game"] = state
        return jsonify({"state": state})

    card = draw_card(state)
    state["log"].append(f"{current['name']} drew: {card.get('name', card.get('color'))}{' (double)' if card.get('double') else ''}")

    if card["type"] == "color":
        # move a fixed number of spaces instead of jumping far
        spaces = 2 if card.get("double") else 1
        current["pos"] = min(current["pos"] + spaces, len(state["board"]) - 1)

    else:
        apply_special_card(state, current, card)

    apply_specials(state, current)

    collapsed = check_collapse(current)
    if collapsed:
        state["log"].append(f"{current['name']}'s smile collapses. Must find a Brush Square to revive.")

    if check_win(state, current):
        state["log"].append(f"{current['name']} reaches Dark King Dentist Office with teeth to spare. Victory!")
    else:
        state["turn"] = 1 - state["turn"]

    session["game"] = state
    return jsonify({"state": state})
        


if __name__ == "__main__":
    app.run(debug=True)
