from flask import Blueprint

main = Blueprint("main", __name__)


@main.get("/")
def home():
    return """
    <h1>Examination Seat Allocator</h1>
    <p>Project setup is working.</p>
    """