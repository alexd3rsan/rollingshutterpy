# rollingshutterpy
A Tkinter GUI-Implementation of a simple rolling-shutter effect.

Inspired by this YouTube video:
https://www.youtube.com/watch?v=nP1elMR5qjc

Aims to simplify the process of creating fake rolling-shutter effects, as explained in said video.
It is still a rapid prototype though, so don't be surprised by errors.

INSTRUCTIONS:
1. Make sure you have 'Python 3.x' and the module 'Pillow' installed. (pip install pillow)
2. Run rollingshutter.py with python

3. Press 'Select Input' and choose any image of the exported frames of your video.
   The containing folder and filetype(!) of the frames + the size of the output image will be determined that way.
4. You may now press 'Select Output File' and choose the name and path of the resulting *.jpg file.
5. You may now change the 'Shutter Speed' with the help of the integrated slider, if you like.
   The higher the shutter speed, the more vertical lines will be skipped each frame.
6. Finally, press 'Give it a go!' and wait until a notification window appears.
7. Enjoy your distorted image!

Troubleshooting:
Make sure you have the proper read and write permissions of the directories in question!

Operating Systems:
rollingshutter.py has been successfully tested under:
- Windows 10 64 Bit
- Arch Linux
