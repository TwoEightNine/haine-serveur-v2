from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy
import utils
import json
from keys import *

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
        return self.__str__()

    def __str__(self):
        return json.dumps(self.as_ui_obj())

    def as_ui_obj(self):
        return {'id': self.id, 'name': self.name,
                'photo': self.photo, 'last_seen': self.last_seen}


class Token(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    token = db.Column('token', db.String(64))
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'))

    def __init__(self, name, password, user_id):
        self.token = utils.get_hash(name + str(utils.get_time()) + password)
        self.user_id = user_id

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return json.dumps({'id': self.id, 'token': self.token, 'user_id': self.user_id})


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
        return json.dumps({'id': self.id, 'to_id': self.to_id, 'from_id': self.from_id,
                           'text': self.text, 'time': self.time})

    def as_str(self, user_id):
        return json.dumps(self.as_ui_obj(user_id))

    def as_ui_obj(self, user_id):
        out = self.from_id == user_id
        peer_id = self.to_id if out else self.from_id
        return {'id': self.id, 'peer_id': peer_id, 'out': out,
                'text': self.text, 'time': self.time}


def log_table():
    print(Message.query.all())
    print(User.query.all())
    print(Token.query.all())


def get_user_id(request):
    if AUTH not in request.headers:
        abort(401)
        return 0
    auth_token = request.headers[AUTH]
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
    if NAME not in data:
        return utils.get_extended_error_by_code(1, NAME)
    if PASSWORD not in data:
        return utils.get_extended_error_by_code(1, PASSWORD)
    name = data[NAME]
    password = data[PASSWORD]
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
    if NAME not in data:
        return utils.get_extended_error_by_code(1, NAME)
    if PASSWORD not in data:
        return utils.get_extended_error_by_code(1, PASSWORD)
    name = data[NAME]
    password = data[PASSWORD]
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


@app.route('/user.photo')
def save_photo():
    req_id = get_user_id(request)
    data = request.form
    if PHOTO not in data:
        return utils.get_extended_error_by_code(1, PHOTO)
    photo = data[PHOTO]
    user = User.query.filter_by(id=req_id).first()
    user.photo = photo
    db.session.commit()
    return utils.RESPONSE_FORMAT % '1'


@app.route('/messages.getDialogs')
def get_dialogs():
    req_id = get_user_id(request)
    result = db.engine.execute("""select * from message where id in (select max(mx) as id from 
    (select max(id) as mx, to_id from message where from_id=%d group by to_id union 
    select max(id) as mx, from_id from message where to_id=%d group by from_id) as der 
    group by to_id order by id desc) order by id desc limit 100""" % (req_id, req_id))
    messages = []
    for row in result:
        messages.append(Message(row=row).as_ui_obj(req_id))
    peer_ids = [mess['peer_id'] for mess in messages]
    users = User.query.filter(User.id.in_(tuple(peer_ids))).all()
    users = [user.as_ui_obj() for user in users]
    response = {'messages': messages, 'users': users}
    return utils.RESPONSE_FORMAT % json.dumps(response)


@app.route('/messages.get/<user_id>')
def get_chat(user_id):
    user_id = int(user_id)
    req_id = get_user_id(request)
    exists = User.query.filter_by(id=user_id).count()
    if not exists:
        return utils.get_extended_error_by_code(4, user_id)
    messages = Message.query\
        .filter(((Message.to_id == req_id) & (Message.from_id == user_id)) |
                ((Message.from_id == req_id) & (Message.to_id == user_id)))\
        .order_by(Message.id.desc())
    messages = [message.as_ui_obj(req_id) for message in messages]
    return utils.RESPONSE_FORMAT % json.dumps(messages)


@app.route('/messages.send', methods=['POST'])
def send_message():
    req_id = get_user_id(request)
    data = request.form
    if TEXT not in data:
        return utils.get_extended_error_by_code(1, TEXT)
    if TO_ID not in data:
        return utils.get_extended_error_by_code(1, TO_ID)
    text = data[TEXT]
    to_id = data[TO_ID]
    exists = User.query.filter_by(id=to_id).count() != 0
    if not exists:
        return utils.get_extended_error_by_code(4, to_id)
    message = Message(req_id, to_id, text)
    db.session.add(message)
    db.session.flush()
    db.session.refresh(message)
    mess_id = message.id
    db.session.commit()
    return utils.RESPONSE_FORMAT % str(mess_id)


@app.route('/user.search')
def search():
    get_user_id(request)
    data = request.args
    if Q not in data:
        return utils.get_extended_error_by_code(1, Q)
    query = data[Q]
    users = User.query.filter(User.name.contains(query)).all()
    users = [user.as_ui_obj() for user in users]
    return utils.RESPONSE_FORMAT % json.dumps(users)


@app.route('/messages.poll')
def poll():
    req_id = get_user_id(request)
    data = request.args
    if NEXT_FROM not in data:
        return utils.get_extended_error_by_code(1, NEXT_FROM)
    next_from = data[NEXT_FROM]
    start_time = utils.get_time()
    while True:
        if utils.get_time() - start_time > 40:
            return utils.RESPONSE_FORMAT % '[]'
        messages = Message.query\
            .filter(((Message.from_id == req_id) | (Message.to_id == req_id)) &
                    (Message.id > next_from)).all()
        if messages is not None and len(messages) > 0:
            messages = [message.as_ui_obj(req_id) for message in messages]
            return utils.RESPONSE_FORMAT % json.dumps(messages)
        utils.sleep()


log_table()
if __name__ == "__main__":
    db.create_all()
    db.init_app(app)
    app.run(threaded=True)
