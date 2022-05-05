from website import create_app
import webbrowser
import os

app = create_app()

if __name__ == '__main__':

    host='localhost'
    port=8080

    if not os.environ.get("WERKZEUG_RUN_MAIN"):

        webbrowser.open('http://{}:{}/'.format(host, port))

    app.run(host=host, port=port, debug=True)
