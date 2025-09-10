from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def voter_login():
    return render_template('voter/login.html')

@app.route('/voter/register')
def voter_register():
    return render_template('voter/register.html')

if __name__ == '__main__':
    app.run(debug=True)