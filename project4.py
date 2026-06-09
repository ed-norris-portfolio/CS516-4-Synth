import argparse, sounddevice
import numpy as np
import random
import mido
import time
from mido import Message

sample_clock = 0
sample_rate = 48000
notes = [] # just one for now
amplitude = 0.0708 # -3dBFS

def make_times(start_time, sample_count):
    """Return a sequence of n time points for wave sampling."""
    times = np.linspace(
        start_time,
        start_time + sample_count,
        num = sample_count,
        endpoint = False,
        dtype = np.float32,
    )
    return times

class Sawtooth(object):
    # https://en.wikipedia.org/wiki/Sawtooth_wave
    def __init__(self, frequency):
        self.tmul = frequency / sample_rate

    def samples(self, start_time, sample_count):
        """
        Generate the next values of the sawtooth wave from the start time
        :param start_time: Number of frames since the note "started"
        :param sample_count: Number of samples
        :return: The samples
        """
        times = make_times(start_time, sample_count)
        a = self.tmul * times
        return 2.0 * (a - np.floor(0.5 + a))

class Note(object):
    def __init__(self, key):
        self.current_time = 0
        self.key = key
        self.freq = 440 * 2**((key - 69)/12)
        self.generator = Sawtooth(self.freq)

    def samples(self, sample_count):
        """
        Generate samples for this note
        :param sample_count: probably 48
        :return: the samples
        """
        self.current_time += sample_count
        return self.generator.samples(self.current_time, sample_count)

def sounddevice_callback(out_data, frame_count, time_info, status):
    """Get me the next x frames of sound data"""
    output = np.zeros(frame_count, dtype=np.float32)
    for note in notes:
        output = note.samples(frame_count)

    global sample_clock
    sample_clock += frame_count
    out_data[:] = amplitude * np.reshape(output, (frame_count, 1))

def query_devices(all_output = True):
    """
    # sound devices
    > 0 MacBook Pro Microphone, Core Audio (1 in, 0 out)
    < 1 MacBook Pro Speakers, Core Audio (0 in, 2 out)
    2 SpacePhone16 Microphone, Core Audio (1 in, 0 out)

    # MIDI ports
    IAC Driver Bus 1
    """

    if all_output:
        print(sounddevice.query_devices())
        print(f'Midi inputs are: {mido.get_input_names()}')

    print(f'Midi outputs are: {mido.get_output_names()}')

def handle_midi_input(message):
    print(message)
    global notes
    if message.type == "note_on":
        if message.velocity > 0:
            notes = [Note(message.note)]
        else:
            notes = []
    if message.type == "note_off":
        notes = []

def play_some_midi(midi_file = None, random_notes = False):
    """
    Instead of controller input, generate or read midi data and post it to the output device
    :param midi_file: Optional midi file
    :param random_notes: Or maybe you want some quick random notes
    """
    midi_output_port = mido.open_output()
    if midi_file is not None:
        mid = mido.MidiFile(midi_file)
        for msg in mid.play():
            midi_output_port.send(msg)
    elif random_notes:
        for i in range(10):
            msg = Message('note_on', note=random.randrange(30,80))
            print(msg)
            midi_output_port.send(msg)
            time.sleep(0.1)
            midi_output_port.send(Message('note_off', note=msg.note))
    midi_output_port.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--show-devices", help="show audio devices", default=False, action="store_true")
    parser.add_argument("--play-file", help="play a midi file", type=str, required=False)
    parser.add_argument("--random", help="play random midi for a few seconds", default=False, action="store_true")
    parser.add_argument("--buffer-size", help="buffer size", type=int, default=48, required=False)
    parser.add_argument("--device", help="midi device name", type=str, required=False)
    args = parser.parse_args()

    if args.show_devices:
        query_devices()
        exit(0)
    if args.device is None:
        print("Please specify a midi device")
        query_devices(all_output=False)
        exit(0)
    midi_device = args.device

    try:
        # sound output
        with sounddevice.OutputStream(
            samplerate=sample_rate,
            channels=1,
            blocksize=args.buffer_size,
            callback=sounddevice_callback,
        ) as audio_output_stream:
            audio_output_stream.start()

            with mido.open_input(midi_device, callback=handle_midi_input) as midi_input_port:
                if args.play_file is not None or args.random:
                    play_some_midi(random_notes=args.random, midi_file=args.play_file)
                else:
                    input("Waiting for MIDI input, press enter to quit")
            audio_output_stream.stop()

    except OSError as e:
        print(f"Failed to start: {e}")
