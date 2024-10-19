import argparse
from collections import deque
import json
from typing import TypedDict, List
from hashlib import sha256


class BlockHeader(TypedDict):
    difficulty: int
    height: int
    miner: str
    nonce: int
    hash: str
    previous_block_header_hash: str
    timestamp: int
    transactions_count: int
    transactions_merkle_root: str


class Transaction(TypedDict):
    amount: int
    lock_time: int
    receiver: str
    sender: str
    signature: str
    transaction_fee: int


class Block(TypedDict):
    header: BlockHeader
    transactions: List[Transaction]


def get_hash(val: str):
    return f'0x{sha256(val.encode()).hexdigest()}'


def get_transactions(mempool_transactions, time):
    potential_transactions = []
    for transaction in mempool_transactions:
        if transaction["lock_time"] <= time:
            potential_transactions.append(transaction)
    potential_transactions.sort(key=lambda x: x["transaction_fee"], reverse=True)
    if len(potential_transactions) > 100:
        potential_transactions = potential_transactions[:100]
    return [{k: v for k, v in sorted(d.items())} for d in potential_transactions]


def get_merkel_hash(transactions=None):
    transaction_hashes = deque()
    for transaction in transactions:
        transaction_hashes.append(get_hash((",".join(str(val) for val in transaction.values()))))
    null_hash = '0x' + 64 * '0'
    if len(transaction_hashes) == 1:
        merkel_hash = get_hash(null_hash + transaction_hashes[0])
    else:
        while len(transaction_hashes) != 1:
            current_length = len(transaction_hashes)
            is_odd = current_length % 2 == 1
            for i in range(0, current_length, 2):
                if is_odd and i == (current_length - 1):
                    transaction_hashes.append(get_hash(null_hash + transaction_hashes.popleft()))
                else:
                    a, b = transaction_hashes.popleft(), transaction_hashes.popleft()
                    if b < a:
                        b, a = a, b
                    transaction_hashes.append(get_hash(a + b))
        merkel_hash = transaction_hashes[0]
    return merkel_hash


def hash_block_header(block_header: BlockHeader):
    temp_block_header = dict(sorted(block_header.items()))
    del temp_block_header["hash"]
    return get_hash(",".join(str(val) for val in temp_block_header.values()))


def produce_blocks(blocks, mempool_transactions, num_blocks):
    for _ in range(num_blocks):
        latest_block = blocks[-1]
        latest_block_time = latest_block["header"]["timestamp"]
        new_block_time = latest_block_time + 10
        transactions = get_transactions(mempool_transactions, new_block_time)
        merkel_hash = get_merkel_hash(transactions)
        new_block_header: BlockHeader = {
            "difficulty": min(((latest_block["header"]["height"] + 1) // 50), 6),
            "height": latest_block["header"]["height"] + 1,
            "miner": "0x000a89667abeb2e87a42c724757ceee4cdc46eaa",
            "nonce": 0,
            "hash": "initial hash",
            "previous_block_header_hash": latest_block["header"]["hash"],
            "timestamp": latest_block["header"]["timestamp"] + 10,
            "transactions_count": len(transactions),
            "transactions_merkle_root": merkel_hash
        }
        new_block_transactions: List[Transaction] = transactions
        while hash_block_header(new_block_header)[2:2 + new_block_header["difficulty"]] != "0" * new_block_header[
            "difficulty"]:
            new_block_header["nonce"] += 1
        new_block_header["hash"] = hash_block_header(new_block_header)
        new_block: Block = {"header": new_block_header, "transactions": new_block_transactions}
        blocks.append(new_block)
        transaction_signatures = set(transaction["signature"] for transaction in blocks[-1]["transactions"])
        new_mempool: List[Transaction] = []
        for mempool_transaction in mempool_transactions:
            if mempool_transaction["signature"] not in transaction_signatures:
                new_mempool.append(mempool_transaction)
        mempool_transactions = new_mempool


def main():
    parser = argparse.ArgumentParser(description="Blockchain Proof of Concept")
    parser.add_argument('--blockchain-state', required=True, help='Path to the blockchain state file (json.gz)')
    parser.add_argument('--mempool', required=True, help='Path to the mempool file (json.gz)')
    parser.add_argument('--blockchain-output', required=True, help='Path to output the new blockchain state (json.gz)')
    parser.add_argument('--mempool-output', required=True, help='Path to output the new mempool (json.gz)')
    parser.add_argument('-n', '--num-blocks', type=int, required=True, help='Number of blocks to produce')
    args = parser.parse_args()

    # Read the current blockchain state and mempool
    blockchain_path = args.blockchain_state
    mempool_path = args.mempool
    with open(blockchain_path) as file:
        blocks: List[Block] = json.load(file)
    with open(mempool_path) as file:
        mempool_transactions: List[Transaction] = json.load(file)

    # Produce new blocks
    produce_blocks(blocks, mempool_transactions, args.num_blocks)


    # Write the new state and mempool to output files
    with open(args.blockchain_output, "w") as file:
        json.dump(blocks, file, indent=4)

    with open(args.mempool_output, "w") as file:
        json.dump(mempool_transactions, file, indent=4)


if __name__ == '__main__':
    main()
