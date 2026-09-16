from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "<h1>Examination Seat Allocator</h1><p>Project setup is working.</p>"


if __name__ == "__main__":
    app.run(debug=True)