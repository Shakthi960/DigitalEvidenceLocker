import hashlib
import json
import time

class Block:
    def __init__(self, index, data, previous_hash):
        self.index = index
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True)

        return hashlib.sha256(block_string.encode()).hexdigest()


class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(0, {"message": "Genesis Block"}, "0")
        self.chain.append(genesis)

    def get_last_block(self):
        return self.chain[-1]

    def add_block(self, data):
        last_block = self.get_last_block()
        new_block = Block(len(self.chain), data, last_block.hash)
        self.chain.append(new_block)
        return new_block

    def get_chain(self):
        return [block.__dict__ for block in self.chain]
