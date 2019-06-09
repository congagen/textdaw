import os
import sys
import json
import random
import threading

from lib import interaction
from lib import audio

print("\n" * 1000)

def init_audio(conf_path, session_path, sample_path="", track_name="untitled", debug=False):
    if sample_path == "":
        input("Enter sample path: ")

    a_studio = audio.Daw(
        conf_path, session_path, sample_path,
        ch_count=100, ptn_length=4, debug=debug
    )

    audio_thread = threading.Thread(
        target=a_studio.main, args=(track_name, 0,))

    return audio_thread


def init_ws(sys_conf_path, session_path):
    with open(sys_conf_path) as d:
        sys_conf = json.load(d)

    interaction.WsClient(
        sys_conf["ws"]["url"],
        sys_conf["ws"]["header"],
        session_path)


def init_session(session_name, init_conf):
    session_conf_path = "sessions/s_" + session_name + ".json"
    if not os.path.exists(session_conf_path):
        with open(session_conf_path, "w") as d:
            json.dump({}, d, sort_keys=True, indent=4)

    project_conf_path = "conf/system" + ".json"
    if not os.path.exists(project_conf_path):
        with open(project_conf_path, "w") as d:
            json.dump(init_conf, d, sort_keys=True, indent=4)

    pro_path = os.path.abspath(project_conf_path)
    ses_path = os.path.abspath(session_conf_path)

    return [pro_path, ses_path]


if __name__ == '__main__':
    threads = []
    init_samples = True
    init_conf = {"bpm": "120", "pattern_length": "8", "loop_count": "4"}

    session = init_session("demo", init_conf)
    project_conf_path = session[0]
    session_conf_path = session[1]

    audio_gens = audio.Generators()
    sample_folders = ["data/samples/misc"]

    if init_samples:
        audio_gens.sfx(
            "data/samples/misc", s_count=100, s_duration=0.4,
            base_freq=10, freq_interval=100, fx=5.98765431)

    for a in sample_folders:
        threads.append(
            init_audio(project_conf_path, session_conf_path, a))

    for t in threads:
        print("initializing: " + str(t.name))
        t.start()

    cli = interaction.Cli()
    cli.c_input(session_conf_path, merge_key="cli_seeds")
