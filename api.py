from flask import Flask, redirect, request
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import simpleobsws
import asyncio
import requests
import json
from config import (
    API_URL,
    API_PORT,
    MQTT_HOST,
    MQTT_PORT,
    MQTT_AUTH,
    OBS_HOST,
    OBS_PORT,
    OBS_PASSWORD,
    )

app = Flask(__name__)
loop = asyncio.get_event_loop()

obs = simpleobsws.obsws(host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD, loop=loop)

async def make_request(call, data=None):
    try:
        destination = data['ref']
    except KeyError:
        destination = None
    await obs.connect()
    result = await obs.call(call, data=data)
    await obs.disconnect()
    if destination:
        return redirect(destination)
    else:
        result["api_warning"] = "All API calls must contain a valid refferal."
        return result

def options_to_GET(options_list):
    output = ""
    for i in range(0, len(options_list)):
        output += options_list[i]
        if i != len(options_list) - 1:
            output += "&"
    return output

def convert_db_to_mul(decibels):
    db = decibels * -1
    perc_db = decibels / 60
    return 

def str_to_bool(target):
    if target.lower() in {'true', 'false'}:
        value = True if target.lower() == "true" else False
        return value
    else:
        return target

@app.route("/api/", methods=['GET'])
def api_call():
    # "volume=-19.3:float" or "source=Desktop Audio:str"
    data={}
    for key, value in request.values.items():
        if key not in {"call"}:
            try:
                if key not in {"ref"}:
                    splitvalue = value.split(":")
                    if splitvalue[1] == "bool":
                        data[key] = str_to_bool(splitvalue[0])
                    elif splitvalue[1] == "int":
                        data[key] = int(splitvalue[0])
                    elif splitvalue[1] == "float":
                        data[key] = float(splitvalue[0])
                    else:
                        data[key] = splitvalue[0]
                else:
                    data[key] = value
            except IndexError:
                data[key] = value
    if len(data.values()) == 0:
        return loop.run_until_complete(make_request(request.values["call"]))
    else:
        return loop.run_until_complete(make_request(request.values["call"], data=data))

@app.route('/api/sound')
def play_sound():
    has_name = False
    has_ref = False
    data, result = {}, {}
    for key, value in request.values.items():
        if key == "name":
            has_name = True
        if key == "ref":
            has_ref = True
        data[key] = value
    
    if has_name and has_ref:
        data['snd'] = request.values["name"]
        msg = json.dumps(data)
        publish.single(
            'buttonbox', 
            str(msg), 
            qos=0, 
            retain=False, 
            hostname=MQTT_HOST,
            port=MQTT_PORT, 
            client_id="", 
            keepalive=60,
            will=None,
            auth=MQTT_AUTH,
            tls=None,
            protocol=mqtt.MQTTv311,
            transport="tcp",
            )
        return redirect(data['ref'])
    elif has_name and not has_ref:
        data['snd'] = request.values["name"]
        msg = json.dumps(data)
        publish.single(
                'buttonbox', 
                str(msg), 
                qos=0, 
                retain=False, 
                hostname=MQTT_HOST,
                port=MQTT_PORT, 
                client_id="", 
                keepalive=60,
                will=None,
                auth=MQTT_AUTH,
                tls=None,
                protocol=mqtt.MQTTv311,
                transport="tcp",
                )
        result["api_error"] = "All API calls must contain a valid refferal."
        return result
    elif not has_name:
        result["api_error"] = "Sound API calls must have a sound name."
        return result
    else:
        result["api_error"] = "None of this working!"
        return result

@app.route('/api/test-volume')
def test_volume():
    return loop.run_until_complete(make_request('SetVolume', data={"source": "Desktop Audio", "volume": -19.3, "useDecibel": True}))

@app.route('/api/start-stream', methods=['GET', 'POST'])
def start_stream():
    # Things To Do:
    # Drop 'Desktop Audio' to -19DB
    options = [ 'call=SetVolume', 'source=Desktop Audio:str', 'useDecibel=true:bool', 'volume=-19.0:float' ]
    r = request.get(f"{API_URL}?{options_to_GET(options)}")
    # Set Mic/Aux -10Db
    # Unmute Mic/Aux
    # Switch to First Scene
