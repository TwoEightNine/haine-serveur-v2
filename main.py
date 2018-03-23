from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy
import utils
import json
import prime
import logging
import os
from keys import *

DEBUG = True
HOST = '0.0.0.0'
PORT = 1753

app = Flask(__name__)
db_path = os.path.join(os.path.dirname(__file__), 'haine.db')
db_uri = 'sqlite:///%s' % db_path
app.config.from_pyfile('app.cfg')
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
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
    attachment = db.Column('attachment', db.String)

    def __init__(self, from_id=0, to_id=0, text='', row=None, attachment=None):
        if row is None:
            self.to_id = to_id
            self.from_id = from_id
            self.text = text
            self.time = utils.get_time()
            self.attachment = attachment
        else:
            self.id = row[0]
            self.to_id = row[1]
            self.from_id = row[2]
            self.text = row[3]
            self.time = row[4]
            self.attachment = row[5]

    def __repr__(self):
        return json.dumps({'id': self.id, 'to_id': self.to_id, 'from_id': self.from_id,
                           'text': self.text, 'time': self.time, 'attachment': self.attachment})

    def as_str(self, user_id):
        return json.dumps(self.as_ui_obj(user_id))

    def as_ui_obj(self, user_id):
        out = self.from_id == user_id
        peer_id = self.to_id if out else self.from_id
        return {'id': self.id, 'peer_id': peer_id, 'out': out,
                'text': self.text, 'time': self.time, 'attachment': self.attachment}


class ExchangeParams(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    p = db.Column('p', db.String)
    g = db.Column('g', db.String)
    public_from = db.Column('public_from', db.String)
    public_to = db.Column('public_to', db.String)
    from_id = db.Column('from_id', db.Integer, db.ForeignKey('user.id'))
    to_id = db.Column('to_id', db.Integer, db.ForeignKey('user.id'))
    last_upd = db.Column('last_upd', db.Integer)
    last_editor = db.Column('last_editor', db.Integer, db.ForeignKey('user.id'))

    def __init__(self, p, g, from_id, to_id, public_from='', public_to='', last_editor=0):
        self.p = p
        self.g = g
        self.from_id = from_id
        self.to_id = to_id
        self.public_from = public_from
        self.public_to = public_to
        self.last_upd = utils.get_time(True)
        self.last_editor = last_editor

    def __repr__(self):
        return self.as_str()

    def as_str(self):
        return json.dumps({'id': self.id, 'p': self.p, 'g': self.g,
                           'from_id': self.from_id, 'to_id': self.to_id,
                           'public_from': self.public_from, 'public_to': self.public_to,
                           'last_upd': self.last_upd, 'last_editor': self.last_editor})

    def as_ui_obj(self):
        return {'p': self.p, 'g': self.g, 'from_id': self.from_id,
                'to_id': self.to_id, 'public_from': self.public_from,
                'public_to': self.public_to, 'last_upd': self.last_upd,
                'last_editor': self.last_editor}


def log_table():
    try:
        print(Message.query.all())
        print(User.query.all())
        print(Token.query.all())
        print(ExchangeParams.query.all())
    except Exception as e:
        print(e)


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
    if not utils.is_name_valid(name):
        return utils.get_error_by_code(7)
    if not utils.is_password_satisfied(password):
        return utils.get_error_by_code(8)
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


@app.route('/auth.terminate')
def terminate_sessions():
    req_id = get_user_id(request)
    token = request.headers[AUTH]
    data = request.form
    if KEEP_CURRENT not in data:
        return utils.get_extended_error_by_code(1, KEEP_CURRENT)
    keep_current = int(data[KEEP_CURRENT]) == 1
    Token.query.filter((Token.user_id == req_id) &
                       ((Token.token != token) | ~keep_current)).delete()
    return utils.RESPONSE_1


@app.route('/user.get/<user_id>')
def get_user(user_id):
    user_id = int(user_id)
    get_user_id(request)
    user = User.query.get(user_id)
    if user is None:
        return utils.get_extended_error_by_code(4, user_id)
    return utils.RESPONSE_FORMAT % str(user)


@app.route('/user.photo', methods=['POST'])
def save_photo():
    req_id = get_user_id(request)
    data = request.form
    if PHOTO not in data:
        return utils.get_extended_error_by_code(1, PHOTO)
    photo = data[PHOTO]
    user = User.query.filter_by(id=req_id).first()
    user.photo = photo
    db.session.commit()
    return utils.RESPONSE_1


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


@app.route('/messages.sendText', methods=['POST'])
def send_message():
    req_id = get_user_id(request)
    data = request.form
    if TEXT not in data:
        return utils.get_extended_error_by_code(1, TEXT)
    if TO_ID not in data:
        return utils.get_extended_error_by_code(1, TO_ID)
    content = data[TEXT]
    to_id = int(data[TO_ID])
    exists = User.query.filter_by(id=to_id).count() != 0
    if not exists:
        return utils.get_extended_error_by_code(4, to_id)
    message = Message(req_id, to_id, content)
    db.session.add(message)
    db.session.flush()
    db.session.refresh(message)
    mess_id = message.id
    db.session.commit()
    return utils.RESPONSE_FORMAT % str(mess_id)


@app.route('/messages.sendFile', methods=['POST'])
def send_attachment():
    req_id = get_user_id(request)
    data = request.form
    if ATTACHED not in data:
        return utils.get_extended_error_by_code(1, ATTACHED)
    if TO_ID not in data:
        return utils.get_extended_error_by_code(1, TO_ID)
    content = data[ATTACHED]
    to_id = int(data[TO_ID])
    exists = User.query.filter_by(id=to_id).count() != 0
    if not exists:
        return utils.get_extended_error_by_code(4, to_id)
    message = Message(req_id, to_id, attachment=content)
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
    if NEXT_MESSAGE_FROM not in data:
        return utils.get_extended_error_by_code(1, NEXT_MESSAGE_FROM)
    if NEXT_XCHG_FROM not in data:
        return utils.get_extended_error_by_code(1, NEXT_XCHG_FROM)
    next_message_from = int(data[NEXT_MESSAGE_FROM])
    next_xchg_from = int(data[NEXT_XCHG_FROM])
    start_time = utils.get_time()
    response = {'messages': [], 'exchanges': []}
    while True:
        should_return = False
        if utils.get_time() - start_time > 40:
            should_return = True

        # getting messages
        messages = Message.query\
            .filter(((Message.from_id == req_id) | (Message.to_id == req_id)) &
                    (Message.id > next_message_from)).all()
        if messages is not None and len(messages) > 0:
            response['messages'] = [message.as_ui_obj(req_id) for message in messages]
            should_return = True

        # getting exchanges
        exchanges = ExchangeParams.query\
            .filter(((ExchangeParams.to_id == req_id) | (ExchangeParams.from_id == req_id)) &
                    (ExchangeParams.last_upd > next_xchg_from)).all()
        if exchanges is not None and len(exchanges) > 0:
            response['exchanges'] = [xchg.as_ui_obj() for xchg in exchanges]
            should_return = True

        # returning everything
        if should_return:
            return utils.RESPONSE_FORMAT % json.dumps(response)
        utils.sleep()


@app.route('/exchange.commit', methods=['POST'])
def make_exchange():
    req_id = get_user_id(request)
    data = request.form
    if P not in data:
        return utils.get_extended_error_by_code(1, P)
    if G not in data:
        return utils.get_extended_error_by_code(1, G)
    if PUBLIC not in data:
        return utils.get_extended_error_by_code(1, PUBLIC)
    if TO_ID not in data:
        return utils.get_extended_error_by_code(1, TO_ID)
    p = data[P]
    g = data[G]
    public = data[PUBLIC]
    to_id = int(data[TO_ID])
    exists = User.query.filter_by(id=to_id).count() != 0
    if not exists:
        return utils.get_extended_error_by_code(4, to_id)
    # if user supports exchange, it exists and its from_id (id of initiator) is equal to_id (user's interlocutor)
    xchg = ExchangeParams.query.filter((ExchangeParams.p == p) & (ExchangeParams.g == g) &
                                       (ExchangeParams.from_id == to_id)).first()
    if xchg is None:  # we create exchange
        xchg = ExchangeParams(p, g, req_id, to_id, public, last_editor=req_id)
        db.session.add(xchg)
    else:  # we support exchange
        xchg.public_to = public
        xchg.last_upd = utils.get_time(True)
        xchg.last_editor = req_id
    db.session.commit()
    return utils.RESPONSE_1


@app.route('/exchange.safePrime')
def safe_prime():
    get_user_id(request)
    actual_prime = prime.get_actual()
    return utils.RESPONSE_FORMAT % ('"' + str(actual_prime) + '"')


log_table()
if not DEBUG:
    prime.generate_async()

if __name__ == "__main__":
    db.create_all()
    db.init_app(app)
    app.logger.setLevel(logging.DEBUG)
    app.run(threaded=True, host=HOST, port=PORT)

