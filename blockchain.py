import hashlib
import json
import time
import os


class Block:
    def __init__(self, index, timestamp, data, previous_hash, hash_value=None):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = hash_value if hash_value else self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True)

        return hashlib.sha256(block_string.encode()).hexdigest()


class Blockchain:
    def __init__(self, chain_file="blockchain.json"):
        self.chain_file = chain_file
        self.chain = []

        if os.path.exists(self.chain_file):
            self.load_chain()
        else:
            self.create_genesis_block()
            self.save_chain()

    # ---------------- Genesis ----------------

    def create_genesis_block(self):
        genesis = Block(
            index=0,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            data={"message": "Genesis Block - Digital Evidence Locker"},
            previous_hash="0"
        )
        self.chain.append(genesis)

    # ---------------- Add Block ----------------

    def add_block(self, data):
        last_block = self.chain[-1]

        new_block = Block(
            index=len(self.chain),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            data=data,
            previous_hash=last_block.hash
        )

        self.chain.append(new_block)
        self.save_chain()
        return new_block

    # ---------------- Save / Load ----------------

    def save_chain(self):
        with open(self.chain_file, "w") as f:
            json.dump([block.__dict__ for block in self.chain], f, indent=4)

    def load_chain(self):
        with open(self.chain_file, "r") as f:
            chain_data = json.load(f)

        for block in chain_data:
            self.chain.append(
                Block(
                    index=block["index"],
                    timestamp=block["timestamp"],
                    data=block["data"],
                    previous_hash=block["previous_hash"],
                    hash_value=block["hash"]
                )
            )

    # ---------------- Validation ----------------

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Check current hash integrity
            if current.hash != current.compute_hash():
                return False

            # Check chain linkage
            if current.previous_hash != previous.hash:
                return False

        return True

    # ---------------- Get Chain ----------------

    def get_chain(self):
        return [block.__dict__ for block in self.chain]