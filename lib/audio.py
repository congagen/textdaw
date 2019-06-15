import os
import array
import wave
import json
import random
import math
import time
import pygame

from lib import utils


class Synth(object):
    def __init__(self, sample_rate, note_range=10000):
        self.sample_rate = sample_rate
        self.note_freq_list = []

        for i in range(note_range):
            note_freq = 27.500 * (1.0594630943592952645618252949463 ** (i + 1))
            self.note_freq_list.append(note_freq)


    def osc(self, frame_index, op1_note, op2_note, fm_multi=1, fm_amount=0):
        op1_freq = (self.sample_rate * (1 / ((self.note_freq_list[op1_note]))))
        op2_freq = (self.sample_rate * (1 / ((self.note_freq_list[op2_note]))))

        op1_sin = math.sin((math.pi * 2 * (frame_index % op1_freq)) / op1_freq)
        op2_sin = math.sin((math.pi * 2 * (frame_index % op2_freq)) / op2_freq) * fm_multi

        composite = op1_sin - ((op1_sin * op2_sin) * fm_amount)

        return composite


    def envelope(self, cursor, num_frames, a, s, r):
        num_a_frames = int((num_frames * a))
        num_s_frames = int((num_frames * (abs(s - (a + r) + 1))))
        num_r_frames = int((num_frames * r))

        if int(cursor) < int(num_a_frames):
            current_envelope = cursor * (1 / num_a_frames)
        elif int(cursor) > int(num_a_frames + num_s_frames):
            dec_val = (1.0 / num_r_frames) * (cursor - (num_a_frames + num_s_frames))
            current_envelope = 1.0 - dec_val
        else:
            current_envelope = 1.0

        e_val = max(min(current_envelope, 0.9999), 0.0)

        return e_val


    def render_note(self, note_value, note_length, adr=[0.1, 1.0, 0.1], fm_multi=2.0, fm_amount=0.0, max_amp=30000):
        note_audio_frames = array.array('h')
        num_frames = int(((self.sample_rate / 1000) * (note_length * 2)))
        max_amplitude = max_amp

        for i in range(num_frames):
            amp_envelope = self.envelope(i, num_frames, adr[0], adr[1], adr[2])
            audio_frame = self.osc(i, note_value, note_value, fm_multi=1, fm_amount=fm_amount)

            note_amp = 1 / (abs(note_value * (note_value * 0.001)) + 2)
            note_amp_frame = abs(max_amplitude * note_amp)

            tot_amp = (note_amp_frame * amp_envelope)
            note_frame = int(audio_frame * tot_amp)

            note_audio_frames.append(note_frame)

        return note_audio_frames


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


    # def sfx(self, output_path, s_count=20, s_duration=0.5, note_freq=20, mod_freq=10, freq_interval=30, fx=0):
    #     sample_rate = 44100
    #     chan_count = 2
    #     dataSize = 2
    #
    #     s = Synth(
    #         sample_rate=sample_rate, note_range=100000
    #     )
    #
    #     for i in range(s_count):
    #         tone = s.render_note(i, 1, adr=[0.1, 1.0, 0.1], fm_multi=2, fm_amount=0, max_amp=30000)
    #
    #         num_samples = int(sample_rate * s_duration)
    #
    #         f_path = output_path +"/"+ str(i) + ".wav"
    #
    #         f = wave.open(f_path, 'w')
    #         f.setparams((chan_count, dataSize, sample_rate, num_samples, "NONE", "Uncompressed"))
    #         f.writeframes(tone.tobytes())
    #         f.close()
    #
    #     return output_path


    def sfx(self, output_path, s_count=20, s_duration=0.5, note_freq=20, mod_freq=10, freq_interval=30, fx=0):
        for i in range(s_count):
            op1_freq = note_freq + (i * freq_interval)
            op2_freq = mod_freq + (i * mod_freq)

            volume = 100
            data = array.array('h')
            sample_rate = 44100
            chan_count = 2
            dataSize = 2

            op1_sam_per_cycle = int(sample_rate / op1_freq)
            op2_sam_per_cycle = int(sample_rate / op2_freq)

            num_samples = int(sample_rate * s_duration)

            for s in range(num_samples):
                sample = 32767 * float(volume) / 100

                f_mod = (((num_samples * 2.0) / (s + 1.0)) * fx) + 1.0

                f_a = math.sin(math.pi * 2 * (s % op1_sam_per_cycle) / op1_sam_per_cycle * f_mod)
                #f_b = math.sin(math.pi * 2.123456 * (s % op2_sam_per_cycle) / op2_sam_per_cycle)

                sample *= f_a

                data.append(int(sample))

            f_path = output_path + "/" + str(i) + ".wav"

            f = wave.open(f_path, 'w')
            f.setparams((chan_count, dataSize, sample_rate, num_samples, "NONE", "Uncompressed"))
            f.writeframes(data.tobytes())
            f.close()

        return output_path