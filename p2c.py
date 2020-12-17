from flask import Flask, redirect, request

app = Flask(__name__)

@app.route('/', defaults={'u_path': ''})
@app.route('/<path:u_path>')
def catch_all(u_path):
    try:
        host = request.headers.get('Host')
        return redirect("https://"+host+'/'+u_path, code=301)
    except:
        content = {'not': 'implemented'}
        return content, status.HTTP_501_NOT_IMPLEMENTED

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)