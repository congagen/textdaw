import sys
import ssl

import json
import websocket

from lib import utils


class Cli(object):
    def __init__(self):
        pass


    def c_input(self, json_path, merge_key="cli_seeds", prompt="\nEnter text: "):
        while 1:
            i = input(prompt)

            if i != "":
                print("    " + i + "\n")
                if i.lower() in ["clear", "reset"]:
                    d = utils.store_json(json_path, {merge_key: [""]}, clear=True, merge_key=merge_key)
                else:
                    d = utils.store_json(json_path, {merge_key: i}, clear=True, merge_key=merge_key)

                print("\n"*1000)
                print(str(d))
                self.c_input(json_path)


class WsClient(object):
    def __init__(self, ws_url, header, cache_path="", ping_interval=60, ping_timeout=10):
        self.url = ws_url
        self.header = header
        self.cache_path = cache_path

        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message = lambda ws, msg: self.on_message(ws, msg),
            on_error   = lambda ws, msg: self.on_error(ws, msg),
            on_close   = lambda ws:      self.on_close(ws),
            on_open    = lambda ws:      self.on_open(ws),
            header=self.header, keep_running=True
        )

        self.ws.run_forever(
            ping_interval=ping_interval, ping_timeout=ping_timeout,
            sslopt={"cert_reqs": ssl.CERT_NONE}
        )

    def on_open(self, ws):
        print("OnOpen")

    def on_message(self, ws, message):
        print("OnMessage: " + str(message))

        try:
            resp = json.loads(message)
            if self.cache_path != "":
                utils.store_data(self.cache_path, resp)
        except ValueError as e:
            print("Malformd response:" + str(message))

    def on_error(self, ws, error):
        print("WS: ERROR")
        print(error)

    def on_close(self, ws):
        print("### closed ###")

    def format_req(req_dct):
        return str(req_dct).replace("""'""", """\"""")


# import telegram
# from telegram.error import NetworkError, Unauthorized
# from time import sleep
# update_id = None
# class TelegramBot():
#     def __init__(self):
#         pass
#
#     def main(self, token):
#         global update_id
#         bot = telegram.Bot(token)
#
#         try:
#             update_id = bot.get_updates()[0].update_id
#         except IndexError:
#             update_id = None
#
#         while True:
#             try:
#                 self.handle_msg(bot)
#             except NetworkError:
#                 sleep(1)
#             except Unauthorized:
#                 update_id += 1
#
#
#     def handle_msg(self, bot):
#         global update_id
#         for update in bot.get_updates(offset=update_id, timeout=10):
#             update_id = update.update_id + 1
#
#             if update.message:
#                 update.message.reply_text(update.message.text)
#                 print(update.message.text)