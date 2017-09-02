# rollingshutterpy

A Tkinter GUI-Implementation of a simple rolling-shutter effect.
This branch attempts to add direct input froma video file.

Inspired by [this](https://www.youtube.com/watch?v=nP1elMR5qjc) YouTube video.

Aims to simplify the process of creating fake rolling-shutter effects, as explained in said video.
It is still a rapid prototype though, so don't be surprised by errors.

## INSTRUCTIONS

1. Make sure you have 'Python 3.x' and the module 'Pillow' installed. (pip install pillow)
1. Run rollingshutter.py with python
1. Press 'Select Input' and choose the video file to use as an input.
1. You may now press 'Select Output File' and choose the name and path of the resulting *.png or (optionally) *.jpg file.
1. You may now change the 'Shutter Speed' with the help of the integrated slider, if necessary.
   The higher the shutter speed, the more vertical lines will be skipped each frame.
1. Finally, press 'Give it a go!' and wait until a notification window appears.
1. Enjoy your distorted image!

## Troubleshooting

Make sure you have the proper read and write permissions of the directories in question!

## Operating Systems

This fork of rollingshutter.py has been successfully tested under:

- MacOS X 10.12.6

## ToDo's

- Fix progress bar to reflect the realistic processing time
+ -Fix the crash when closing the preview window-
- Add realistic processing of the shutter speeds in non-integer speeds
- Add separate option panel
- Separate windows into files
- Add save to movie option
- Add phase roll rendering
- Refactor the code in a more sane way
