from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy
import utils
import json

app = Flask(__name__)
app.config.from_pyfile('app.cfg')
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.String(30), unique=True)
    password_hash = db.Column('pass_hash', db.String(64))
    salt = db.Column('salt', db.String(16))
    photo = db.Column('photo', db.String)
    last_seen = db.Column('last_seen', db.Integer)

    def __init__(self, name, password, photo=None):
        self.name = name
        self.photo = photo
        self.salt = utils.get_salt()
        self.password_hash = utils.get_hash(password + self.salt)
        self.last_seen = utils.get_time()

    def __repr__(self):
        return {'id': self.id, 'name': self.name,
                'photo': self.photo, 'last_seen': self.last_seen}

    def __str__(self):
        return json.dumps(self.__repr__())


class Token(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    token = db.Column('token', db.String(64))
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'))

    def __init__(self, name, password, user_id):
        self.token = utils.get_hash(name + str(utils.get_time()) + password)
        self.user_id = user_id

    def __repr__(self):
        return {'id': self.id, 'token': self.token, 'user_id': self.user_id}

    def __str__(self):
        return json.dumps(self.__repr__())


class Message(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    to_id = db.Column('to_id', db.Integer, db.ForeignKey('user.id'))
    from_id = db.Column('from_id', db.Integer, db.ForeignKey('user.id'))
    text = db.Column('text', db.String)
    time = db.Column('time', db.Integer)

    def __init__(self, from_id=0, to_id=0, text='', row=None):
        if row is None:
            self.to_id = to_id
            self.from_id = from_id
            self.text = text
            self.time = utils.get_time()
        else:
            self.id = row[0]
            self.to_id = row[1]
            self.from_id = row[2]
            self.text = row[3]
            self.time = row[4]

    def __repr__(self):
        return {'id': self.id, 'to_id': self.to_id, 'from_id': self.from_id,
                'text': self.text, 'time': self.time}

    def as_str(self, user_id):
        out = self.from_id == user_id
        peer_id = self.to_id if out else self.from_id
        return json.dumps({'id': self.id, 'peer_id': peer_id, 'out': out,
                           'text': self.text, 'time': self.time})


def get_user_id(request):
    if 'auth' not in request.headers:
        abort(401)
        return 0
    auth_token = request.headers['auth']
    token = Token.query.filter_by(token=auth_token).first()
    if token is None:
        abort(401)
        return 0
    user_id = token.user_id
    user = User.query.filter_by(id=user_id).first()
    user.last_seen = utils.get_time()
    db.session.commit()
    return user_id


@app.errorhandler(Exception)
def exception_handler(e):
    print(e)
    return utils.get_error_by_code(500)


@app.errorhandler(500)
@app.errorhandler(502)
@app.errorhandler(405)
@app.errorhandler(404)
@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(400)
def error_handler(e):
    print(e)
    code, _ = utils.get_error_data(e)
    return utils.get_error_by_code(code)


@app.route('/auth.signUp', methods=['POST'])
def sign_up():
    data = request.form
    if 'name' not in data:
        return utils.get_extended_error_by_code(1, 'name')
    if 'password' not in data:
        return utils.get_extended_error_by_code(1, 'password')
    name = data['name']
    password = data['password']
    exists = User.query.filter_by(name=name).count() != 0
    if exists:
        return utils.get_extended_error_by_code(2, name)
    user = User(name, password)
    db.session.add(user)
    db.session.flush()
    db.session.refresh(user)
    result_id = user.id
    db.session.commit()
    return utils.RESPONSE_FORMAT % result_id


@app.route('/auth.logIn', methods=['POST'])
def log_in():
    data = request.form
    if 'name' not in data:
        return utils.get_extended_error_by_code(1, 'name')
    if 'password' not in data:
        return utils.get_extended_error_by_code(1, 'password')
    name = data['name']
    password = data['password']
    exists = User.query.filter_by(name=name).count() != 0
    if not exists:
        return utils.get_error_by_code(3)
    user = User.query.filter_by(name=name).first()
    if utils.get_hash(password + user.salt) != user.password_hash:
        return utils.get_error_by_code(3)
    token = Token(name, password, user.id)
    db.session.add(token)
    db.session.flush()
    db.session.refresh(token)
    result_token = token.token
    db.session.commit()
    return utils.RESPONSE_FORMAT % utils.get_log_in_response(user.id, result_token)


@app.route('/user.get/<user_id>')
def get_user(user_id):
    user_id = int(user_id)
    get_user_id(request)
    user = User.query.get(user_id)
    if user is None:
        return utils.get_extended_error_by_code(4, user_id)
    return utils.RESPONSE_FORMAT % str(user)


@app.route('/messages.getDialogs')
def get_dialogs():
    req_id = get_user_id(request)
    result = db.engine.execute("""select * from message where id in (select max(mx) as id from 
    (select max(id) as mx, to_id from message where from_id=%d group by to_id union 
    select max(id) as mx, from_id from message where to_id=%d group by from_id) as der 
    group by to_id order by id desc) order by id desc limit 100""" % (req_id, req_id))
    messages = []
    for row in result:
        messages.append(Message(row=row))
    as_str = "["
    for message in messages:
        if as_str != "[":
            as_str += ", "
        as_str += message.as_str(req_id)
    as_str += "]"
    return utils.RESPONSE_FORMAT % as_str


@app.route('/messages.send', methods=['POST'])
def send_message():
    req_id = get_user_id(request)
    data = request.form
    if 'text' not in data:
        return utils.get_extended_error_by_code(1, 'text')
    if 'to_id' not in data:
        return utils.get_extended_error_by_code(1, 'to_id')
    text = data['text']
    to_id = data['to_id']
    message = Message(req_id, to_id, text)
    db.session.add(message)
    db.session.flush()
    db.session.refresh(message)
    mess_id = message.id
    db.session.commit()
    return utils.RESPONSE_FORMAT % str(mess_id)


if __name__ == "__main__":
    db.create_all()
    db.init_app(app)
    app.run(threaded=True)
