# CS516 - Project 4 - Synth

Ed Norris - Spring 2026

### Description
Make a synth

### Development
This is two parts
1. A controller that generates notes
1. An instrument that 
   1. Listens for notes and
   1. Turns them into data for consumption by a sound card or file system.

The first part is optional for the assignment but critical for debugging.  You could also debug with [Cheap Midi Piano](https://github.com/ed-norris/cheap-midi-piano/blob/main/SPEC.md)

### To run
List devices
```commandline
uv run project4.py --devices
```

Then run with `uv` 

```commandline
uv run project4.py --device [device name]
```

