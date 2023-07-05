from web3 import Web3
import json

def initializeConnection():
    web3 = Web3(Web3.HTTPProvider('https://proud-purple-star.ethereum-goerli.discover.quiknode.pro/e4cdebf9ad1c695a5e66d0245f402919b6e9b590/'))
    
    if web3.is_connected():
        print("Connection successful")
    else:
        print("Connection failed")
        return None
    
    return web3

def extractData():
    with open('./SmartContracts/contractData.json', 'r') as contractFile:
        contractData = json.load(contractFile)

    if isinstance(contractData, list) and len(contractData) > 0:
        data = contractData[0]
        if 'abi' in data and 'bytecode' in data:
            abiData = data['abi']
            bytecodeData = data['bytecode']
        else:
            abiData = None
            bytecodeData = None
            print("Invalid contract data: 'abi' or 'bytecode' field is missing")
            return None, None
    else:
        print("Invalid contract data: Expected a list containing contract data")
        return None, None

    return abiData, bytecodeData

def deployContract():
    web3 = initializeConnection()
    if web3 is None:
        return None

    abiData, bytecodeData = extractData()
    if abiData is None or bytecodeData is None:
        return None

    defaultAccount = '0x21efAAea8ADFA4fBF5b8d5A827C0EF237b6cb645'
    privateKey = 'b437656a5b100e130bda1bae90ed44b1048307edfeb27fde9a4d0b156d822b0b'

    web3.eth.default_account = defaultAccount
    account = web3.eth.account.from_key(privateKey)
    nonce = web3.eth.get_transaction_count(account.address)
    chainID = web3.eth.chain_id
    gasPrice = web3.eth.gas_price

    transaction = {
        'chainId': chainID,
        'from': account.address,
        'gas': 700000,
        'gasPrice': gasPrice,
        'nonce': nonce,
        'data': bytecodeData
    }
    signedTransaction = account.sign_transaction(transaction)
    txHash = web3.eth.send_raw_transaction(signedTransaction.rawTransaction)
    txReceipt = web3.eth.wait_for_transaction_receipt(txHash)

    deployedContractAddress = txReceipt['contractAddress']

    return deployedContractAddress


deployedAddress = deployContract()
if deployedAddress is not None:
    print("Contract deployed successfully. Address:", deployedAddress)
else:
    print("Contract deployment failed.")
