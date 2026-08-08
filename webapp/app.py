import os, sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, 'youth_assessment.db')
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-secret-key')

ORG = 'Berekum Pentecost Child and Youth Development Centre (CYDC) – GH0954'
AREAS = {
    'Growth in Christ': [
        'The participant understands basic Christian teachings.',
        'The participant regularly reads or listens to the Bible.',
        'The participant participates in prayer.',
        'The participant demonstrates positive Christian values.',
        'The participant participates in church or Christian activities.'
    ],
    'Child Protection': [
        'The participant understands what child protection means.',
        'The participant can identify unsafe situations.',
        'The participant knows how to report abuse or unsafe situations.',
        'The participant understands basic rights and responsibilities.',
        'The participant demonstrates safe behaviour.'
    ],
    'Youth Life Skills': [
        'The participant can make responsible decisions.',
        'The participant demonstrates good communication skills.',
        'The participant can solve everyday problems.',
        'The participant demonstrates self-control.',
        'The participant can work positively with others.'
    ],
    'Youth Mentorship': [
        'The participant has identified personal goals.',
        'The participant follows guidance from a mentor.',
        'The participant takes responsibility for personal development.',
        'The participant demonstrates positive behaviour.',
        'The participant is making progress toward personal goals.'
    ],
    'Well-being': [
        'The participant understands the importance of personal hygiene.',
        'The participant demonstrates healthy habits.',
        'The participant understands the importance of good nutrition.',
        'The participant can identify ways of managing stress.',
        'The participant knows when and where to seek help.'
    ],
    'Vocational Training': [
        'The participant attends vocational training regularly.',
        'The participant understands the basic skills of the selected trade.',
        'The participant can demonstrate practical skills.',
        'The participant shows commitment to learning.',
        'The participant can apply learned skills to practical activities.'
    ],
    'Literacy & Numeracy': [
        'The participant can read and understand simple texts.',
        'The participant can write simple sentences.',
        'The participant can perform basic addition and subtraction.',
        'The participant can solve simple everyday mathematical problems.',
        'The participant demonstrates improvement in literacy and numeracy.'
    ]
}
PERIODS = ['Baseline', '1st Quarter', '2nd Quarter', '3rd Quarter', '4th Quarter']
SCORES = {0:'Not Demonstrated',1:'Needs Support',2:'Improved',3:'Enhanced',4:'Transformational Growth'}

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = db(); cur = c.cursor()
    cols = [r['name'] for r in cur.execute('PRAGMA table_info(assessments)')]
    if 'assessment_period' not in cols:
        cur.execute("ALTER TABLE assessments ADD COLUMN assessment_period TEXT DEFAULT 'Baseline'")
    if 'assessment_type' not in cols:
        cur.execute("ALTER TABLE assessments ADD COLUMN assessment_type TEXT DEFAULT 'Current'")
    c.commit(); c.close()

def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not session.get('user'): return redirect(url_for('login'))
        return f(*a, **kw)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if session.get('role') != 'admin': abort(403)
        return f(*a, **kw)
    return login_required(wrapper)

def interpretation(p):
    if p >= 85: return 'Transformational Growth'
    if p >= 70: return 'Enhanced'
    if p >= 50: return 'Improved'
    if p >= 35: return 'Maintained'
    return 'Needs Support'

def recommendation(level):
    return {
      'Transformational Growth':'Continue leadership opportunities, practical application and peer support.',
      'Enhanced':'Continue mentoring and provide opportunities for further development and practical application.',
      'Improved':'Continue regular support, mentoring and follow-up to strengthen progress.',
      'Maintained':'Provide additional encouragement, mentoring and targeted activities to promote further improvement.',
      'Needs Support':'Develop an individual support plan, provide closer mentoring and conduct a follow-up assessment.'
    }[level]

@app.context_processor
def globals_(): return {'ORG': ORG, 'areas': list(AREAS), 'periods': PERIODS}

@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username=request.form.get('username','').strip()
        password=request.form.get('password','')
        teacher_pass=os.environ.get('TEACHER_PASSWORD','teacher123')
        admin_pass=os.environ.get('ADMIN_PASSWORD','admin123')
        if username.lower() == 'teacher' and password == teacher_pass:
            session.update(user='Teacher', role='teacher'); return redirect(url_for('dashboard'))
        if username.lower() == 'admin' and password == admin_pass:
            session.update(user='Administrator', role='admin'); return redirect(url_for('dashboard'))
        flash('Incorrect username or password.')
    return render_template('login.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    c=db(); participants=c.execute('SELECT COUNT(*) n FROM participants').fetchone()['n']; assessments=c.execute('SELECT COUNT(*) n FROM assessments').fetchone()['n']; assessed=c.execute('SELECT COUNT(DISTINCT participant_id) n FROM assessments').fetchone()['n']; c.close()
    return render_template('dashboard.html', participants=participants, assessments=assessments, assessed=assessed)

@app.route('/participants')
@login_required
def participants():
    q=request.args.get('q','').strip(); c=db()
    rows=c.execute('''SELECT * FROM participants WHERE participant_name LIKE ? OR participant_id LIKE ? ORDER BY participant_name''',(f'%{q}%',f'%{q}%')).fetchall(); c.close()
    return render_template('participants.html', rows=rows, q=q)

@app.route('/participants/new', methods=['GET','POST'])
@admin_required
def participant_new():
    if request.method=='POST':
        data=[request.form.get(x,'').strip() for x in ['participant_id','participant_name','gender','school_level','school_name','caregiver_name','caregiver_phone']]
        if not data[0] or not data[1]: flash('Participant ID and name are required.'); return render_template('participant_form.html', row=None)
        try:
            c=db(); c.execute('INSERT INTO participants(participant_id,participant_name,gender,school_level,school_name,caregiver_name,caregiver_phone) VALUES(?,?,?,?,?,?,?)',data); c.commit(); c.close(); flash('Participant registered.'); return redirect(url_for('participants'))
        except sqlite3.IntegrityError: flash('That participant ID already exists.')
    return render_template('participant_form.html', row=None)

@app.route('/participants/<int:pid>/edit', methods=['GET','POST'])
@admin_required
def participant_edit(pid):
    c=db(); row=c.execute('SELECT * FROM participants WHERE id=?',(pid,)).fetchone(); c.close()
    if not row: abort(404)
    if request.method=='POST':
        data=[request.form.get(x,'').strip() for x in ['participant_id','participant_name','gender','school_level','school_name','caregiver_name','caregiver_phone']]
        try:
            c=db(); c.execute('''UPDATE participants SET participant_id=?,participant_name=?,gender=?,school_level=?,school_name=?,caregiver_name=?,caregiver_phone=? WHERE id=?''',(*data,pid)); c.commit(); c.close(); flash('Participant updated.'); return redirect(url_for('participants'))
        except sqlite3.IntegrityError: flash('That participant ID already exists.')
    return render_template('participant_form.html', row=row)

@app.post('/participants/<int:pid>/delete')
@admin_required
def participant_delete(pid):
    c=db(); row=c.execute('SELECT participant_id FROM participants WHERE id=?',(pid,)).fetchone()
    if row:
        c.execute('DELETE FROM assessment_answers WHERE assessment_id IN (SELECT id FROM assessments WHERE participant_id=?)',(row['participant_id'],)); c.execute('DELETE FROM assessments WHERE participant_id=?',(row['participant_id'],)); c.execute('DELETE FROM participants WHERE id=?',(pid,)); c.commit()
    c.close(); flash('Participant and linked assessment records deleted.'); return redirect(url_for('participants'))

@app.route('/assess/<participant_id>', methods=['GET','POST'])
@login_required
def assess(participant_id):
    c=db(); p=c.execute('SELECT * FROM participants WHERE participant_id=?',(participant_id,)).fetchone(); c.close()
    if not p: abort(404)
    selected_area=request.form.get('assessment_area','')
    selected_period=request.form.get('assessment_period','Baseline')
    if request.method=='POST' and 'save' in request.form:
        area=selected_area; period=selected_period
        if area not in AREAS: flash('Select an assessment area.'); return render_template('assess.html',p=p,area=area,period=period,questions=[])
        scores=[]
        for i in range(1,6):
            try: scores.append(int(request.form.get(f'q{i}','-1')))
            except: scores.append(-1)
        if -1 in scores: flash('Please score all five questions.'); return render_template('assess.html',p=p,area=area,period=period,questions=AREAS[area])
        total=sum(scores); maximum=20; pct=total/maximum*100; level=interpretation(pct); rec=request.form.get('recommendation','').strip() or recommendation(level); assessor=request.form.get('assessor_name','').strip() or session['user']; adate=request.form.get('assessment_date','').strip()
        if not adate: flash('Assessment date is required.'); return render_template('assess.html',p=p,area=area,period=period,questions=AREAS[area])
        c=db(); cur=c.cursor(); cur.execute('''INSERT INTO assessments(assessor_name,participant_name,participant_id,assessment_date,assessment_area,total_score,maximum_score,percentage,interpretation,recommendation,assessment_type,assessment_period) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',(assessor,p['participant_name'],p['participant_id'],adate,area,total,maximum,pct,level,rec,'Current',period)); aid=cur.lastrowid
        for i,(q,s) in enumerate(zip(AREAS[area],scores),1): cur.execute('INSERT INTO assessment_answers(assessment_id,question_number,question,score) VALUES(?,?,?,?)',(aid,i,q,s))
        c.commit(); c.close(); flash('Assessment saved successfully.'); return redirect(url_for('participant_view',pid=p['id']))
    return render_template('assess.html',p=p,area=selected_area,period=selected_period,questions=AREAS.get(selected_area,[]))

@app.route('/participant/<int:pid>')
@login_required
def participant_view(pid):
    c=db(); p=c.execute('SELECT * FROM participants WHERE id=?',(pid,)).fetchone(); hist=c.execute('SELECT * FROM assessments WHERE participant_id=? ORDER BY id DESC',(p['participant_id'],)).fetchall() if p else [] ; c.close()
    if not p: abort(404)
    return render_template('participant_view.html',p=p,hist=hist)

@app.route('/results')
@login_required
def results():
    q=request.args.get('q','').strip(); c=db(); rows=c.execute('''SELECT * FROM assessments WHERE participant_name LIKE ? OR participant_id LIKE ? OR assessment_area LIKE ? OR assessment_period LIKE ? ORDER BY id DESC''',(f'%{q}%',)*4).fetchall(); c.close(); return render_template('results.html',rows=rows,q=q)

@app.post('/results/<int:aid>/delete')
@admin_required
def assessment_delete(aid):
    c=db(); c.execute('DELETE FROM assessment_answers WHERE assessment_id=?',(aid,)); c.execute('DELETE FROM assessments WHERE id=?',(aid,)); c.commit(); c.close(); flash('Assessment deleted.'); return redirect(url_for('results'))

if __name__=='__main__':
    init_db(); app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)),debug=True)
else: init_db()
