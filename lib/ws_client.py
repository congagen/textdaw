import ssl
import json
import websocket

conf_path = ""
session_path = ""

def update_data(conf_path, response_data, merge_key=""):
    print(conf_path)
    print(merge_key)

    with open(conf_path) as d:
        conf_file = json.load(d)

    tmp_data = conf_file
    d.close()

    for k in response_data.keys():
        if merge_key == "":
            tmp_data[k] = response_data[k]
        else:
            if merge_key in tmp_data:
                tmp_data[merge_key] = str(response_data[k])
            else:
                tmp_data[merge_key] += str(response_data[k])

    with open(conf_path, "w") as d:
        json.dump(tmp_data, d, sort_keys=True, indent=4)

    d.close()


def format_req(req_dct):
    return str(req_dct).replace("""'""", """\"""")


def on_message(ws, message):
    print(message)

    try:
        resp = json.loads(message)
        update_data(conf_path, resp)
        update_data(session_path, resp, "text_seed")

    except ValueError as e:
        print("Malformd data:" + str(message))



def on_msg_test():
    print()


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("### closed ###")


def main(ws_url, con_header, ping_interval=60, ping_timeout=10):
    ws = websocket.WebSocketApp(
        url=ws_url, on_message=on_message, on_error=on_error,
        on_close=on_close, header=con_header, keep_running=True)

    ws.run_forever(
        ping_interval=ping_interval, ping_timeout=ping_timeout,
        sslopt={"cert_reqs": ssl.CERT_NONE})