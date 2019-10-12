from flask import render_template, url_for, flash, redirect, request, session, abort 
from spectrum import app, db
from spectrum.db_models import Contract, Peer, Host, Block
from random import randint
from datetime import datetime
import socket

def get_host_ip():
    host_name = socket.gethostname() 
    host_ip = socket.gethostbyname(host_name) 
    return host_ip

def get_peer_id():
    my_peer_id = randint(100000000000, 999999999999)
    return my_peer_id

about = [
    {
        'version': '0.2',
        'author': 'Steven Platt, Universitat Pompeu Fabra',
        'location': 'Barcelona, Spain'
    }
]

@app.route("/")
@app.route("/blockchain", methods=["GET", "POST"])
def home():
    if not session.get('logged_in'):
        return render_template('login_form.html', title='Login')

    elif request.method == "POST" and "ssid" in request.form:

        contract = request.form

        new_contract = Contract(contract_id=randint(1000000000, 9999999999), ssid=contract.get("ssid"), spectrum_block=contract.get("spectrum_block"))
        db.session.add(new_contract)
        db.session.commit()
        print("this method is for new contract")

        return redirect(url_for('home'))

    elif request.method == "POST" and "permission" in request.form:

        block = request.form

        new_block = Block(time_stamp=datetime.utcnow(), creator=block.get("my_hostid"), host_id=block.get("host_id"), contract=block.get("contract_id"), block_action=block.get("permission"))
        db.session.add(new_block)
        db.session.commit()
        print("this method is for new block")

        return redirect(url_for('home'))

    elif request.method == "POST" and "contract_id" in request.form:

        contract = request.form

        print("this method is for existing contract")
        return redirect(url_for('home'))

    elif request.method == "POST" and "tps" in request.form:

        print("this method is for benchmarking")
        return redirect(url_for('home'))

    else:

        my_ip = get_host_ip()
        my_id = get_peer_id()
        peer_list_full = Peer.query.all()

        contract_page = request.args.get('contract_page', 1, type=int)
        contract_list = Contract.query.paginate(page=contract_page, per_page=3)
        contract_list_full = Contract.query.all()
        block_page = request.args.get('block_page', 1, type=int)
        block_list = Block.query.order_by(Block.time_stamp.desc()).paginate(page=block_page, per_page=5)

        return render_template('dashboard.html', title='Blockchain', blocks=block_list, about=about, ip=my_ip, id=my_id, contracts=contract_list, 
        contracts_full=contract_list_full, peers_full=peer_list_full, block_page=block_page, contract_page=contract_page)

@app.route("/nodes", methods=["GET", "POST"])
def nodes():

    if request.method == "POST" and "peer_hostid" in request.form:

        peer = request.form

        new_peer = Peer(public_key=peer.get("peer_hostid"), ip=peer.get("peer_ip"), contract=peer.get("allowed_contract"))
        db.session.add(new_peer)
        db.session.commit()
        print("this method is for a new peer")

        return redirect(url_for('nodes'))

    elif request.method == "POST" and "tps" in request.form:

        print("this method is for benchmarking")

        return redirect(url_for('nodes'))
    
    else:
        my_ip = get_host_ip()
        my_id = get_peer_id()
        peer_page = request.args.get('peer_page', 1, type=int)
        peer_list = Peer.query.paginate(page=peer_page, per_page=10)
        peer_list_full = Peer.query.all()
        contract_list = Contract.query.all()

        return render_template('nodes.html', title='Nodes', about=about, ip=my_ip, id=my_id, peers=peer_list, peers_full=peer_list_full, contracts_full=contract_list, peer_page=peer_page)

@app.route("/login", methods=['POST'])
def login():
    if request.form['password'] == 'spectrum' and request.form['username'] == 'admin':
        session['logged_in'] = True
    else:
        flash('wrong password!')
    return home()

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()