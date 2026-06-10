import argparse, sounddevice
import numpy as np
import random
import mido
import time
from mido import Message

sample_clock = 0
sample_rate = 48000
notes = {}
scaling = 0.708 # -3dBFS
amplitude = 0.1 * scaling # adjusting by ear
buffer_size = 48
envelope_samples = int(sample_rate * 0.01) # 10ms - so this would be 480

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

# create 0->1 and 1->0 arrays for linear scaling
ramp_up = make_times(0, envelope_samples) / envelope_samples
ramp_down = np.append(np.flip(ramp_up, axis = 0), np.zeros(buffer_size), axis = 0)

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
        self.death_time = 0

    def samples(self, sample_count):
        """
        Generate samples for this note
        :param sample_count: probably 48
        :return: the samples
        """
        self.current_time += sample_count
        generated_samples = self.generator.samples(self.current_time, sample_count)

        if self.current_time < envelope_samples:
            # fade in
            return generated_samples * ramp_up[self.current_time:self.current_time+sample_count]
        elif self.death_time > 0:
            # fade out or zero
            elapsed_time = self.current_time - self.death_time
            if elapsed_time >= envelope_samples:
                global notes
                del notes[self.key]
                return np.zeros(int(sample_count), dtype=np.float32)
            return generated_samples * ramp_down[elapsed_time:elapsed_time+sample_count]
        return generated_samples

    def die(self):
        self.death_time = self.current_time

def sounddevice_callback(out_data, frame_count, time_info, status):
    """Get me the next x frames of sound data"""
    output = np.zeros(frame_count, dtype=np.float32)
    for key in notes:
        output = notes[key].samples(frame_count)
        break

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
        print("Sound devices detected:")
        print(sounddevice.query_devices())
        print(f'\nMidi outputs are: {mido.get_output_names()}')

    print(f'\nMidi inputs are: {mido.get_input_names()}\n')

def handle_midi_input(message):
    print(message)
    global notes
    if message.type == "note_on" and message.velocity > 0:
        notes = {message.note: Note(message.note)}
    elif message.type == "note_on" or message.type == "note_off":
        note = notes[message.note]
        if note != None:
            note.die()

def play_some_midi(midi_device, midi_file = None, random_notes = False):
    """
    Instead of controller input, generate or read midi data and post it to the output device
    :param midi_file: Optional midi file
    :param random_notes: Or maybe you want some quick random notes
    """
    midi_output_port = mido.open_output(midi_device)
    if midi_file is not None:
        for msg in mido.MidiFile(midi_file).play():
            midi_output_port.send(msg)
    elif random_notes:
        for i in range(100):
            msg = Message('note_on', note=random.randrange(30,80))
            midi_output_port.send(msg)
            time.sleep(0.1)
            midi_output_port.send(Message('note_off', note=msg.note))
    midi_output_port.close()
    time.sleep(0.1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--show-devices", help="show audio devices", default=False, action="store_true")
    parser.add_argument("--play-file", help="play a midi file", type=str, required=False)
    parser.add_argument("--random", help="play random midi for a few seconds", default=False, action="store_true")
    parser.add_argument("--device", help="midi device name", type=str, required=False)
    args = parser.parse_args()

    if args.show_devices:
        query_devices()
        exit(0)
    if args.device is None:
        print("Please specify a midi input device")
        query_devices(all_output=False)
        print("\nIf you are on a mac and do not see a value, try:")
        print("1. Open 'Audio MIDI Setup'")
        print("2. Go to Window | Show MIDI Studio")
        print("3. Click 'IAC Driver'")
        print("4. Ensure 'Device is online' is checked")
        exit(0)
    midi_device = args.device

    try:
        with sounddevice.OutputStream(
            samplerate=sample_rate,
            channels=1,
            blocksize=buffer_size,
            callback=sounddevice_callback,
        ) as audio_output_stream:
            audio_output_stream.start()

            with mido.open_input(midi_device, callback=handle_midi_input) as midi_input_port:
                if args.play_file is not None or args.random:
                    play_some_midi(midi_device, random_notes=args.random, midi_file=args.play_file)
                input("Listening for MIDI input, or press enter to quit")
            audio_output_stream.stop()

    except OSError as e:
        print(f"Failed to start: {e}")
    except KeyboardInterrupt:
        print("\nGoodbye!")
