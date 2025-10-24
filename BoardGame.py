#Example Flask App for a hexaganal tile game
#Logic is in this python file

from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Keep track of the current player
current_player = 1

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_tile')
def add_tile():
    global current_player
    color = 'green' if current_player == 1 else 'blue'  # Alternate between green and blue
    current_player = 2 if current_player == 1 else 1  # Switch to the other player
    return jsonify(color=color)

if __name__ == "__main__":
    app.run(debug=True)
