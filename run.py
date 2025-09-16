import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

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


class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    positions = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Draft')


class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    photo_filename = db.Column(db.String(255), nullable=True)
    position = db.Column(db.String(120), nullable=False)
    party = db.Column(db.String(120), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=True)


class Position(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    max_winners = db.Column(db.Integer, nullable=False, default=1)
    # how many votes a voter may cast for this position (per voter)
    votes_allowed = db.Column(db.Integer, nullable=False, default=1)
    # election assignment removed; candidates now link to elections



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
        return redirect(url_for('voter_select'))
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
    # Render voting page for a specific election. Expects ?election_id=<id>
    election_id = request.args.get('election_id')
    if not election_id:
        flash('No election selected')
        return redirect(url_for('voter_select'))

    try:
        election_id_int = int(election_id)
    except (ValueError, TypeError):
        flash('Invalid election selected')
        return redirect(url_for('voter_select'))

    election = Election.query.get(election_id_int)
    if not election:
        flash('Election not found')
        return redirect(url_for('voter_select'))

    # load candidates for that election and group by position
    try:
        candidates = Candidate.query.filter_by(election_id=election_id_int).order_by(Candidate.full_name.asc()).all()
    except Exception:
        candidates = []

    positions = {}
    for c in candidates:
        positions.setdefault(c.position or 'Other', []).append(c)

    # positions_list: list of tuples (position_title, candidates_list)
    positions_list = list(positions.items())

    return render_template('voter/vote.html', election=election, positions=positions_list)


@app.route('/voter/submit_votes', methods=['POST'])
def voter_submit_votes():
    # Accepts JSON { election_id: int, selections: { position: candidate_id, ... } }
    data = request.get_json(silent=True) or {}
    election_id = data.get('election_id')
    selections = data.get('selections')

    if not election_id or not selections:
        return jsonify({'success': False, 'message': 'Missing election or selections'}), 400

    # Note: this endpoint currently does not persist votes to the database.
    # It validates payload shape and returns success. Persisting votes and
    # voter-authenticated submissions can be added in a follow-up change.
    return jsonify({'success': True, 'message': 'Votes submitted successfully'})


@app.route('/voter/select')
def voter_select():
    # list elections for voter to choose from
    try:
        elections = Election.query.order_by(Election.start_date.desc()).all()
    except Exception:
        elections = []
    return render_template('voter/select_election.html', elections=elections)


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

@app.route('/admin/voters')
def admin_voters():
    voters = Voter.query.order_by(Voter.fullname.asc()).all()
    return render_template('admin/voters.html', voters=voters)

@app.route('/admin/elections', methods=['GET', 'POST'])
def admin_elections():
    if request.method == 'POST':
        election_id = request.form.get('election_id')
        title = request.form.get('title')
        description = request.form.get('description')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        positions = request.form.get('positions')
        status = request.form.get('status') or 'Draft'

        # basic validation
        if not title or not start_date or not end_date:
            flash('Please provide title, start date and end date for the election')
            return redirect(url_for('admin_elections'))

        # parse dates
        from datetime import datetime
        try:
            sd = datetime.strptime(start_date, '%Y-%m-%d').date()
            ed = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format')
            return redirect(url_for('admin_elections'))

        if sd > ed:
            flash('End date must be the same or after start date')
            return redirect(url_for('admin_elections'))

        if election_id:
            # update existing
            election = Election.query.get(election_id)
            if not election:
                flash('Election not found')
                return redirect(url_for('admin_elections'))
            election.title = title
            election.description = description
            election.start_date = sd
            election.end_date = ed
            election.positions = positions
            election.status = status
        else:
            election = Election(
                title=title,
                description=description,
                start_date=sd,
                end_date=ed,
                positions=positions,
                status=status,
            )
            db.session.add(election)
        db.session.commit()
        flash('Election created successfully')
        return redirect(url_for('admin_elections'))

    # GET: list elections
    elections = Election.query.order_by(Election.start_date.desc()).all()
    return render_template('admin/elections.html', elections=elections)

@app.route('/admin/candidates')
def admin_candidates():
    # list candidates
    candidates = Candidate.query.order_by(Candidate.position.asc(), Candidate.full_name.asc()).all()
    positions = []
    try:
        positions = Position.query.order_by(Position.title.asc()).all()
    except Exception:
        positions = []
    elections = Election.query.order_by(Election.start_date.desc()).all()
    return render_template('admin/candidates.html', candidates=candidates, positions=positions, elections=elections)


@app.route('/admin/candidates', methods=['POST'])
def admin_create_or_update_candidate():
    # create or update candidate
    candidate_id = request.form.get('candidate_id')
    full_name = request.form.get('full_name')
    position = request.form.get('position')
    party = request.form.get('party')
    bio = request.form.get('bio')
    election_select = request.form.get('election_id')

    if not full_name or not position:
        flash('Please provide candidate name and position')
        return redirect(url_for('admin_candidates'))

    # handle file upload
    photo = request.files.get('photo')
    photo_filename = None
    if photo and photo.filename:
        uploads_dir = os.path.join(app.static_folder, 'uploads', 'candidates')
        os.makedirs(uploads_dir, exist_ok=True)
        # secure filename: keep simple, prepend timestamp
        from datetime import datetime
        ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        _, ext = os.path.splitext(photo.filename)
        photo_filename = f"{ts}_{secure_filename(photo.filename)}"
        photo.save(os.path.join(uploads_dir, photo_filename))

    if candidate_id:
        candidate = Candidate.query.get(candidate_id)
        if not candidate:
            flash('Candidate not found')
            return redirect(url_for('admin_candidates'))
        candidate.full_name = full_name
        candidate.position = position
        candidate.party = party
        candidate.bio = bio
        candidate.election_id = election_select or None
        if photo_filename:
            candidate.photo_filename = photo_filename
    else:
        candidate = Candidate(
            full_name=full_name,
            position=position,
            party=party,
            bio=bio,
            photo_filename=photo_filename,
            election_id=election_select or None,
        )
        db.session.add(candidate)
    db.session.commit()
    flash('Candidate saved')
    return redirect(url_for('admin_candidates'))


@app.route('/admin/candidates/delete', methods=['POST'])
def admin_delete_candidate():
    candidate_id = request.form.get('candidate_id')
    if not candidate_id:
        flash('No candidate specified')
        return redirect(url_for('admin_candidates'))
    candidate = Candidate.query.get(candidate_id)
    if not candidate:
        flash('Candidate not found')
        return redirect(url_for('admin_candidates'))
    # remove photo file if exists
    if candidate.photo_filename:
        try:
            path = os.path.join(app.static_folder, 'uploads', 'candidates', candidate.photo_filename)
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
    db.session.delete(candidate)
    db.session.commit()
    flash('Candidate deleted')
    return redirect(url_for('admin_candidates'))

@app.route('/admin/position', methods=['GET', 'POST'])
def admin_position():
    if request.method == 'POST':
        position_id = request.form.get('position_id')
        title = request.form.get('position_title')
        description = request.form.get('position_description')
        max_winners = request.form.get('max_winners')
        votes_allowed = request.form.get('votes_allowed')

        if not title:
            flash('Position title is required')
            return redirect(url_for('admin_position'))

        try:
            max_winners = int(max_winners or 1)
            if max_winners < 1:
                raise ValueError()
        except ValueError:
            flash('Maximum winners must be a positive integer')
            return redirect(url_for('admin_position'))

        try:
            votes_allowed = int(votes_allowed or 1)
            if votes_allowed < 1:
                raise ValueError()
        except ValueError:
            flash('Votes allowed must be a positive integer')
            return redirect(url_for('admin_position'))

        if position_id:
            pos = Position.query.get(position_id)
            if not pos:
                flash('Position not found')
                return redirect(url_for('admin_position'))
            pos.title = title
            pos.description = description
            pos.max_winners = max_winners
            pos.votes_allowed = votes_allowed
        else:
            pos = Position(title=title, description=description, max_winners=max_winners, votes_allowed=votes_allowed)
            db.session.add(pos)
        db.session.commit()
        flash('Position saved')
        return redirect(url_for('admin_position'))

    positions = Position.query.order_by(Position.id.asc()).all()
    elections = Election.query.order_by(Election.start_date.desc()).all()
    return render_template('admin/position.html', positions=positions, elections=elections)


@app.route('/admin/position/delete', methods=['POST'])
def admin_delete_position():
    position_id = request.form.get('position_id')
    if not position_id:
        flash('No position specified')
        return redirect(url_for('admin_position'))
    pos = Position.query.get(position_id)
    if not pos:
        flash('Position not found')
        return redirect(url_for('admin_position'))
    db.session.delete(pos)
    db.session.commit()
    flash('Position deleted')
    return redirect(url_for('admin_position'))


@app.route('/admin/elections/delete', methods=['POST'])
def admin_delete_election():
    election_id = request.form.get('election_id')
    if not election_id:
        flash('No election specified')
        return redirect(url_for('admin_elections'))
    election = Election.query.get(election_id)
    if not election:
        flash('Election not found')
        return redirect(url_for('admin_elections'))
    db.session.delete(election)
    db.session.commit()
    flash('Election deleted')
    return redirect(url_for('admin_elections'))


@app.route('/logout', methods=['POST'])
def logout():
    # clear any session data (if used) and redirect to admin login
    try:
        session.clear()
    except Exception:
        pass
    flash('You have been logged out')
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    create_db_and_default_admin()
    app.run(debug=True)