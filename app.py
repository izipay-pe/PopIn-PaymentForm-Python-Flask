from flask import Flask, request, render_template, redirect, url_for, json
from datetime import datetime
import base64
import requests
import json
import hmac
import hashlib
from key import credentials

app = Flask(__name__)


@app.get('/')
def index():
    order = datetime.now().strftime("Order-%Y%m%d%H%M%S")
    args = request.args
    return render_template('home.html', data={"order": order})


@app.post('/formulario')
def formulario():
    username = credentials["USERNAME"]
    password = credentials["PASSWORD"]
    publickey = credentials['PUBLIC_KEY']

    url = 'https://api.micuentaweb.pe/api-payment/V4/Charge/CreatePayment'
    auth = 'Basic ' + base64.b64encode(f"{username}:{password}".encode('utf-8')).decode('utf-8')

    data = {
        "amount": int(request.form["amount"]) * 100,
        "currency": "PEN",
        "customer": {
            "email": request.form["email"],
            "billingDetails": {
                "firstName": request.form["firstname"],
                "lastName": request.form["lastname"]
            }
        },
        "orderId": request.form["order"]
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': auth,
    }

    response = requests.post(url, json=data, headers=headers)
    response_data = response.json()

    if response_data['status'] == 'SUCCESS':
        formToken = response_data['answer']['formToken']
        return render_template("formToken.html", data={"formToken": formToken, "public_key": publickey})
    else:
        serialized_data = json.dumps(response_data, indent=4)
        return render_template('error.html', data={'serialized_data': serialized_data})


@app.post('/resultado')
def paidResult():
    answer = request.form.get('kr-answer')
    hash = request.form.get('kr-hash')

    hash_object = hmac.new(credentials['HMACSHA256'].encode('utf-8'), answer.encode('utf-8'), hashlib.sha256)
    answerHash = hash_object.hexdigest()

    answer_json = json.loads(answer)
    orderDetails = answer_json.get('orderDetails')

    if hash == answerHash:
        return render_template('result.html', data={'response': answer_json.get('orderStatus'), 'orderTotalAmount': orderDetails.get('orderTotalAmount'), 'orderId': orderDetails.get('orderId')})
    else:
        return render_template('result.html', data={'response': 'Error en el pago'})


@app.post('/ipn')
def ipn():
    answer = request.form.get('kr-answer')
    hash = request.form.get('kr-hash')

    hash_object = hmac.new(credentials['PASSWORD'].encode('utf-8'), answer.encode('utf-8'), hashlib.sha256)
    answerHash = hash_object.hexdigest()

    answer_json = json.loads(answer)
    print('IPN')
    print(answer_json)
    print('Codigo Hash: ' + answerHash)

    if hash == answerHash:
        return 'Correcto', 200
    else:
        return 'Acceso denegado', 500


if __name__ == '__main__':
    app.run(debug=True)
