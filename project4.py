import argparse, sounddevice
import random
import time

import numpy as np

debugging = False
sample_clock = 0
sample_rate = 48000
notes = []

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

class Saw(object):
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
        self.generator = Saw(self.freq)

    def samples(self, sample_count):
        """
        Generate samples for this note
        :param sample_count: probably 48
        :return: the samples
        """
        self.current_time += sample_count
        return self.generator.samples(self.current_time, sample_count)

def callback(out_data, frame_count, time_info, status):
    """Get me the next x frames of sound data"""
    output = np.zeros(frame_count, dtype=np.float32)
    for note in notes:
        output = note.samples(frame_count)

    global sample_clock
    sample_clock += frame_count
    out_data[:] = np.reshape(output, (frame_count, 1))

def query_devices():
    """
    > 0 MacBook Pro Microphone, Core Audio (1 in, 0 out)
    < 1 MacBook Pro Speakers, Core Audio (0 in, 2 out)
    2 SpacePhone16 Microphone, Core Audio (1 in, 0 out)
    """
    print(sounddevice.query_devices())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--devices", help="show audio devices", action=argparse.BooleanOptionalAction, required=False)
    parser.add_argument("--buffer-size", help="buffer size", type=int, default=48, required=False)
    args = parser.parse_args()
    if args.devices:
        query_devices()
        exit(0)

    stream = sounddevice.OutputStream(
        samplerate=sample_rate,
        channels=1,
        blocksize=args.buffer_size,
        callback=callback,
    )
    stream.start()

    # how about some 70s-era sound effects?
    for i in range(50):
        notes = [Note(random.randrange(30,80))]
        time.sleep(0.1)
    stream.close()
