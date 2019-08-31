import datetime
import time
from threading import Thread
from flask import Flask, request, render_template
import json
import requests
import hashlib, uuid
from config import *
import threading
import csv
import json

headers = {
    "Content-Type": "text/json"
}

def get_types(token):
    url = "https://int.drugscreening.ru/v1/concepts/types?access_token={}".format(token)

    answer = requests.get(url, headers=headers)

    return answer.json()


def find_medicine(medicine_name, token):
    url = "https://int.drugscreening.ru/v1/concepts/find?q={}&type={}&searchBy={}&access_token={}".format(medicine_name,
                                                                                                          "DrugName",
                                                                                                          "Text", token)

    answer = requests.get(url, headers=headers)

    drug_list = answer.json()

    if not len(drug_list):
        return None
    else:
        return drug_list[0]


def find_interaction(medicines, token):
    url = "https://int.drugscreening.ru/v1/screening?access_token={}".format(token)

    params = {
        "ScreeningTypes": "DrugDrugInteractions",
        "Drugs": [
            {
                "Name": medicine['Name'],
                "Type": "DrugName",
                "Code": medicine['Code']
            } for medicine in medicines
        ],
    }

    answer = requests.post(url, headers=headers, json=params)
    return answer.json()


with open("clear_meds.txt", 'r') as f:
    names = f.read().split('\n')

app = Flask(__name__)


def delayed(delay, f, args):
    timer = threading.Timer(delay, f, args=args)
    timer.start()


@app.route('/init', methods=['POST', 'GET'])
def init():
    return 'ok'


@app.route('/remove', methods=['POST'])
def remove():
    return 'ok'


@app.route('/settings', methods=['GET'])
def settings():
    return "<strong>Данный интеллектуальный агент не требует настройки.</strong>"


@app.route('/', methods=['GET'])
def index():
    return 'waiting for the thunder!'


def send_warning(contract_id, names):
    data = {
        "contract_id": contract_id,
        "api_key": APP_KEY,
        "message": {
            "text": "Внимание!\n\nСледующие лекарственные препараты могут быть противопоказаны для беременных: {}.".format(
                ", ".join(names)),
            "is_urgent": True,
        }
    }
    try:
        print('sending warning')
        result = requests.post(MAIN_HOST + '/api/agents/message', json=data)
    except Exception as e:
        print('connection error', e)


@app.route('/message', methods=['POST'])
def save_message():
    data = request.json
    key = data['api_key']
    contract_id = str(data['contract_id'])

    if key != APP_KEY:
        return "<strong>Некорректный ключ доступа.</strong> Свяжитесь с технической поддержкой."

    text = data['message']['text'].replace('\n', ' ')

    medicines = []
    for name in names:
        if len(name) < 4:
            variants = [' ' + name + ' ', ' ' + name + '.', ' ' + name + '?', ' ' + name + '!', ' ' + name + '(']
        else:
            variants = [name]
        for variant in variants:
            if variant.lower() in (' ' + text + ' ').lower():
                medicines.append(name)
    print(medicines)
    found_meds = []
    for medicine in list(set(medicines)):
        found = find_medicine(medicine, element_token)
        if found:
            found_meds.append(found)

    print(find_interaction(found_meds, element_token))

    if warning:
        delayed(1, send_warning, [contract_id, list(set())])

    return "ok"


if not DEBUG:
    app.run(port='9094', host='0.0.0.0', ssl_context=SSL)
else:
    app.run(port='9094', host='0.0.0.0')
