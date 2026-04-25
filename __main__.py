from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///football_club.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100))
    stadium = db.Column(db.String(100))
    founded = db.Column(db.Integer)
    players = db.relationship('Player', backref='club', lazy=True)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id', ondelete='SET NULL'))
    position = db.Column(db.String(20))
    number = db.Column(db.Integer)
    age = db.Column(db.Integer)
    nationality = db.Column(db.String(50))
    rating = db.Column(db.Float, default=6.0)
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    home_club_id = db.Column(db.Integer, db.ForeignKey('club.id', ondelete='CASCADE'))
    away_club_id = db.Column(db.Integer, db.ForeignKey('club.id', ondelete='CASCADE'))
    match_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='scheduled')
    home_score = db.Column(db.Integer, default=0)
    away_score = db.Column(db.Integer, default=0)
    home_club = db.relationship('Club', foreign_keys=[home_club_id])
    away_club = db.relationship('Club', foreign_keys=[away_club_id])

class MatchEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id', ondelete='CASCADE'))
    event_type = db.Column(db.String(20))
    player_id = db.Column(db.Integer, db.ForeignKey('player.id', ondelete='SET NULL'))
    minute = db.Column(db.Integer)
    additional_info = db.Column(db.String(200))
    match = db.relationship('Match', backref='events')
    player = db.relationship('Player', backref='events')

class Transfer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id', ondelete='CASCADE'))
    from_club_id = db.Column(db.Integer, db.ForeignKey('club.id', ondelete='SET NULL'))
    to_club_id = db.Column(db.Integer, db.ForeignKey('club.id', ondelete='SET NULL'))
    transfer_date = db.Column(db.DateTime)
    fee = db.Column(db.Integer)
    player = db.relationship('Player', backref='transfers')
    from_club = db.relationship('Club', foreign_keys=[from_club_id])
    to_club = db.relationship('Club', foreign_keys=[to_club_id])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_admin():
    admin_password = generate_password_hash('KULOKI22867')
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', password_hash=admin_password, is_admin=True)
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IFTTScore - Футбольная организация</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:#0a0e1a;color:#fff;}
.header{background:linear-gradient(135deg,#1a1f2e 0%,#0d1117 100%);padding:16px 24px;position:sticky;top:0;z-index:100;border-bottom:1px solid #2a2f3e;}
.header-content{max-width:1400px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;}
.logo{font-size:28px;font-weight:800;background:linear-gradient(135deg,#00b4d8,#0077b6);-webkit-background-clip:text;background-clip:text;color:transparent;}
.nav{display:flex;gap:32px;}
.nav a{color:#8b92a8;text-decoration:none;font-weight:500;transition:color 0.3s;}
.nav a:hover,.nav a.active{color:#00b4d8;}
.admin-btn{background:linear-gradient(135deg,#00b4d8,#0077b6);padding:8px 20px;border-radius:25px;color:white !important;}
.container{max-width:1400px;margin:0 auto;padding:24px;}
.card{background:#131724;border-radius:16px;padding:20px;margin-bottom:24px;border:1px solid #1e2433;}
.section-title{font-size:20px;font-weight:700;margin-bottom:20px;display:flex;align-items:center;gap:10px;}
.section-title::before{content:'';width:4px;height:24px;background:linear-gradient(135deg,#00b4d8,#0077b6);border-radius:2px;}
.table-container{overflow-x:auto;}
.standings-table{width:100%;border-collapse:collapse;}
.standings-table th,.standings-table td{padding:12px 8px;text-align:center;border-bottom:1px solid #1e2433;}
.standings-table th{color:#8b92a8;font-weight:500;font-size:13px;}
.matches-grid{display:grid;gap:16px;}
.match-card{background:#0d1117;border-radius:12px;padding:16px;display:flex;justify-content:space-between;align-items:center;}
.match-teams{display:flex;align-items:center;gap:20px;flex:1;}
.team{display:flex;align-items:center;gap:12px;}
.score{font-size:24px;font-weight:800;margin:0 20px;}
.match-date{color:#8b92a8;font-size:13px;}
.match-status{padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;}
.status-finished{background:#1a3a2a;color:#00c853;}
.status-scheduled{background:#2a2f3e;color:#8b92a8;}
.top-scorers{display:grid;gap:12px;}
.scorer-item{display:flex;align-items:center;gap:15px;padding:12px;background:#0d1117;border-radius:12px;}
.scorer-rank{font-size:20px;font-weight:800;color:#00b4d8;width:40px;}
.scorer-info{flex:1;}
.scorer-name{font-weight:600;}
.scorer-club{font-size:12px;color:#8b92a8;}
.scorer-stats{text-align:right;}
.scorer-goals{font-size:20px;font-weight:800;color:#00c853;}
.transfers-list{display:grid;gap:12px;}
.transfer-item{display:flex;align-items:center;justify-content:space-between;padding:12px;background:#0d1117;border-radius:12px;}
.admin-fab{position:fixed;bottom:24px;right:24px;background:linear-gradient(135deg,#00b4d8,#0077b6);width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;text-decoration:none;box-shadow:0 4px 12px rgba(0,180,216,0.3);font-size:24px;}
.admin-fab:hover{transform:scale(1.1);}
.two-columns{display:grid;grid-template-columns:1fr 1fr;gap:24px;}
@media(max-width:768px){.container{padding:16px;}.match-teams{flex-direction:column;align-items:flex-start;gap:10px;}.score{margin:10px 0;}.nav{display:none;}.two-columns{grid-template-columns:1fr;}}
</style>
</head>
<body>
<header class="header"><div class="header-content"><div class="logo">⚽ IFTTScore</div><nav class="nav"><a href="#" class="active">Главная</a><a href="#matches">Матчи</a><a href="#table">Таблица</a><a href="#scorers">Бомбардиры</a><a href="#transfers">Трансферы</a></nav><a href="/login" class="admin-btn">👑 Администраторам</a></div></header>
<main class="container">
<div class="card" id="matches"><div class="section-title"><span>⚡ МАТЧИ</span></div><div class="matches-grid" id="matches-list"><div style="text-align:center;padding:40px;">Загрузка...</div></div></div>
<div class="card" id="table"><div class="section-title"><span>🏆 ТУРНИРНАЯ ТАБЛИЦА</span></div><div class="table-container"><table class="standings-table"><thead><tr><th>#</th><th>Клуб</th><th>И</th><th>В</th><th>Н</th><th>П</th><th>ГЗ</th><th>ГП</th><th>Р</th><th>О</th></tr></thead><tbody id="standings-body"><tr><td colspan="10" style="text-align:center;">Загрузка...</td></table></tbody></table></div></div>
<div class="two-columns">
<div class="card" id="scorers"><div class="section-title"><span>⚽ ЛУЧШИЕ БОМБАРДИРЫ</span></div><div class="top-scorers" id="scorers-list"><div style="text-align:center;padding:20px;">Загрузка...</div></div></div>
<div class="card" id="transfers"><div class="section-title"><span>🔄 ПОСЛЕДНИЕ ТРАНСФЕРЫ</span></div><div class="transfers-list" id="transfers-list"><div style="text-align:center;padding:20px;">Загрузка...</div></div></div>
</div>
</main>
<a href="/admin" class="admin-fab">👑</a>
<script>
function loadMatches(){fetch('/api/matches').then(r=>r.json()).then(d=>{document.getElementById('matches-list').innerHTML=d.map(m=>`<div class="match-card"><div class="match-teams"><div class="team"><strong>${m.home}</strong></div><div class="score">${m.home_score}:${m.away_score}</div><div class="team"><strong>${m.away}</strong></div></div><div><div class="match-date">${m.date}</div><span class="match-status status-${m.status}">${m.status==='finished'?'Завершён':'Запланирован'}</span></div></div>`).join('')});}
function loadTable(){fetch('/api/table').then(r=>r.json()).then(d=>{document.getElementById('standings-body').innerHTML=d.map((c,i)=>`<tr><td><strong>${i+1}</strong></td><td style="text-align:left;"><strong>${c.name}</strong></td><td>${c.played}</td><td>${c.wins}</td><td>${c.draws}</td><td>${c.losses}</td><td>${c.goals_for}</td><td>${c.goals_against}</td><td>${c.gd}</td><td><strong style="color:#00b4d8;">${c.points}</strong></td></tr>`).join('')});}
function loadScorers(){fetch('/api/top_scorers').then(r=>r.json()).then(d=>{document.getElementById('scorers-list').innerHTML=d.map((p,i)=>`<div class="scorer-item"><div class="scorer-rank">${i+1}</div><div class="scorer-info"><div class="scorer-name">${p.name}</div><div class="scorer-club">${p.club}</div></div><div class="scorer-stats"><div class="scorer-goals">⚽ ${p.goals}</div><div style="font-size:12px;">🎯 ${p.assists}</div></div></div>`).join('')});}
function loadTransfers(){fetch('/api/transfers').then(r=>r.json()).then(d=>{document.getElementById('transfers-list').innerHTML=d.map(t=>`<div class="transfer-item"><div><strong>${t.player}</strong><div style="font-size:12px;color:#8b92a8;">${t.from} → ${t.to}</div></div><div style="text-align:right;"><div style="color:#00c853;">${t.fee}</div><div style="font-size:11px;color:#8b92a8;">${t.date}</div></div></div>`).join('')});}
loadMatches();loadTable();loadScorers();loadTransfers();
setInterval(()=>{loadMatches();loadTable();},30000);
</script>
</body>
</html>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('admin_panel'))
        else:
            flash('Неверный логин или пароль')
    return '''
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Вход - IFTTScore Admin</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:linear-gradient(135deg,#0a0e1a 0%,#1a1f2e 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;}
.login-container{background:#131724;border-radius:24px;padding:40px;width:100%;max-width:420px;box-shadow:0 20px 40px rgba(0,0,0,0.4);border:1px solid #2a2f3e;}
.logo{font-size:36px;text-align:center;margin-bottom:30px;background:linear-gradient(135deg,#00b4d8,#0077b6);-webkit-background-clip:text;background-clip:text;color:transparent;font-weight:800;}
.form-group{margin-bottom:20px;}
label{display:block;color:#8b92a8;margin-bottom:8px;font-size:14px;}
input{width:100%;padding:12px 16px;background:#0d1117;border:1px solid #2a2f3e;border-radius:12px;color:white;font-size:16px;}
input:focus{outline:none;border-color:#00b4d8;}
button{width:100%;padding:12px;background:linear-gradient(135deg,#00b4d8,#0077b6);border:none;border-radius:12px;color:white;font-size:16px;font-weight:600;cursor:pointer;}
button:hover{transform:translateY(-2px);}
.error{background:rgba(255,59,48,0.1);border:1px solid #ff3b30;color:#ff3b30;padding:12px;border-radius:12px;margin-bottom:20px;font-size:14px;}
.demo{background:#1a2a3a;padding:15px;border-radius:12px;margin-top:20px;font-size:12px;text-align:center;}
.info{text-align:center;margin-top:20px;color:#8b92a8;font-size:13px;}
</style>
</head>
<body>
<div class="login-container">
<div class="logo">⚽ IFTTScore ADMIN</div>
''' + (f'<div class="error">{flash}</div>' if flash else '') + '''
<form method="POST">
<div class="form-group"><label>👤 Логин</label><input type="text" name="username" placeholder="admin" required></div>
<div class="form-group"><label>🔐 Пароль</label><input type="password" name="password" placeholder="••••••••" required></div>
<button type="submit">Войти в панель управления</button>
</form>
<div class="demo">🔐 Пароль администратора: <strong>KULOKI22867</strong><br>Логин: <strong>admin</strong></div>
<div class="info">Только для авторизованных администраторов</div>
</div>
</body>
</html>
    '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    clubs = Club.query.all()
    players = Player.query.all()
    matches = Match.query.order_by(Match.match_date.desc()).all()
    transfers = Transfer.query.all()
    return f'''
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Админ-панель - IFTTScore</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:#0a0e1a;color:#fff;}}
.admin-header{{background:linear-gradient(135deg,#1a1f2e 0%,#0d1117 100%);padding:16px 24px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #2a2f3e;}}
.logo{{font-size:24px;font-weight:800;background:linear-gradient(135deg,#00b4d8,#0077b6);-webkit-background-clip:text;background-clip:text;color:transparent;}}
.container{{max-width:1400px;margin:0 auto;padding:24px;}}
.card{{background:#131724;border-radius:16px;padding:20px;margin-bottom:24px;border:1px solid #1e2433;}}
.section-title{{font-size:20px;font-weight:700;margin-bottom:20px;display:flex;align-items:center;gap:10px;}}
.section-title::before{{content:'';width:4px;height:24px;background:linear-gradient(135deg,#00b4d8,#0077b6);border-radius:2px;}}
.form-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:15px;margin-bottom:20px;}}
.form-group input,.form-group select{{width:100%;padding:10px;background:#0d1117;border:1px solid #2a2f3e;border-radius:8px;color:white;}}
.form-group label{{display:block;margin-bottom:5px;color:#8b92a8;font-size:13px;}}
.btn{{background:linear-gradient(135deg,#00b4d8,#0077b6);padding:10px 20px;border:none;border-radius:8px;color:white;cursor:pointer;font-weight:600;}}
.btn-danger{{background:linear-gradient(135deg,#ff3b30,#c0392b);}}
table{{width:100%;border-collapse:collapse;}}
th,td{{padding:10px;text-align:left;border-bottom:1px solid #1e2433;}}
th{{color:#8b92a8;}}
.delete-btn{{background:#ff3b30;color:white;border:none;padding:5px 10px;border-radius:5px;cursor:pointer;font-size:12px;}}
.delete-btn:hover{{background:#cc0000;}}
</style>
</head>
<body>
<div class="admin-header"><div class="logo">⚽ IFTTScore Админ-панель</div><a href="/logout" style="color:#ff3b30;text-decoration:none;">Выйти</a></div>
<div class="container">

<div class="card"><div class="section-title"><span>➕ ДОБАВИТЬ КЛУБ</span></div>
<form method="POST" action="/admin/add_club"><div class="form-grid"><div class="form-group"><label>Название</label><input type="text" name="name" required></div><div class="form-group"><label>Город</label><input type="text" name="city"></div><div class="form-group"><label>Стадион</label><input type="text" name="stadium"></div><div class="form-group"><label>Год основания</label><input type="number" name="founded"></div></div><button type="submit" class="btn">➕ Добавить клуб</button></form></div>

<div class="card"><div class="section-title"><span>➕ ДОБАВИТЬ ИГРОКА</span></div>
<form method="POST" action="/admin/add_player"><div class="form-grid"><div class="form-group"><label>Имя игрока</label><input type="text" name="name" required></div><div class="form-group"><label>Клуб</label><select name="club_id">{''.join(f'<option value="{c.id}">{c.name}</option>' for c in clubs) if clubs else '<option value="">Сначала добавьте клуб</option>'}</select></div><div class="form-group"><label>Позиция</label><select name="position"><option value="GK">Вратарь</option><option value="DF">Защитник</option><option value="MF">Полузащитник</option><option value="FW">Нападающий</option></select></div><div class="form-group"><label>Номер</label><input type="number" name="number"></div><div class="form-group"><label>Возраст</label><input type="number" name="age"></div><div class="form-group"><label>Национальность</label><input type="text" name="nationality"></div></div><button type="submit" class="btn">➕ Добавить игрока</button></form></div>

<div class="card"><div class="section-title"><span>➕ ДОБАВИТЬ МАТЧ</span></div>
<form method="POST" action="/admin/add_match"><div class="form-grid"><div class="form-group"><label>Хозяева</label><select name="home_club_id">{''.join(f'<option value="{c.id}">{c.name}</option>' for c in clubs) if clubs else '<option value="">Сначала добавьте клуб</option>'}</select></div><div class="form-group"><label>Гости</label><select name="away_club_id">{''.join(f'<option value="{c.id}">{c.name}</option>' for c in clubs) if clubs else '<option value="">Сначала добавьте клуб</option>'}</select></div><div class="form-group"><label>Дата и время</label><input type="datetime-local" name="match_date" required></div></div><button type="submit" class="btn">➕ Добавить матч</button></form></div>

<div class="card"><div class="section-title"><span>📋 СПИСОК КЛУБОВ</span></div>
<table><thead><th>ID</th><th>Название</th><th>Город</th><th>Стадион</th><th>Действия</th></thead><tbody>
{''.join(f'<tr><td>{c.id}</td><td>{c.name}</td><td>{c.city or "-"}</td><td>{c.stadium or "-"}</td><td><form method="POST" action="/admin/delete_club/{c.id}" style="display:inline;" onsubmit="return confirm(\'Удалить клуб {c.name} и всех его игроков?\')"><button type="submit" class="delete-btn">🗑 Удалить</button></form></td></tr>' for c in clubs)}
</tbody></table></div>

<div class="card"><div class="section-title"><span>📋 СПИСОК ИГРОКОВ</span></div>
<table><thead><th>ID</th><th>Имя</th><th>Клуб</th><th>Позиция</th><th>Голы</th><th>Ассисты</th><th>Рейтинг</th><th>Действия</th></thead><tbody>
{''.join(f'<tr><td>{p.id}</td><td>{p.name}</td><td>{p.club.name if p.club else "Нет клуба"}</td><td>{p.position}</td><td>{p.goals}</td><td>{p.assists}</td><td>{p.rating}</td><td><form method="POST" action="/admin/delete_player/{p.id}" style="display:inline;" onsubmit="return confirm(\'Удалить игрока {p.name}?\')"><button type="submit" class="delete-btn">🗑 Удалить</button></form></td></tr>' for p in players)}
</tbody></table></div>

<div class="card"><div class="section-title"><span>📋 СПИСОК МАТЧЕЙ</span></div>
<table><thead><th>ID</th><th>Хозяева</th><th>Гости</th><th>Счет</th><th>Статус</th><th>Действия</th></thead><tbody>
{''.join(f'<tr><td>{m.id}</td><td>{m.home_club.name}</td><td>{m.away_club.name}</td><td><form method="POST" action="/admin/update_score/{m.id}" style="display:flex;gap:5px;"><input type="number" name="home_score" value="{m.home_score}" style="width:50px;"><span>-</span><input type="number" name="away_score" value="{m.away_score}" style="width:50px;"><select name="status"><option value="scheduled" {"selected" if m.status=="scheduled" else ""}>Запланирован</option><option value="finished" {"selected" if m.status=="finished" else ""}>Завершён</option></select><button type="submit" class="btn" style="padding:5px 10px;">Обновить</button></form></td><td><form method="POST" action="/admin/delete_match/{m.id}" style="display:inline;" onsubmit="return confirm(\'Удалить матч?\')"><button type="submit" class="delete-btn">🗑 Удалить</button></form></td></tr>' for m in matches)}
</tbody></table></div>

<div class="card"><div class="section-title"><span>➕ ДОБАВИТЬ ТРАНСФЕР</span></div>
<form method="POST" action="/admin/add_transfer"><div class="form-grid"><div class="form-group"><label>Игрок</label><select name="player_id">{''.join(f'<option value="{p.id}">{p.name}</option>' for p in players) if players else '<option value="">Сначала добавьте игрока</option>'}</select></div><div class="form-group"><label>Из клуба</label><select name="from_club_id"><option value="">Свободный агент</option>{''.join(f'<option value="{c.id}">{c.name}</option>' for c in clubs)}</select></div><div class="form-group"><label>В клуб</label><select name="to_club_id" required>{''.join(f'<option value="{c.id}">{c.name}</option>' for c in clubs) if clubs else '<option value="">Сначала добавьте клуб</option>'}</select></div><div class="form-group"><label>Дата</label><input type="date" name="transfer_date" required></div><div class="form-group"><label>Сумма (€)</label><input type="number" name="fee"></div></div><button type="submit" class="btn">➕ Добавить трансфер</button></form></div>

<div class="card"><div class="section-title"><span>📋 СПИСОК ТРАНСФЕРОВ</span></div>
<table><thead><th>ID</th><th>Игрок</th><th>Из клуба</th><th>В клуб</th><th>Сумма</th><th>Дата</th><th>Действия</th></thead><tbody>
{''.join(f'<tr><td>{t.id}</td><td>{t.player.name}</td><td>{t.from_club.name if t.from_club else "Свободный агент"}</td><td>{t.to_club.name if t.to_club else "-"}</td><td>{t.fee:,} €</td><td>{t.transfer_date.strftime("%d.%m.%Y")}</td><td><form method="POST" action="/admin/delete_transfer/{t.id}" style="display:inline;" onsubmit="return confirm(\'Удалить трансфер?\')"><button type="submit" class="delete-btn">🗑 Удалить</button></form></td></tr>' for t in transfers)}
</tbody></table></div>

</div>
</body>
</html>
    '''

@app.route('/admin/add_club', methods=['POST'])
@login_required
def add_club():
    if not current_user.is_admin:
        return 'Unauthorized', 403
    club = Club(name=request.form.get('name'), city=request.form.get('city'), stadium=request.form.get('stadium'), founded=request.form.get('founded') or None)
    db.session.add(club)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_club/<int:club_id>', methods=['POST'])
@login_required
def delete_club(club_id):
    if not current_user.is_admin:
        return 'Unauthorized', 403
    club = Club.query.get_or_404(club_id)
    db.session.delete(club)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/add_player', methods=['POST'])
@login_required
def add_player():
    if not current_user.is_admin:
        return 'Unauthorized', 403
    player = Player(name=request.form.get('name'), club_id=request.form.get('club_id'), position=request.form.get('position'), number=request.form.get('number') or None, age=request.form.get('age') or None, nationality=request.form.get('nationality'))
    db.session.add(player)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_player/<int:player_id>', methods=['POST'])
@login_required
def delete_player(player_id):
    if not current_user.is_admin:
        return 'Unauthorized', 403
    player = Player.query.get_or_404(player_id)
    db.session.delete(player)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/add_match', methods=['POST'])
@login_required
def add_match():
    if not current_user.is_admin:
        return 'Unauthorized', 403
    match = Match(home_club_id=request.form.get('home_club_id'), away_club_id=request.form.get('away_club_id'), match_date=datetime.strptime(request.form.get('match_date'), '%Y-%m-%dT%H:%M'), status='scheduled')
    db.session.add(match)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_match/<int:match_id>', methods=['POST'])
@login_required
def delete_match(match_id):
    if not current_user.is_admin:
        return 'Unauthorized', 403
    match = Match.query.get_or_404(match_id)
    db.session.delete(match)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/update_score/<int:match_id>', methods=['POST'])
@login_required
def update_score(match_id):
    if not current_user.is_admin:
        return 'Unauthorized', 403
    match = Match.query.get_or_404(match_id)
    match.home_score = int(request.form.get('home_score'))
    match.away_score = int(request.form.get('away_score'))
    match.status = request.form.get('status')
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/add_transfer', methods=['POST'])
@login_required
def add_transfer():
    if not current_user.is_admin:
        return 'Unauthorized', 403
    transfer = Transfer(player_id=request.form.get('player_id'), from_club_id=request.form.get('from_club_id') or None, to_club_id=request.form.get('to_club_id'), transfer_date=datetime.strptime(request.form.get('transfer_date'), '%Y-%m-%d'), fee=int(request.form.get('fee')) if request.form.get('fee') else 0)
    player = Player.query.get(request.form.get('player_id'))
    player.club_id = request.form.get('to_club_id')
    db.session.add(transfer)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_transfer/<int:transfer_id>', methods=['POST'])
@login_required
def delete_transfer(transfer_id):
    if not current_user.is_admin:
        return 'Unauthorized', 403
    transfer = Transfer.query.get_or_404(transfer_id)
    db.session.delete(transfer)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/api/matches')
def get_matches():
    matches = Match.query.order_by(Match.match_date.desc()).limit(20).all()
    return jsonify([{'id': m.id, 'home': m.home_club.name, 'away': m.away_club.name, 'home_score': m.home_score, 'away_score': m.away_score, 'date': m.match_date.strftime('%d.%m.%Y %H:%M'), 'status': m.status} for m in matches])

@app.route('/api/table')
def get_table():
    clubs = Club.query.all()
    table_data = []
    for club in clubs:
        matches = Match.query.filter(((Match.home_club_id == club.id) | (Match.away_club_id == club.id)), Match.status == 'finished').all()
        wins, draws, losses, goals_for, goals_against = 0, 0, 0, 0, 0
        for m in matches:
            if m.home_club_id == club.id:
                goals_for += m.home_score
                goals_against += m.away_score
                if m.home_score > m.away_score: wins += 1
                elif m.home_score == m.away_score: draws += 1
                else: losses += 1
            else:
                goals_for += m.away_score
                goals_against += m.home_score
                if m.away_score > m.home_score: wins += 1
                elif m.away_score == m.home_score: draws += 1
                else: losses += 1
        table_data.append({'name': club.name, 'played': len(matches), 'wins': wins, 'draws': draws, 'losses': losses, 'goals_for': goals_for, 'goals_against': goals_against, 'gd': goals_for - goals_against, 'points': wins * 3 + draws})
    table_data.sort(key=lambda x: (-x['points'], -x['gd'], -x['goals_for']))
    return jsonify(table_data)

@app.route('/api/top_scorers')
def top_scorers():
    players = Player.query.order_by(Player.goals.desc()).limit(10).all()
    return jsonify([{'name': p.name, 'goals': p.goals, 'assists': p.assists, 'club': p.club.name if p.club else 'Свободный агент'} for p in players])

@app.route('/api/transfers')
def get_transfers():
    transfers = Transfer.query.order_by(Transfer.transfer_date.desc()).limit(20).all()
    return jsonify([{'player': t.player.name, 'from': t.from_club.name if t.from_club else 'Свободный агент', 'to': t.to_club.name if t.to_club else 'Неизвестно', 'fee': f"{t.fee:,} €" if t.fee else 'Свободный агент', 'date': t.transfer_date.strftime('%d.%m.%Y')} for t in transfers])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_admin()
    app.run(debug=True, host='0.0.0.0', port=5000)