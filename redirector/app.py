from flask import Flask, redirect, jsonify

import os

app = Flask(__name__)

REDIRECT = os.getenv('REDIRECT', None)

@app.route('/', defaults={'u_path': ''})
@app.route('/<path:u_path>')
def catch_all(u_path):
    try:
        if REDIRECT:
            host = REDIRECT
        else:
            raise Exception("config error - redirect not defined")
        # TODO: check valid URL
        return redirect("https://"+host+'/'+u_path, code=301)
    except Exception as e:
        content = {'error': str(e)}
        return jsonify(content), 501

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)