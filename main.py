from flask import Flask, render_template
from flask_ngrok import run_with_ngrok

app = Flask(__name__)
run_with_ngrok(app)


@app.route('/')
def index():
    return render_template('base.html', title='market')


@app.route('/terms')
def terms():
    return render_template('terms.html', title='Terms and guarantees')


if __name__ == '__main__':
    app.run()
