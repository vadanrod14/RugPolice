import os
import time
import pandas as pd
import requests
import shared
from Utils.eth_utils import obtain_hash_event, connect_to_web3
shared.init()
import json
from hexbytes import HexBytes
from web3.datastructures import AttributeDict

def get_response(pool, from_block):
    endpoint = "https://api.polygonscan.com/api?module=logs" \
               "&action=getLogs" \
               f"&fromBlock={from_block}" \
               f"&toBlock={shared.BLOCKSTUDY}" \
               f"&address={pool}" \
               f"&topic0={sync_hash}" \
               f"&apikey={apikey}"

    return json.loads(requests.get(endpoint).text)['result']

def clean_response(response):
    receipts = []
    for event in response:
        receipts.append(AttributeDict({
            'blockNumber': int(event['blockNumber'], 16),
            'contractAddress': event['address'],
            'topics': [HexBytes(topic) for topic in event['topics']],
            'transactionHash': HexBytes(event['transactionHash']),
            'data': event['data'],
            'logIndex': 0,
            'transactionIndex': event['transactionIndex'],
            'address': event['address'],
            'blockHash': HexBytes(event['transactionHash'])
        }))

    log_dict = {'logs': receipts}
    return contract.events.Sync().processReceipt(log_dict)

sync_hash = obtain_hash_event('Sync(uint112,uint112)')
_, web3 = connect_to_web3()
apikey = "P6Z71M2VBHAHHBFMM91YT5YWENGJYTJT81"
tokens_and_pools = pd.read_csv("../data/SUSHISWAP/polygon_pools.csv", index_col='pair')
pools = tokens_and_pools.index.tolist()

contract = web3.eth.contract(shared.EXCHANGES['sushiswap'], abi=shared.ABI_POOL)
done_pools = [pool.split(".csv")[0] for pool in os.listdir("../data/SUSHISWAP/pool_sync_events")]

for i, pool in enumerate(pools):
    if pool in done_pools:
        continue
    response = [0] * 1000

    print(pool, i, len(pools))
    timestamps, block_numbers, reserves0, reserves1 = [], [], [], []
    from_block, first_timestamp, current_timestamp = 0, 0, 0
    cont = 0

    while len(response) >= 1000 and current_timestamp - first_timestamp < shared.WEEK:
        response = get_response(pool, from_block)
        if len(response) == 0:
            continue
        decoded_logs = clean_response(response)
        for k, log in enumerate(decoded_logs):
            block_numbers.append(log['blockNumber'])
            reserves0.append(log['args']["reserve0"])
            reserves1.append(log['args']["reserve1"])
            timestamps.append(int(response[k]["timeStamp"], 16))
        from_block = int(response[-1]['blockNumber'], 16) + 1
        current_timestamp = int(response[-1]['timeStamp'], 16)

    pd.DataFrame({'block_number': block_numbers, 'reseve0': reserves0 , 'reserve1': reserves1, 'timestamps': timestamps}).to_csv(
        f"../data/SUSHISWAP/pool_sync_events/{pool}.csv", index=False)

