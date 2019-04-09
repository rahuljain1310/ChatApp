from flask import Flask,render_template,Response

app = Flask(__name__)
# app.config['DEBUG']=True

@app.route('/')
def sessions():
    return 'OK'

if __name__ == '__main__':    
   app.run()