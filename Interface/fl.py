from flask import render_template, request, redirect, url_for
import numpy as np
from sklearn.preprocessing import StandardScaler
import logging
import binascii
import verification
import blockchain
import ast
import time

web3 = blockchain.blockchainConnect()
account = blockchain.unlockAccount()
contract = blockchain.instantiateContract()

class FLNode:
    def __init__(self, id, name, weight):
        self.id = id
        self.name = name
        self.weight = weight
        self.model_updates = []
        self.learning_exchanges = {}  

    def storeModelUpdate(self, model_update, version):
        # Store the model update in the node's storage
        self.model_updates.append((model_update, version))

    def recordLearningExchange(self, exchange_id, contribution):
        # Record the learning exchange locally
        self.learning_exchanges[exchange_id] = contribution

class FLAggregator:
    def __init__(self, name, weight):
        self.name = name
        self.weight = weight
        self.model_updates = []

    def storeModelUpdate(self, model_update, version):
        # Store the model update in the aggregator's storage
        self.model_updates.append((model_update, version))

# List to store FL Nodes
flNodes = []
flAggregator = None

def addFLNode(node):
    flNodes.append(node)

def getFLNodes():
    return flNodes

def setFLAggregator(aggregator):
    global flAggregator
    flAggregator = aggregator

def getFLAggregator():
    return flAggregator

def clearFLNodes():
    global flNodes
    flNodes = []

def clearFLAggregator():
    global flAggregator
    flAggregator = None
    return True

#Dummy FL Operations
def generateSynData():
    # Generate synthetic data
    data = np.random.rand(100, 10)  # Example: Generating 100 samples with 10 features
    return data

def preprocessData(data):
    # Preprocess the data
    # Standardize the data
    scaler = StandardScaler()
    standardizedData = scaler.fit_transform(data)

    return standardizedData

def makePredictions(data):
    # Make predictions using the data
    predictions = np.sum(data, axis=1)  # Example: Summing the values along each row
    return predictions

def aggregateModelUpdates(aggregator):
    if aggregator is None:
        return None

    # Retrieve the model updates from the aggregator
    modelUpdates = aggregator.model_updates

    # Check if any model updates are available
    if not modelUpdates:
        return None

    # Aggregate the model updates
    aggregatedModel = [0.0] * len(modelUpdates[0][0])  # Initialize with zeros

    for update in modelUpdates:
        modelData, _ = update
        for i in range(len(aggregatedModel)):
            aggregatedModel[i] += modelData[i]

    # Average the aggregated model by dividing by the number of updates
    numUpdates = len(modelUpdates)
    aggregatedModel = [value / numUpdates for value in aggregatedModel]

    # Store the aggregated model in the aggregator
    aggregator.storeModelUpdate(aggregatedModel, version=numUpdates + 1)

    return aggregatedModel



def measureLatency():
    numRuns = 10  # Number of runs for latency measurement
    totalLatency = 0

    for _ in range(numRuns):
        # Record the start timestamp
        startTime = time.time()

        flAggregator = getFLAggregator()
        # Perform the model aggregation process
        aggregatedModel = aggregateModelUpdates(flAggregator)

        # Record the end timestamp
        endTime = time.time()

        # Calculate the latency for this run
        latency = endTime - startTime

        # Add the latency to the total
        totalLatency += latency

    # Calculate the average latency
    averageLatency = totalLatency / numRuns

    return averageLatency

def measureThroughput():
    numRuns = 10  # Number of runs for throughput measurement
    totalOperations = 0
    totalTime = 0

    for _ in range(numRuns):
        # Record the start timestamp
        startTime = time.time()

        fl_aggregator = getFLAggregator()
        # Perform the model aggregation process
        aggregateModelUpdates(fl_aggregator)

        # Record the end timestamp
        endTime = time.time()

        # Calculate the time taken for this run
        timeTaken = endTime - startTime

        # Count the number of operations completed in this run
        operationsCompleted = 1  # Update this based on the actual number of operations in the aggregation process

        # Add the operations and time to the total
        totalOperations += operationsCompleted
        totalTime += timeTaken

    # Calculate the average time taken per operation
    averageTimePerOperation = totalTime / totalOperations

    # Calculate the throughput (operations per unit of time)
    throughput = 1 / averageTimePerOperation  # Inverse of average time per operation

    return throughput

def submitNodes():
    if request.method == 'POST':
        if 'submit' in request.form:
            # Done Submitting Nodes button clicked
            return redirect(url_for('home'))
        elif 'add_node' in request.form:
            if 'node_id' in request.form and 'node_name' in request.form and 'node_weight' in request.form:
                # FL Node form submission
                node_id = request.form.get('node_id')
                node_name = request.form.get('node_name')
                node_weight = request.form.get('node_weight')

                # Create FL Node instance with the provided data
                fl_node = FLNode(node_id, node_name, node_weight)

                # Add the FL Node to the list of FL Nodes
                addFLNode(fl_node)
        elif 'add_aggregator' in request.form:
            if 'aggregator_name' in request.form and 'aggregator_weight' in request.form:
                # FL Aggregator form submission
                aggregator_name = request.form.get('aggregator_name')
                aggregator_weight = request.form.get('aggregator_weight')

                # Create FL Aggregator instance with the provided data
                fl_aggregator = FLAggregator(aggregator_name, aggregator_weight)

                # Set the FL Aggregator
                setFLAggregator(fl_aggregator)
        elif 'clear_nodes' in request.form:
            # Clear Nodes button clicked
            clearFLNodes()
        elif 'clear_aggregator' in request.form:
            # Clear Aggregator button clicked
            clearFLAggregator()

    fl_nodes = getFLNodes()  # Get FL Nodes
    fl_aggregator = getFLAggregator()  # Get FL Aggregator

    return render_template('flNodes.html', fl_nodes=fl_nodes, fl_aggregator=fl_aggregator)

def getFLParameters():
    flAggregator = getFLAggregator()
    aggregatedModel = None

    if flAggregator:
        aggregatedModel = aggregateModelUpdates(flAggregator)
        if not aggregatedModel:
            aggregatedModel = None

    return render_template('flNodes2.html', flNodes=getFLNodes(), flAggregator=flAggregator, aggregatedModel=aggregatedModel)


def initFL():
    # Get FL nodes and aggregator data from the contract or data source
    flNodes = getFLNodes()
    flAggregator = getFLAggregator()

    if flNodes is None or flAggregator is None:
        return render_template('initFL2.html', flNodes=[], flAggregator=None)

    # Build the transaction dictionary
    transaction = {
        'from': account.address,
        'gas': 500000,
        'nonce': web3.eth.get_transaction_count(account.address),
        'to': contract.address,
        'gasPrice': web3.eth.gas_price,
        'chainId': web3.eth.chain_id
    }

    # Sign and send the transaction
    signedTxn = account.sign_transaction(transaction)

    try:
        # Send the signed transaction
        txHash = web3.eth.send_raw_transaction(signedTxn.rawTransaction)
        txReceipt = web3.eth.wait_for_transaction_receipt(txHash)

        # Get nodes' data and aggregator data
        nodeData = [{'id': node.id, 'name': node.name, 'weight': node.weight} for node in flNodes]
        aggregatorData = {'name': flAggregator.name, 'weight': flAggregator.weight}

        return render_template('initFL2.html', txHash=txHash.hex(), txReceipt=txReceipt,
                               flNodes=nodeData, flAggregator=aggregatorData)
    except Exception as e:
        logging.error(str(e))
        return render_template('error.html', error_message='Unable to initialize Federated Learning!')


def beginTraining():
    if request.method == 'POST':
        numRuns = 10  # Number of runs for latency measurement
        totalLatency = 0

        for _ in range(numRuns):
            # Record the start timestamp
            startTime = time.time()

            newModelVersion = int(request.form['new_model_version'])
            nodeID = request.form['node_id']

            # Perform data compliance check
            if not verification.verifyTool(newModelVersion):
                return render_template('error.html', message='Data does not comply with the defined policies.')

            # Load the initial model from the selected node
            flNodes = getFLNodes()
            currentNode = None
            for node in flNodes:
                if node.id == nodeID:
                    currentNode = node
                    break

            if currentNode is None:
                return render_template('error.html', message='Invalid node ID.')
            

            modelWeights = ast.literal_eval(currentNode.model_updates[-1][0]) if currentNode.model_updates else [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]

            # Perform minimal training on the model
            for i in range(len(modelWeights)):
                modelWeights[i] = str(float(modelWeights[i]) + 0.1)

            # Update the model_updates list with the new model weights
            currentNode.model_updates.append((modelWeights, newModelVersion))
            updatedModelWeights = modelWeights

            # Build the transaction dictionary
            transaction = {
                'from': account.address,
                'gas': 300000,
                'nonce': web3.eth.get_transaction_count(account.address),
                'gasPrice': web3.eth.gas_price,
                'chainId': web3.eth.chain_id
            }

            initializeData = contract.encodeABI(fn_name='initializeFL')
            startRoundData = contract.encodeABI(fn_name='startTrainingRound', args=[newModelVersion])

            transaction_data = initializeData + startRoundData
            transaction['data'] = '0x' + binascii.hexlify(transaction_data.encode()).decode('utf-8')

            # Sign and send the transaction
            signedTxn = account.sign_transaction(transaction)

            try:
                # Wait for the transaction receipt
                txHash = web3.eth.send_raw_transaction(signedTxn.rawTransaction)
                txReceipt = web3.eth.wait_for_transaction_receipt(txHash)

                # Record the end timestamp
                endTime = time.time()

                # Calculate the latency for this run
                latency = endTime - startTime


                # Calculate the throughput for this run
                throughput = 1 / latency

                totalLatency += latency

                averageLatency = totalLatency / numRuns


                # Retrieve the updated model metadata
                modelMetadata = contract.functions.getModelMetadata().call()
                currentModelVersion = modelMetadata[0]  # Access the first element of the tuple
                currentModelWeights = modelMetadata[1]  # Access the second element of the tuple

                flNodes = getFLNodes()
                flAggregator = getFLAggregator()

                return render_template('tr6.html',
                                       averageLatency = averageLatency,
                                       throughput=throughput,
                                       txHash=txHash.hex(),
                                       txReceipt=txReceipt,
                                       newModelVersion=newModelVersion,
                                       currentModelVersion=currentModelVersion,
                                       currentModelWeights=currentModelWeights,
                                       flNodes=flNodes,
                                       flAggregator=flAggregator, 
                                       updatedModelWeights=updatedModelWeights)
            except Exception as e:
                logging.error(str(e))
                return render_template('error.html', message='Unable to start the training round.')
    else:
        return render_template('startFL.html')


def getTraining():
    # Retrieve the training round
    trainingRound = contract.functions.getTrainingRound().call()

    # Retrieve the model metadata
    modelMetadata = contract.functions.getModelMetadata().call()
    if isinstance(modelMetadata, tuple):
        # Handle the case where model_metadata is a tuple
        modelMetadata = {
            'version': modelMetadata[0],
            'weights': modelMetadata[1]
        }
    elif isinstance(modelMetadata, list):
        # Handle the case where model_metadata is a list
        modelMetadata = {
            'version': modelMetadata[0],
            'weights': modelMetadata[1]
        }
    currentModelVersion = modelMetadata['version']
    currentModelWeights = modelMetadata['weights']

    # Perform data compliance check
    if not verification.verifyTool(currentModelVersion):
        return render_template('error.html', message='Data does not comply with the defined policies.')

    # Perform operations on the synthetic data
    synthetic_data = generateSynData()
    processed_data = preprocessData(synthetic_data)
    predictions = makePredictions(processed_data)

    # Perform some calculations on the predictions
    averagePrediction = sum(predictions) / len(predictions)
    maxPrediction = max(predictions)
    minPrediction = min(predictions)

    # Convert the weights data from a list of strings to a single string
    currentModelWeights = ' '.join(currentModelWeights)

    # Get the FL nodes and aggregator
    flNodes = getFLNodes()
    flAggregator = getFLAggregator()

    return render_template('getTraining.html',
                           trainingRound=trainingRound,
                           currentModelVersion=currentModelVersion,
                           currentModelWeights=currentModelWeights,
                           averagePrediction=averagePrediction,
                           maxPrediction=maxPrediction,
                           minPrediction=minPrediction,
                           flNodes=flNodes,
                           flAggregator=flAggregator)

    

def aggregateFL():
    # Measure the latency using the measureLatency() function
    latency = measureLatency()

    # Retrieve the FL aggregator
    flAggregator = getFLAggregator()

    # Update the aggregator with two model updates
    model_update1 = [0.1, 0.2, 0.3]
    version1 = 1
    model_update2 = [0.4, 0.5, 0.6]
    version2 = 2

    flAggregator.storeModelUpdate(model_update1, version1)
    flAggregator.storeModelUpdate(model_update2, version2)

    if flAggregator:
        # Aggregate model updates from participating devices
        aggregatedModel = aggregateModelUpdates(flAggregator)

        # Store the aggregated model in the aggregator
        flAggregator.storeModelUpdate(aggregatedModel, version2 + 1)  # Use the next version number

    # Measure the throughput using the measureThroughput() function
    throughput = measureThroughput()

    # Convert the aggregated model to a string
    aggregatedModelString = ','.join(map(str, aggregatedModel))

    # Build the transaction dictionary
    transaction = {
        'from': account.address,
        'gas': 300000,
        'nonce': web3.eth.get_transaction_count(account.address),
        'gasPrice': web3.eth.gas_price,
        'chainId': web3.eth.chain_id
    }

    # Encode the aggregated model data as transaction data
    transactionData = contract.encodeABI(fn_name='aggregateModel', args=[aggregatedModelString])
    transaction['data'] = '0x' + binascii.hexlify(transactionData.encode()).decode('utf-8')

    # Sign and send the transaction
    signedTxn = account.sign_transaction(transaction)

    try:
        # Wait for the transaction receipt
        txHash = web3.eth.send_raw_transaction(signedTxn.rawTransaction)
        txReceipt = web3.eth.wait_for_transaction_receipt(txHash)

        # Render the template with the aggregated model data, latency, throughput, and transaction information
        return render_template('aggregateFL.html', aggregatedModel=aggregatedModel, latency=latency, throughput=throughput, txHash=txHash.hex(), txReceipt=txReceipt)
    except Exception as e:
        logging.error(str(e))
        return render_template('error.html', message='Unable to aggregate model updates and transact with the blockchain.')

    
def endTraining():
    if request.method == 'POST':
        # Build the transaction dictionary
        transaction = {
            'from': account.address,
            'gas': 300000,
            'nonce': web3.eth.get_transaction_count(account.address),
            'data': contract.encodeABI(fn_name='stopTrainingRound'),
            'gasPrice': web3.eth.gas_price,
            'chainId': web3.eth.chain_id
        }

        # Sign and send the transaction
        signedTxn = account.sign_transaction(transaction)

        try:
            # Wait for the transaction receipt
            txHash = web3.eth.send_raw_transaction(signedTxn.rawTransaction)
            txReceipt = web3.eth.wait_for_transaction_receipt(txHash)

            return render_template('stopFl.html', txHash=txHash.hex(), txReceipt=txReceipt)
        except Exception as e:
            logging.error(str(e))
            return render_template('error.html', message='Unable to stop the training round')
    else:
        return render_template('stopFL.html')
