from flask import Flask, redirect, request
from flask_cors import cross_origin
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import paho.mqtt.subscribe as subscribe
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
    except (KeyError, TypeError):
        destination = None
    await obs.connect()
    result = await obs.call(call, data=data)
    await obs.disconnect()
    if destination:
        return redirect(destination)
    else:
        result["api_warning"] = "All API calls must contain a valid refferal."
        return result

def automation_start_stream():
    data_list = [
        {"source":"Mic/Aux", "mute": True},
        None,
        {"source":"Desktop Audio", "volume":-9, "useDecibel": True},
        {'scene-name': 'Starting Soon'},
    ]

    call_list = [
        "SetMute",
        "StartStreaming",
        "SetVolume",
        "SetCurrentScene",
    ]

    for n in range(0, len(data_list)):
        loop.run_until_complete(make_request(call_list[n], data=data_list[n]))

def automation_start_countdown(time=300):
    publish.single(
                'countdown', 
                str(time),
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
    loop.run_until_complete(make_request("SetCurrentScene", data={'scene-name': 'Countdown'}))

def automation_on_camera():
    data_list = [
        {"source":"Mic/Aux", "mute": False},
        {"source":"Desktop Audio", "volume":-19, "useDecibel": True},
        {'scene-name': 'Left Monitor w/ Lower-Left Camera'},
    ]

    call_list = [
        "SetMute",
        "SetVolume",
        "SetCurrentScene",
    ]

    for n in range(0, len(data_list)):
        loop.run_until_complete(make_request(call_list[n], data=data_list[n]))

def automation_on_camera():
    data_list = [
        {"source":"Mic/Aux", "mute": False},
        {"source":"Desktop Audio", "volume":-19, "useDecibel": True},
        {'scene-name': 'Left Monitor w/ Lower-Left Camera'},
    ]

    call_list = [
        "SetMute",
        "SetVolume",
        "SetCurrentScene",
    ]

    for n in range(0, len(data_list)):
        loop.run_until_complete(make_request(call_list[n], data=data_list[n]))

def automation_outro():
    data_list = [
        {"source":"Mic/Aux", "mute": True},
        {"source":"Desktop Audio", "volume":-9, "useDecibel": True},
        {'scene-name': 'Outro'},
    ]

    call_list = [
        "SetMute",
        "SetVolume",
        "SetCurrentScene",
    ]

    for n in range(0, len(data_list)):
        loop.run_until_complete(make_request(call_list[n], data=data_list[n]))

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

@app.route('/api/sounds-available')
@cross_origin()
def sound_available():
    sounds_available = subscribe.simple(
        'buttonbox-sounds', 
        qos=0, 
        msg_count=1, 
        retained=True, 
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
    return json.dumps(sounds_available.payload.decode('utf-8'))

@app.route('/api/countdown')
def start_countdown():
    has_time = False
    has_ref = False
    data, result = {}, {}
    for key, value in request.values.items():
        if key == "time":
            has_time = True
        if key == "ref":
            has_ref = True
        data[key] = value
    
    if has_time and has_ref:
        try:
            countdown = int(request.values["time"])
            publish.single(
                'countdown', 
                str(countdown), 
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
            return redirect(data["ref"])
        except ValueError:
            result['api_error'] = "API must receive a number for time."
            return result
    elif has_time and not has_ref:
        try:
            countdown = int(request.values["time"])
            publish.single(
                    'countdown', 
                    countdown, 
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
        except ValueError:
            result['api_error'] = "API must receive a number for time. All API calls must contain a valid refferal."
        return result
    elif not has_time:
        result["api_error"] = "Countdown API calls must have a number to count down from..."
        return result
    else:
        result["api_error"] = "None of this working!"
        return result
    return redirect(data["ref"])


    # Things To Do:
    # Drop 'Desktop Audio' to -19DB
    options = [ 'call=SetVolume', 'source=Desktop Audio:str', 'useDecibel=true:bool', 'volume=-19.0:float' ]
    r = request.get(f"{API_URL}?{options_to_GET(options)}")
    # Set Mic/Aux -10Db
    # Unmute Mic/Aux
    # Switch to First Scene

@app.route('/api/automation')
def trigger_automation():
    has_trigger = False
    has_ref = False
    data, result = {}, {}
    for key, value in request.values.items():
        if key == "trigger":
            has_trigger = True
        if key == "ref":
            has_ref = True
        data[key] = value
    if has_trigger and has_ref:
        if data["trigger"] == "startstream":
            automation_start_stream()
        if data["trigger"] == "startcountdown":
            if "time" in data.keys():
                try:
                    automation_start_countdown(int(data["time"]))
                except:
                    automation_start_countdown()    
            else:
                automation_start_countdown()
        if data["trigger"] == "gooncamera":
            automation_on_camera()
        if data["trigger"] == "start-outro":
            automation_outro()
        return redirect(data["ref"])
    elif has_trigger and not has_ref:
        if data["trigger"] == "startstream":
            automation_start_stream()
        if data["trigger"] == "startcountdown":
            if "time" in data.keys():
                try:
                    automation_start_countdown(int(data["time"]))
                except:
                    automation_start_countdown()    
            else:
                automation_start_countdown()
        if data["trigger"] == "gooncamera":
            automation_on_camera
        if data["trigger"] == "start-outro":
            automation_outro
        return result
    elif not has_trigger:
        result["api_error"] = "Automation API calls must have a valid automation."
        return result
    else:
        result["api_error"] = "None of this working!"
        return result
    return redirect(data["ref"])
