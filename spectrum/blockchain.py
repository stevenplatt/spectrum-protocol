"""
Version 1.0.2

This application holds the blockchain code used by the network. 
This code is the base for expanding and testing consensus and performance on devices running OpenWRT

This program is built partially using example code from Daniel van Flymen
https://hackernoon.com/learn-blockchains-by-building-one-117428612f46

*** Current code does not include mechanism for PBFT node sync ***
*** Current code does not include mechanism for pruning / expiring synced nodes ***
*** "requests" and "Flask" libraries are not standard and must be installed / supported on device ***
*** "CURL" also required on OpenWRT devices for testing Flask methods ***
*** Chain record, node ID, neighbor ID will eventually need storing in DB for persistence ***

"""

import hashlib
import json
import requests
import subprocess
import collections

from textwrap import dedent
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request
from urllib.parse import urlparse

class Blockchain(object):
    def __init__(self):
        self.current_transactions = []
        self.chain = []

        # Define initial empty user MAC address list
        self.users = set()

        self.nodes = set()

        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def remove_node(self, address):
        """
        Remove a node from the list of nodes
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.remove(parsed_url.netloc)

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            # Iterate over each block to create a list of MAC address values that are not null
            iterate_block = json.dumps(block)
            block_data = json.loads(iterate_block)

            transaction_data = (block_data["transactions"])
            matches = (d for d in transaction_data if d['mac'] != 'null')

            user_id = next(matches, None)
            # user_list = list(matches)
            mac_address = user_id['mac']

            # If a new MAC address is detectd in a valid block, execute OpenWRT commands to update FW
            if mac_address not in self.users:
                self.users.add(mac_address)

                # OpenWRT Commands

                """
                subprocess.call('uci add firewall rule', shell=True)
                subprocess.call("uci set firewall.@rule[-1].target='ACCEPT'", shell=True)
                subprocess.call("uci set firewall.@rule[-1].proto='tcp udp icmp'", shell=True)
                subprocess.call("uci set firewall.@rule[-1].src='lan'", shell=True)
                subprocess.call(['uci set firewall.@rule[-1].src_mac=' + "'{0}'".format(mac_address)], shell=True)
                subprocess.call('uci commit && service firewall reload', shell=True)
                """
                           

            last_block = block
            current_index += 1
        
        print(self.users)

        return True

    def resolve_conflicts(self):
        """
        This is our Consensus Algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: <bool> True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # Storing the old chain before comparison
        old_chain = self.chain
        current_index = len(self.chain)

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain

        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, mac, action, amount):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the Block that will hold this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'mac': mac,
            'action': action,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block: <dict> Block
        :return: <str>
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()


    # Adding proof of work consensus to the chain, this can be swapped later
    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
         - p is the previous proof, and p' is the new proof
        :param last_proof: <int>
        :return: <int>
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
