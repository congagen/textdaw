import os
import array
import wave
import json
import random
import math
import time
import pygame

from lib import utils


class Daw():
    def __init__(self, conf_path, session_path, root_sample_path, ch_count=10, ptn_length=16, debug=False):
        self.init = False
        self.seed_chars = "abcdefghijklmnopqrstuvxyz1234567890"
        self.keymap     = {}

        for c in self.seed_chars:
            self.keymap[c] = ord(c)

        self.loop_count = 2

        self.conf_path   = conf_path
        self.session_path = session_path

        self.conf_cache  = {}
        self.tracks = {}

        self.paused = False

        self.chan_count  = ch_count
        self.bpm         = 240
        self.debug       = debug
        self.swing       = 0

        self.composite_seed_n = 0
        self.composite_seed_s = "init"

        self.pattern_length = ptn_length
        self.pattern_length = ptn_length

        self.root_sample_path = root_sample_path
        self.sample_paths = []

        pygame.init()
        pygame.mixer.init()
        pygame.mixer.set_num_channels(self.chan_count)


    def update_sample_data(self):
        self.sample_paths = utils.get_abs_paths(self.root_sample_path)


    def play_wav_sample(self, sample_path, loop=False):
        chan = int(self.chan_count * abs(math.sin(time.time())))
        if self.debug:
            print("Playing: " + str(os.path.basename(sample_path)) + " @ Channel: " + str(chan))

        pygame.mixer.Channel(chan).play(pygame.mixer.Sound(sample_path))


    def update_settings(self, conf_path):
        with open(conf_path) as d:
            curr_conf = json.load(d)

        with open(self.session_path) as d:
            curr_sess = json.load(d)

        new_comp_seed = ""

        for k in curr_sess.keys():
            new_comp_seed += str(curr_sess[k])

        self.composite_seed_s = new_comp_seed
        self.composite_seed_n = abs(utils.any_to_num(self.composite_seed_s, "1234")[0]) + 1

        if "bpm" in curr_conf.keys():
            if curr_conf["bpm"] != "":
                self.bpm = utils.any_to_num(curr_conf["bpm"], "120")[1]

        if "pattern_length" in curr_conf.keys():
            if curr_conf["pattern_length"] != "":
                self.pattern_length = utils.any_to_num(curr_conf["pattern_length"], "120")[1]

        if "loop_count" in curr_conf.keys():
            if curr_conf["loop_count"] != "":
                self.loop_count = utils.any_to_num(curr_conf["loop_count"], "2")[1]

        if self.debug:
            print("Bpm: " + str(self.bpm))
            print("New string seed: " + str(self.composite_seed_s))
            print("New number seed: " + str(self.composite_seed_n))

        random.seed(self.composite_seed_s)


    def text_to_sequence(self, input_text, item_list, seq_length, filer_input=False, reverse=True, position_seed=1):

        i_txt = input_text

        if filer_input:
            i_txt = "".join([i if i.lower() in self.seed_chars else "" for i in i_txt])

        if reverse:
            i_txt = i_txt[::-1]

        i_txt = i_txt.replace(" ", "")

        while len(i_txt) < seq_length:
            i_txt += "xyz"

        seq = []

        for i in range(seq_length):
            i_sine = abs(math.sin(position_seed + ord(i_txt[i]) * 0.987654321))
            idx = int((len(item_list)-1) * i_sine)
            seq.append(item_list[idx])

        if self.debug:
            print("\n")
            print("Raw seed:   " + input_text)
            print("Filter seed: " + i_txt)
            print("\n")

        return seq


    def main(self, track_id, randomize=False):
        self.update_sample_data()
        self.tracks[track_id] = True
        seq_list = self.text_to_sequence(
            self.composite_seed_s, self.sample_paths, self.pattern_length)
        ptn_pos = 0
        bar = 0

        while self.tracks[track_id]:
            if not self.paused:
                self.update_settings(self.conf_path)

                if self.debug:
                    print("\nBar: " + str(bar) + " @ " + "Seq: " + str(ptn_pos) + "\n")

                if ptn_pos < (len(seq_list) - 1):
                    ptn_pos += 1
                else:
                    self.update_sample_data()
                    if self.loop_count > 0:
                        bar += 1

                    if bar % abs(self.loop_count + 1) == 0:
                        seq_list = self.text_to_sequence(
                            self.composite_seed_s, self.sample_paths,
                            self.pattern_length, position_seed=bar
                        )

                    ptn_pos = 0

                sample_file_path = seq_list[ptn_pos]
                self.play_wav_sample(sample_file_path)

                time.sleep(60.0 / float(self.bpm))


class Generators():
    def __init__(self):
        pass


    def sfx(self, output_path, s_count=20, s_duration=0.5, base_freq=20, freq_interval=25, fx=0):

        for i in range(s_count):
            s_freq = base_freq + (i * freq_interval)
            volume = 100
            data = array.array('h')
            sample_rate = 44100
            chan_count = 2
            dataSize = 2
            sam_per_cycle = int(sample_rate / s_freq)
            num_samples = int(sample_rate * s_duration)

            for s in range(num_samples):
                sample = 32767 * float(volume) / 100

                f_mod = (((num_samples * 2) / (s + 1)) * fx) + 1
                sample *= math.sin(math.pi * 2 * (s % sam_per_cycle) / sam_per_cycle * f_mod)

                data.append(int(sample))

            f_path = output_path +"/"+ str(i) + ".wav"

            f = wave.open(f_path, 'w')
            f.setparams((chan_count, dataSize, sample_rate, num_samples, "NONE", "Uncompressed"))
            f.writeframes(data.tobytes())
            f.close()

        return output_path
