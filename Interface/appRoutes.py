from flask import render_template, request
import logging
import random
import blockchain
import time
import fl

web3 = blockchain.blockchainConnect()
account = blockchain.unlockAccount()
contract = blockchain.instantiateContract()

def genContributions():
    learningExchanges = {}
    flNodes = fl.getFLNodes()

    for node in flNodes:
        nodeLE = node.learning_exchanges
        for exchange_id, contribution in nodeLE.items():
            learningExchanges[exchange_id] = {
                'node': node.name,
                'contribution': contribution
            }

    dataSharingAgreements = {}
    if hasattr(contract, 'dataSharingAgreements'):
        for agreement_id in range(len(contract.dataSharingAgreements)):
            agreement = contract.dataSharingAgreements[agreement_id]
            dataSharingAgreements[agreement_id] = {
                'agreementId': agreement.agreementId,
                'participants': agreement.participants,
                'terms': agreement.terms,
                'isActive': agreement.isActive
            }

    return render_template('contributions.html', learningExchanges=learningExchanges, dataSharingAgreements=dataSharingAgreements)


def initAgreement():    
    if request.method == 'POST':
        agreementID = int(request.form['agreement_id'])
        participant1 = request.form['participant1']
        participant2 = request.form['participant2']
        terms = request.form['terms']

        # Build the transaction dictionary
        transaction = {
            'from': account.address,
            'to': contract.address,
            'gas': 800000,  # Adjust the gas limit according to your requirements
            'nonce': web3.eth.get_transaction_count(account.address),
            'data': contract.encodeABI(fn_name='proposeTermsAndConditions', args=[agreementID, participant1, participant2, terms]),
            'gasPrice': web3.eth.gas_price,
            'chainId': web3.eth.chain_id
        }

        # Sign and send the transaction
        signedTxn = account.sign_transaction(transaction)

        try:
            # Wait for the transaction receipt
            txHash = web3.eth.send_raw_transaction(signedTxn.rawTransaction)
            txReceipt = web3.eth.wait_for_transaction_receipt(txHash)
            # Render the template to display the transaction receipt
            return render_template('tr2.html', txHash=txHash, txReceipt=txReceipt, agreementID=agreementID, participant1=participant1, participant2=participant2, terms=terms)
        except Exception as e:
            logging.error(str(e))
            # Transaction failed, handle the error or render an error template
            return render_template('error.html', message='Failed to create agreement.')

    # Handle GET request by rendering the createAgreement.html template
    else:
        return render_template('createAgreement.html')

    
def termUpdate():
    if request.method == 'POST':
        agreementID = int(request.form.get('agreement_id'))
        newTerms = request.form.get('new_terms')

        # Build the transaction dictionary
        transaction = {
            'from': account.address,
            'to': contract.address,
            'gas': 300000,  # Adjust the gas limit according to your requirements
            'nonce': web3.eth.get_transaction_count(account.address),
            'data': contract.encodeABI(fn_name='proposeTermUpdate', args=[agreementID, newTerms]),
            'gasPrice': web3.eth.gas_price,
            'chainId': web3.eth.chain_id
        }

        # Sign and send the transaction
        signedTxn = account.sign_transaction(transaction)

        try:
            # Wait for the transaction receipt
            txHash = web3.eth.send_raw_transaction(signedTxn.rawTransaction)
            txReceipt = web3.eth.wait_for_transaction_receipt(txHash)

            # Render the template to display the transaction receipt
            return render_template('tr3.html', txHash=txHash, txReceipt=txReceipt, agreementID=agreementID, newTerms=newTerms)
        except Exception as e:
            logging.error(str(e))
            # Transaction not found, handle the error or render an error template
            return render_template('error.html', message='Failed to update agreement terms.')

    # Handle GET request by rendering the updateTerms.html template
    return render_template('updateTerms.html')


def modelUpdate():
    if request.method == 'POST':
        modelUpdate = request.form['model_update']
        version = request.form['version']
        nodeID = request.form['node_id']

        for node in fl.flNodes:
            if node.id == nodeID:
                node.storeModelUpdate(modelUpdate, version)
                break
        else:
            return render_template('error.html', message='Invalid node ID.')

        # Build the transaction dictionary
        transaction = {
            'from': account.address,
            'gas': 300000,
            'nonce': web3.eth.get_transaction_count(account.address),
            'data': contract.encodeABI(fn_name='updateModel', args=[modelUpdate, int(version)]),
            'gasPrice': web3.eth.gas_price,
            'chainId': web3.eth.chain_id
        }

        # Sign and send the transaction
        signedTxn = account.sign_transaction(transaction)

        try:
            # Wait for the transaction receipt
            txHash = web3.eth.send_raw_transaction(signedTxn.rawTransaction)
            txReceipt = web3.eth.wait_for_transaction_receipt(txHash)

            # Get the updated node details
            updatedNode = None
            for node in fl.getFLNodes():
                if node.id == nodeID:
                    updatedNode = node
                    break

            return render_template('tr5.html', txHash=txHash.hex(), txReceipt=txReceipt, modelUpdate=modelUpdate, updatedNode = updatedNode)
        except Exception as e:
            logging.error(str(e))
            return render_template('error.html', message='Unable to update model.')
    else:
        return render_template('updateModel.html')
    
def exchangeRecords():
    if request.method == 'POST':
        useSyntheticData = request.form.get('synthetic_data') == 'on'

        if useSyntheticData:
            # Generate synthetic data
            exchangeID = random.randint(1, 100)
            contribution = random.randint(1, 1000)
        else:
            exchangeID = int(request.form.get('exchange_id'))
            contribution = int(request.form.get('contribution'))

        # Perform some validation on the input data
        if exchangeID < 0 or contribution < 0:
            return render_template('error.html', message='Invalid input.')

        # Locally record the learning exchange
        nodeAddress = account.address
        node = None
        aggregator = fl.getFLAggregator()

        # Check if the node exists in the FL nodes list
        for flNode in fl.getFLNodes():
            if flNode.id == nodeAddress:
                node = flNode
                break

        if node is None:
            # Create a new FLNode instance
            node = fl.FLNode(nodeAddress, 'Node', 1.0)
            fl.addFLNode(node)

        # Record the learning exchange locally in the node
        node.recordLearningExchange(exchangeID, contribution)

        numRuns = 10  # Number of runs for latency measurement
        totalLatency = 0
        totalThroughput = 0

        for _ in range(numRuns):
            # Measure the start time
            startTime = time.time()

            # Build the transaction dictionary
            transaction = {
                'from': account.address,
                'to': contract.address,
                'gas': 300000,  # Adjust the gas limit according to your requirements
                'nonce': web3.eth.get_transaction_count(account.address),
                'data': contract.encodeABI(fn_name='recordLearningExchange', args=[exchangeID, account.address, contribution]),
                'gasPrice': web3.eth.gas_price,
                'chainId': web3.eth.chain_id
            }

            try:
                # Sign and send the transaction
                signedTxn = account.sign_transaction(transaction)
                txHash = web3.eth.send_raw_transaction(signedTxn.rawTransaction)
                txReceipt = web3.eth.wait_for_transaction_receipt(txHash)

                # Measure the end time and calculate the latency for this run
                endTime = time.time()
                latency = endTime - startTime

                # Add the latency to the total
                totalLatency += latency

                # Calculate the throughput for this run
                throughput = 1 / latency

                # Add the throughput to the total
                totalThroughput += throughput

                # Render the template to display the transaction receipt with average latency and throughput
                return render_template('transactionReceipt.html', txHash=txHash, txReceipt=txReceipt, useSyntheticData=useSyntheticData, exchangeID=exchangeID, contribution=contribution, averageLatency=totalLatency / numRuns, throughput=totalThroughput / numRuns)
            except Exception as e:
                logging.error(str(e))
                # Transaction not found, handle the error or render an error template
                return render_template('error.html', message='Exchange was not recorded.')

        # The loop completes without returning, meaning all transactions failed
        # Render the template to display an error message or redirect to an error page
        return render_template('error.html', message='All exchange transactions failed.')

    return render_template('recordExchange.html')


def agreementTerminated():
    if request.method =='POST':
        agreementID = int(request.form['agreement_id'])

        # Build the transaction dictionary
        transaction = {
            'from': account.address,
            'to': contract.address,
            'gas': 500000,  # Adjust the gas limit according to your requirements
            'nonce': web3.eth.get_transaction_count(account.address),
            'data': contract.encodeABI(fn_name='proposeTermination', args=[agreementID]),
            'gasPrice': web3.eth.gas_price,
            'chainId': web3.eth.chain_id
        }

        # Sign and send the transaction
        signed_txn = account.sign_transaction(transaction)

        try:
            # Wait for the transaction receipt
            txHash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            txReceipt = web3.eth.wait_for_transaction_receipt(txHash)
            
            return render_template('tr4.html', txHash=txHash.hex(), txReceipt=txReceipt, agreementID=agreementID)
        except Exception as e:
            logging.error(str(e))
            return render_template('error.html', message='Error terminating agreement.')

    else:
        return render_template('terminateAgreement.html')
    
