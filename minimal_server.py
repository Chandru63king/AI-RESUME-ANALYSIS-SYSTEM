
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return "Minimal Server Running"

if __name__ == '__main__':
    print("Starting minimal server...")
    app.run(port=5000)
