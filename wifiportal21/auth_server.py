#!/usr/bin/env python

import logging
import requests
import flask
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask import request, flash, redirect, render_template, url_for
from flask import jsonify

from two1.lib.bitcoin.crypto import HDKey, HDPublicKey
from two1.lib.wallet.hd_account import HDAccount
from two1.lib.wallet.cache_manager import CacheManager
from two1.lib.blockchain.twentyone_provider import TwentyOneProvider

import qrcode
import base64
import io

import uuid

# change the receiving_key in config.py in the root folder.
from config import receiving_key, SATOSHIS_PER_MINUTE

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.ERROR)

auth_app = Flask(__name__, static_folder='static')
auth_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/wifiportal21.db'
db = SQLAlchemy(auth_app)

K = HDPublicKey.from_b58check(receiving_key)
blockchain_provider = TwentyOneProvider()
cache = CacheManager()
receiving_account = HDAccount(hd_key=K, name="hotspot receiving", index=0,data_provider=blockchain_provider, cache_manager=cache)

SATOSHIS_PER_MBTC = 100*10**3
SATOSHIS_PER_BTC = 100*10**6

STATUS_NONE = 0
STATUS_PAYREQ = 1
STATUS_PAID = 2

class Guest(db.Model):
    uuid = db.Column(db.String, primary_key=True)
    mac = db.Column(db.String(17), unique=True)
    address = db.Column(db.String(40), unique=True)
    status = db.Column(db.Integer())
    minutes = db.Column(db.Integer())

    def __init__(self, uuid, mac):
        self.uuid = uuid
        self.mac = mac
        self.address = None
        self.status = STATUS_NONE
        self.minutes = -1

    def __repr__(self):
        return "UUID: {0}\nMAC: {1}\nStatus: {2}\nAddress: {3}\nMinutes: {4}".format(self.uuid,self.mac, self.status, self.address, self.minutes)

db.create_all()

@auth_app.route('/wifidog/login/', methods=[ 'GET', 'POST' ])
def client_login():
    gw_address = flask.request.args.get('gw_address')
    gw_port = flask.request.args.get('gw_port')
    success_URL = flask.request.args.get('url')
    token = uuid.uuid4()
    auth_URL = "http://{0}:{1}/wifidog/auth?token={2}".format(gw_address, gw_port, token)
    price = "The cost of this service is {0:1.6f} BTC, or {1:1.2f} mBTC or {2:,} satoshis per minute".format(SATOSHIS_PER_MINUTE/SATOSHIS_PER_BTC, SATOSHIS_PER_MINUTE/SATOSHIS_PER_MBTC, SATOSHIS_PER_MINUTE)
    portal_html = render_template('portal.html', auth_URL=auth_URL, token=token, price=price, success_URL=success_URL)
    return portal_html

@auth_app.route('/wifidog/auth/')
def client_auth():
    stage = flask.request.args.get('stage')
    mac = flask.request.args.get('mac')
    uuid = flask.request.args.get('token')
    guest = Guest.query.filter_by(mac=mac).first()

    if guest: # Existing Guest
        if guest.uuid != uuid: # Old UUID, update it
            # print("Found existing under different uuid {0}".format(guest.uuid))
            guest.uuid = uuid # Update UUID in guest
            if guest.status == STATUS_PAID and guest.minutes <= 0: # Old guest without balance
                guest.status = STATUS_PAYREQ
            db.session.commit()
    else: # New Guest
        guest = Guest(uuid,mac)
        db.session.add(guest)
        db.session.commit()

    if stage == "login":
        if guest.status == STATUS_NONE:
            return ("Auth: -1" , 200) # Auth - Invalid
        elif guest.status == STATUS_PAID:
            if guest.minutes > 0:
                return("Auth: 1", 200) # Paid, give access!
            else:
                guest.status == STATUS_NONE
                return ("Auth: -1" , 200) # Auth - Invalid
        elif guest.status == STATUS_PAYREQ:
                return ("Auth: -1" , 200) # Auth - Invalid

    elif stage == "counters":
        guest = Guest.query.filter_by(uuid=uuid).first()
        if guest.minutes > 0:
            guest.minutes -= 1
            db.session.commit()
            print("Guest accounting, {0} minutes remain".format(guest.minutes))
            return("Auth: 1", 200) # Paid, give access!
        else:
            # print("Guest {0} not yet paid".format(uuid))
            if guest.status == STATUS_PAID: # No more minutes left, restart payment request
                guest.status = STATUS_PAYREQ
            return ("Auth: 0" , 200) # Auth - Invalid
    else:
        raise Exception("Unknown authorization stage {0}".format(stage))


@auth_app.route('/auth_status')
def auth_status():
    uuid = flask.request.args.get('token')
    guest = Guest.query.filter_by(uuid=uuid).first()
    if not guest:
        # print("Unregistered guest {0}".format(uuid))
        return "Must register first", 404
    try:
        # print("Returning status {0} for {1}".format(guest.status, guest.uuid))
        status_response = { 'status' : guest.status }
        return flask.json.dumps(status_response)
    except:
        raise Exception("Error finding guest status {0}".format(uuid))


def inline_base64_qrcode(address):
    qr = qrcode.make("bitcoin:{0}".format(address), error_correction=qrcode.constants.ERROR_CORRECT_L)
    output = io.BytesIO()
    qr.save(output,'PNG')
    output.seek(0)
    qr_base64 = base64.b64encode(output.read()).decode()
    return qr_base64

def get_unconfirmed_balance(address):
    r = requests.get('https://blockchain.info/unspent?active={0}'.format(address))
    # print("Checking balance for {0}".format(address))
    balance = 0
    if r.status_code == 200:
        utxo_response = r.json()
        if 'unspent_outputs' in utxo_response:
            for utxo in utxo_response['unspent_outputs']:
                if 'value' in utxo:
                    balance += utxo['value']
        # print("Balance for {0} is {1}".format(address, balance))
        return balance
    elif r.status_code == 500: # No UTXO to spend
        return balance
    else:
        raise Exception("Error checking balance, unexpected HTTP code: {0} {1}".format(r.status_code, r.text))

@auth_app.route('/static/<path:path>')
@auth_app.route('/js/<path:path>')
def static_jquery(path):
    return flask.send_from_directory(auth_app.static_folder, path)

@auth_app.route('/get_payment_address')
def get_payment_address():
    uuid = flask.request.args.get('token')
    guest = Guest.query.filter_by(uuid=uuid).first()
    if guest.status == STATUS_NONE or guest.status == STATUS_PAYREQ:
        guest.status = STATUS_PAYREQ
        if not guest.address:
            new_address = receiving_account.get_address(False)
            guest.address = new_address
        db.session.commit()
        qr = inline_base64_qrcode(guest.address)
        response = {'address': guest.address, 'qr': qr}
        return flask.json.dumps(response), 200
    else:
        return('must register first', 404)

@auth_app.route('/check_payment')
def check_payment():
    uuid = flask.request.args.get('token')
    guest = Guest.query.filter_by(uuid=uuid).first()
    # assert guest
    # assert guest.status == STATUS_PAYREQ
    # assert guest.address
    address = guest.address
    unconf_balance = get_unconfirmed_balance(address)
    if unconf_balance > 0: # Payment detected on this address
        guest.status = STATUS_PAID
        minutes = unconf_balance // SATOSHIS_PER_MINUTE
        # assert minutes > 0
        # print("Allocating {0} stoshis, {1} minutes to guest {2}".format(unconf_balance,minutes, uuid))
        guest.minutes = minutes
        db.session.commit()
        return("Payment received", 200)
    else:
        return("Waiting for payment", 402)


@auth_app.route('/wifidog/ping/')
def gw_ping():
    # print(db.session.query(Guest).all())
    return ('Pong', 200)

def run_server(host='0.0.0.0', port=21142):
    auth_app.run(host=host, port=port)

if __name__ == '__main__':
    run_server()
