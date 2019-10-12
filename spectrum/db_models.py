from datetime import datetime
from spectrum import db


class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, unique=True, nullable=False)
    ssid = db.Column(db.String(30), unique=True, nullable=False)
    spectrum_block = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f"Contract('{self.contract_key}', '{self.ssid}', '{self.spectrum_block}')"

class Peer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_key = db.Column(db.String(30), nullable=False)
    ip = db.Column(db.String(30), unique=True, nullable=False)
    contract = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return f"Peer('{self.public_key}', '{self.ip}')"

class Host(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_key = db.Column(db.String(30), nullable=False)
    contract = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return f"Host('{self.public_key}')"

class Block(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time_stamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    creator = db.Column(db.String(30), nullable=False)
    host_id = db.Column(db.String(30), nullable=False)
    contract = db.Column(db.Integer, nullable=False)
    block_action = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f"Block('{self.time_stamp}', '{self.creator}', '{self.block_action}')"