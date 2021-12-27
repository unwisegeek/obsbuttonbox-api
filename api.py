from flask import Flask, redirect, request, Response
from flask_cors import cross_origin
from string import Template
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import paho.mqtt.subscribe as subscribe
import simpleobsws
import asyncio
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
from templates import (
    scrollbar_template
)

BADREQ = Response(status=400)
GOODREQ = Response(status=200)
TEAPOTREQ = Response(status=418)
# BADREQ = 400
# GOODREQ = 200
# TEAPOTREQ = 418

app = Flask(__name__)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

obs = simpleobsws.obsws(host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD, loop=loop)

async def make_request(call, data=None):
    try:
        destination = data['ref']
    except (KeyError, TypeError):
        destination = None
    await obs.connect()
    result = await obs.call(call, data=data)
    await obs.disconnect()
    return result

def automation_start_stream():
    data_list = [
        {"source":"Mic/Aux", "mute": True},
        None,
        {"source":"Desktop Audio", "volume":-9, "useDecibel": True},
        {"source":"Mic/Aux", "volume":-7.1, "useDecibel": True},
        {'scene-name': 'Starting Soon'},
    ]

    call_list = [
        "SetMute",
        "StartStreaming",
        "SetVolume",
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
        {"source":"Desktop Audio", "volume":-25.2, "useDecibel": True},
        {"source":"Mic/Aux", "volume":-7.1, "useDecibel": True},
        {'scene-name': 'Main'},
    ]

    call_list = [
        "SetMute",
        "SetVolume",
        "SetVolume",
        "SetCurrentScene",
    ]

    for n in range(0, len(data_list)):
        loop.run_until_complete(make_request(call_list[n], data=data_list[n]))

def automation_stir_browser():
    data_list = [
        {'scene-name': 'Main'},
        {'scene-name': 'Main 2'},
        {'scene-name': 'Main'},
    ]

    call_list = [
        "SetCurrentScene",
        "SetCurrentScene",
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

def str_to_bool(target):
    if target.lower() in {'true', 'false'}:
        value = True if target.lower() == "true" else False
        return value
    else:
        return target

@app.route("/api/", methods=['GET'])
@cross_origin()
def api_call():
    # "volume=-19.3:float" or "source=Desktop Audio:str"
    data={}
    for key, value in request.values.items():
        if key not in {"call"}:
            try:
                splitvalue = value.split(":")
                if splitvalue[1] == "bool":
                    data[key] = str_to_bool(splitvalue[0])
                elif splitvalue[1] == "int":
                    data[key] = int(splitvalue[0])
                elif splitvalue[1] == "float":
                    data[key] = float(splitvalue[0])
                else:
                    data[key] = splitvalue[0]
            except IndexError:
                data[key] = value
        else:
            data[key] = value
    if len(data.values()) == 0:
        return loop.run_until_complete(make_request(request.values["call"]))
    else:
        return loop.run_until_complete(make_request(request.values["call"], data=data))

@app.route('/api/sound')
def play_sound():
    has_name = False
    data, result = {}, {}
    for key, value in request.values.items():
        if key == "name":
            has_name = True
        data[key] = value
    
    if has_name:
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
        return GOODREQ
    elif not has_name:
        return BADREQ
    else:
        return BADREQ

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
    data, result = {}, {}
    for key, value in request.values.items():
        if key == "time":
            has_time = True
        data[key] = value
    
    if has_time:
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
            return GOODREQ
        except ValueError:
            result['api_error'] = "API must receive a number for time."
            return BADREQ
    elif not has_time:
        return BADREQ
    else:
        result["api_error"] = "None of this working!"
        return BADREQ

AUTOMATION_LIST = [
                    "Start Stream:startstream",
                    "Countdown - 1m:startcountdown&time=60",
                    "Countdown - 2m:startcountdown&time=120",
                    "Countdown - 5m:startcountdown&time=300",
                    "Countdown - 10m:startcountdown&time=600",
                    "Go On Camera:gooncamera",
                    "Outro:start-outro",
                    ]

@app.route('/api/automation/triggers')
@cross_origin()
def automation_trigger_list():
    response = ""
    for i in range(0, len(AUTOMATION_LIST)):
        response += AUTOMATION_LIST[i] if i == (len(AUTOMATION_LIST) - 1) else f"{AUTOMATION_LIST[i]},"
    return json.dumps(response)

@app.route('/api/automation')
def trigger_automation():
    has_trigger = False
    data, result = {}, {}
    for key, value in request.values.items():
        if key == "trigger":
            has_trigger = True
        data[key] = value
    if has_trigger:
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
        return GOODREQ
    elif not has_trigger:
        return BADREQ
    else:
        return BADREQ

@app.route('/api/healthcheck')
@cross_origin()
def health_check():
    return "true"

@app.route('/api/getsoundsources')
@cross_origin()
def getsoundsources():
    res = loop.run_until_complete(make_request("GetSourcesList"))
    source_list = {}
    source_list["sources"] = {}
    counter = 0
    for i in range(0, len(res["sources"])):
        if res["sources"][i]["typeId"] in ("pulse_input_capture", "pulse_output_capture"):
            source = loop.run_until_complete(
                make_request("GetVolume", data={'source': res["sources"][i]["name"], 'useDecibel': True})
            )
            source_list["sources"][counter] = { 
                'muted': source["muted"],
                'name': source["name"],
                'status': source["status"],
                'volume': round(source["volume"], 1)
            }
            counter += 1
    return source_list

@app.route('/api/refresh_soundboard')
@cross_origin()
def refresh_soundboard():
    has_name = False
    data, result = {}, {}
    for key, value in request.values.items():
        if key == "name":
            has_name = True
        data[key] = value
    
    if has_name:
        data['refresh'] = True
        msg = json.dumps(data)
        publish.single(
            'buttonbox', 
            str(msg), 
            qos=0, 
            retain=False, 
            hostname=MQTT_HOST,
            port=MQTT_PORT, 
            client_id="", 
            keepalive=1,
            will=None,
            auth=MQTT_AUTH,
            tls=None,
            protocol=mqtt.MQTTv311,
            transport="tcp",
            )
    return GOODREQ

@app.route('/api/scrollbar')
@cross_origin()
def render_scrollbar():
    msg = json.dumps(subscribe.simple(
        'scrollbarline1', 
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
        ).payload.decode('utf-8')).strip('"')
    msg2 = json.dumps(subscribe.simple(
        'scrollbarline2', 
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
        ).payload.decode('utf-8')).strip('"')
    page = scrollbar_template.safe_substitute(line1=msg, line2=msg2)
    return str(page)

@app.route('/api/setscrollbar')
@cross_origin()
def set_scrollbar():
    # if (has_line and has_msg) and data["line"] in ("1", "2"):
    #     publish.single(
    #         f'scrollbarline{data["line"]}', 
    #         data["msg"], 
    #         qos=0, 
    #         retain=True, 
    #         hostname=MQTT_HOST,
    #         port=MQTT_PORT, 
    #         client_id="set-scrollbar",
    #         keepalive=60,
    #         will=None,
    #         auth=MQTT_AUTH,
    #         tls=None,
    #         protocol=mqtt.MQTTv311,
    #         transport="tcp",
    #         )
    has_sb1 = False
    has_sb2 = False
    data, result = {}, {}
    for key, value in request.values.items():
        if key == "sb1":
            has_sb1 = True
        if key == "sb2":
            has_sb2 = True
        data[key] = value
    
    if not has_sb1 and not has_sb2:
        return BADREQ

    publish.single(
        'scrollbarline1', 
        data["sb1"], 
        qos=0, 
        retain=True, 
        hostname=MQTT_HOST,
        port=MQTT_PORT, 
        client_id="set-scrollbar",
        keepalive=60,
        will=None,
        auth=MQTT_AUTH,
        tls=None,
        protocol=mqtt.MQTTv311,
        transport="tcp",
        )

    publish.single(
        'scrollbarline2',
        data["sb2"], 
        qos=0, 
        retain=True, 
        hostname=MQTT_HOST,
        port=MQTT_PORT, 
        client_id="set-scrollbar",
        keepalive=60,
        will=None,
        auth=MQTT_AUTH,
        tls=None,
        protocol=mqtt.MQTTv311,
        transport="tcp",
        )
    automation_stir_browser()
    return GOODREQ

@app.route('/api/getscrollbar')
@cross_origin()
def get_scrollbar():
    msg1 = json.dumps(subscribe.simple(
        'scrollbarline1', 
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
        ).payload.decode('utf-8'))
    msg2 = json.dumps(subscribe.simple(
        'scrollbarline2', 
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
        ).payload.decode('utf-8'))
    results = {
        'line1': msg1.strip('"').strip("\\"),
        'line2': msg2.strip('"').strip("\\"),
        }
    return(results)

@app.route('/api/whoareyou')
@cross_origin()
def whoami():
    return TEAPOTREQ