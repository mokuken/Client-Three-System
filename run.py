import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')

# Database config: use instance folder for sqlite file
os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.String(120), unique=True, nullable=False)
    fullname = db.Column(db.String(200), nullable=False)
    grade = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(200), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


def create_db_and_default_admin():
    """Create DB tables and a default admin account if missing."""
    with app.app_context():
        db.create_all()
        default_username = 'admin'
        default_password = 'admin'
        admin = Admin.query.filter_by(username=default_username).first()
        if not admin:
            admin = Admin(username=default_username, password_hash=generate_password_hash(default_password))
            db.session.add(admin)
            db.session.commit()
            print(f"Created default admin -> username: {default_username} password: {default_password}")


@app.route('/', methods=['GET', 'POST'])
def voter_login():
    if request.method == 'POST':
        school_id = request.form.get('school-id')
        password = request.form.get('password')
        if not school_id or not password:
            flash('Please provide school ID and password')
            return redirect(url_for('voter_login'))
        voter = Voter.query.filter_by(school_id=school_id).first()
        if not voter or not voter.check_password(password):
            flash('Invalid school ID or password')
            return redirect(url_for('voter_login'))
        flash('Voter logged in successfully')
        return redirect(url_for('voter_vote'))
    return render_template('voter/login.html')


@app.route('/voter/register', methods=['GET', 'POST'])
def voter_register():
    if request.method == 'POST':
        school_id = request.form.get('school-id')
        fullname = request.form.get('fullname')
        grade = request.form.get('grade')
        password = request.form.get('password')
        confirm = request.form.get('confirm-password')

        if not school_id or not fullname or not password or not confirm:
            flash('Please fill out all required fields')
            return redirect(url_for('voter_register'))
        if password != confirm:
            flash('Passwords do not match')
            return redirect(url_for('voter_register'))
        if Voter.query.filter_by(school_id=school_id).first():
            flash('School ID already registered')
            return redirect(url_for('voter_register'))

        voter = Voter(
            school_id=school_id,
            fullname=fullname,
            grade=grade,
            password_hash=generate_password_hash(password),
        )
        db.session.add(voter)
        db.session.commit()
        flash('Registration successful. You can now log in.')
        return redirect(url_for('voter_login'))
    return render_template('voter/register.html')


@app.route('/voter/vote')
def voter_vote():
    # Simple landing page after successful voter login
    return render_template('voter/vote.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('school-id')
        password = request.form.get('password')
        if not username or not password:
            flash('Please provide username and password')
            return redirect(url_for('admin_login'))
        admin = Admin.query.filter_by(username=username).first()
        if not admin or not admin.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('admin_login'))
        flash('Admin logged in successfully')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')


if __name__ == '__main__':
    create_db_and_default_admin()
    app.run(debug=True)