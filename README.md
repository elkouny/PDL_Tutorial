### Example Usage

The `blockchain_simulator.py` script simulates a blockchain environment. You can specify the paths to your blockchain state and mempool files, as well as the desired output files and the number of blocks to produce.

#### Command:

```bash
python blockchain_simulator.py \
  --blockchain-state data/blockchain.json \
  --mempool data/mempool.json \
  --blockchain-output data/new-blockchain.json \
  --mempool-output data/new-mempool.json \
  -n 15
