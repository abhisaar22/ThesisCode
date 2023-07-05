from flask import Flask, render_template, redirect, url_for
import appRoutes
import fl

app = Flask(__name__)

@app.route('/index', methods=['GET', 'POST'])
def home():
    return render_template('index.html')

@app.route('/contributions')
def contributions():
    return appRoutes.genContributions()

@app.route('/createAgreement', methods=['GET', 'POST'])
def createAgreement():
    return appRoutes.initAgreement()

@app.route('/updateTerms', methods=['GET', 'POST'])
def updateAgreementTerms():
    return appRoutes.termUpdate()

@app.route('/updateModel', methods=['GET', 'POST'])
def updateModel():
    return appRoutes.modelUpdate()

@app.route('/recordExchange', methods=['GET', 'POST'])
def recordExchange():
    return appRoutes.exchangeRecords()
    
@app.route('/terminateAgreement', methods=['GET', 'POST'])
def terminateAgreement():
    return appRoutes.agreementTerminated()

@app.route('/initFL', methods=['GET', 'POST'])
def initFL():
    return fl.initFL()        

@app.route('/flNodes')
def flNodes():
    return render_template('flNodes.html', fl_nodes=fl.getFLNodes(), fl_aggregator=fl.getFLAggregator())

@app.route('/', methods=['GET', 'POST'])
def submitNodes():
    return fl.submitNodes()

@app.route('/clearAggregator', methods=['POST'])
def clearAggregator():
    fl.clearFLAggregator()
    return redirect(url_for('clear_nodes'))
    
@app.route('/clearNodes', methods=['GET','POST'])
def clearNodes():
    fl.clearFLNodes()
    return redirect(url_for('fl_nodes'))

@app.route('/startFL', methods=['GET','POST'])
def startFL():
    return fl.beginTraining()

@app.route('/aggregateFL', methods=['GET','POST'])
def aggregateUpdates():
    return fl.aggregateFL()

@app.route('/parametersFL', methods=['GET', 'POST'])
def executeParams():
    return fl.getFLParameters()

@app.route('/getTraining')
def getTrainingRound():
    return fl.getTraining()

@app.route('/stopFL', methods=['POST'])
def stopFL():
    return fl.endTraining()

if __name__ == '__main__':
    app.run(debug=True)
