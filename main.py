from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "Mitchat09"
socketio = SocketIO(app)

rooms = {}


def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
            break

    return code


@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("home.html", error="Please Enter Name", code=code, name=name)

        if join != False and not code:
            return render_template(home.html, error="Please Enter A Room Code", code=code, name=name)

        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, 'messages': []}

        elif code not in rooms:
            return render_template("home.html", error="Room doesn't exist", code=code, name=name)

        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")


@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])


@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return
    
    name = session.get("name")
    message_content = data["data"]
    content = {
        "name": name,
        "message": message_content
    }
    send(content, to=room)
    
    # Check if the user has sent previous messages
    if room in rooms and name in rooms[room]["members"]:
        # Same user sent another message, update only the message content
        rooms[room]["messages"].append({"name": name, "message": message_content})
    else:
        # Different user or first message from the same user
        rooms[room]["members"].add(name)
        rooms[room]["messages"].append(content)
    
    print(f"{name} said: {message_content}")


@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return

    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")


@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} left room {room}")


if __name__ == "__main__":
    extra_files = ['templates/home.html', 'templates/room.html', 'templates/base.html']
    socketio.run(app, debug=True, port=5001, extra_files=extra_files, allow_unsafe_werkzeug=True, host='0.0.0.0')
