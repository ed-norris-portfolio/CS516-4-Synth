# CS516 - Project 4 - Synth

Ed Norris - Spring 2026

### Description
Make a synth!

Specifically, an application that listens for MIDI messages and plays the appropriate notes through the local sound device.

Caveats
1. Monophonic
2. All sounds are squaretooth waves
3. All notes are the same volume

See SYNTH.mp4 for a quick example.  It is truly a tragedy (for all of us) that we were limited to 5 seconds by the requirements.

### Development
This is two parts
1. A controller that generates notes
1. An instrument that 
   1. Listens for notes and
   1. Turns them into data for consumption by a sound card or file system.

The first part is optional for the assignment but critical for debugging.  You could also debug with [Cheap Midi Piano](https://github.com/ed-norris/cheap-midi-piano/blob/main/SPEC.md)

Inspired by the more robust and flexible implementation at https://github.com/pdx-cs-sound/fm 

### To run
List devices
```commandline
uv run project4.py --devices
```

Then run with `uv` 

```commandline
uv run project4.py --device [device name]
```

