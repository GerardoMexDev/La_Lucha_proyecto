import threading
import webbrowser
from app import create_app
from app.db import init_db

app = create_app()

with app.app_context():
    init_db()


def _abrir_navegador():
    webbrowser.open('http://127.0.0.1:5000')


if __name__ == '__main__':
    threading.Timer(1.5, _abrir_navegador).start()
    app.run(debug=True, host='127.0.0.1', port=5000)
