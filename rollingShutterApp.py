#!/usr/bin/env python
''' This script creates a 'rolling-shutter' effect image from a video clip
'''

__author__ = 'Alex Zeising & Marcin Konowalczyk'
__version__ = '0.14.0 - options window'

# import os
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import asksaveasfilename, askopenfile
# from tkinter.messagebox import showerror, showinfo, askyesno
from tkinter.messagebox import askyesno

from PIL import Image, ImageTk
import imageio # for direct movie input

from rollingShutter import RollingShutter

MAX_SPEED = 30
IMAGE_QUALITY = 95  # effective range stops at 100

class MainApp(object):
    def __init__(self, master):
        ''' Contains GUI (tkinter) structure and logic
        '''
        self.master = master
        self.version = __version__

        # executes self.on_closing on program exit
        master.protocol('WM_DELETE_WINDOW', self.on_closing)
        master.resizable(False, False)
        master.minsize(width=400, height=380)
        master.title('The RSE-Simulator')

        self.rolling_shutter = RollingShutter()

        self.vid = None
        self.file_output = ''

        self.preview_window = None
        self.options_window = None

        self.tk_speed_val = tk.IntVar()
        self.tk_speed_val.set(1)
        self.tk_progress_val = tk.DoubleVar()
        self.tk_progress_val.set(0.0)

        self.populate_panel()

    def populate_panel(self) -> None:
        ''' Populate the window with things
        '''
        master = self.master

        # Window frame
        self.frame_main = tk.Frame(master)
        self.frame_main.pack(fill='both', expand=True)
        
        self.frame_footer = tk.Frame(master)
        self.frame_footer.pack(fill='both', anchor='s')

        # Window title
        self.label_title = ttk.Label(self.frame_main,
                                     text='Rolling-Shutter-Simulator',
                                     font=('Tahoma', 18))
        self.label_title.pack(pady=(8, 20))

        # Buttons
        self.btn_input = ttk.Button(self.frame_main,
                                    text='Select Input',
                                    command=self.select_input,
                                    takefocus=0)
        self.btn_input.pack(fill='both', padx=40, expand=True, pady=10)

        self.btn_output = ttk.Button(self.frame_main,
                                     text='Select Output File',
                                     command=self.select_output,
                                     state='disabled',
                                     takefocus=0)
        self.btn_output.pack(fill='both', padx=40, expand=True, pady=10)
        
        self.btn_options = ttk.Button(self.frame_main,
                                     text='Options',
                                     command=self.show_options,
                                     state='normal',
                                     takefocus=0)
        self.btn_options.pack(fill='both', padx=40, expand=True, pady=10)

        self.btn_preview = ttk.Button(self.frame_main,
                                     text='Show Preview window',
                                     command=self.show_preview,
                                     state='disabled',
                                     takefocus=0)
        self.btn_preview.pack(fill='both', padx=40, expand=True, pady=10)

        self.speed_scale = ttk.Scale(self.frame_main,
                                     variable=self.tk_speed_val,
                                     command=self.update_speed,
                                     from_=1, to=MAX_SPEED,
                                     length=310,
                                     takefocus=0)
        self.speed_scale.pack(pady=(8, 0))
        self.speed_scale.state(['disabled'])

        self.label_speed = ttk.Label(self.frame_main,
                                     text='Shutter Speed: 1',
                                     font=('Tahoma', 13))
        self.label_speed.pack(pady=(0, 8))

        self.progress_bar = ttk.Progressbar(self.frame_main,
                                            orient='horizontal',
                                            mode='determinate',
                                            variable=self.tk_progress_val,
                                            maximum = 100)
        self.progress_bar.pack(fill='x', padx=20, pady=(30, 0))
        self.progress_bar.state(['disabled'])
        
        self.btn_start = ttk.Button(self.frame_main,
                                    text='Give it a go!',
                                    command=self.start,
                                    state='disabled',
                                    takefocus=0)
        self.btn_start.pack(fill='both', padx=140, pady=(8, 0), expand=True)
        
        # Version label
        self.label_version = tk.Label(self.frame_footer,
                                      text='Version ' + self.version,
                                      font=('Tahoma', 10),
                                      fg='grey60')
        self.label_version.pack(anchor='e', padx=(0, 5))

    def select_input(self) -> None:
        ''' Select the input file
        '''
        file = askopenfile(title='Please select the video to process',
                           filetypes=[('Video files', ['.mov', '.avi', '.mpg', '.mpeg', '.mp4', '.mkv', '.wmv'])])
        if not file:
            return None

        # Try to close the video reader
        if self.vid:
            try:
                self.vid.close()
            finally:
                self.vid = None

        self.vid = imageio.get_reader(file.name, 'ffmpeg') # open video reader
        self.btn_output['state'] = 'normal'
        self.btn_preview['state'] = 'normal'

    def select_output(self) -> None:
        ''' Select the output file
        '''
        path = asksaveasfilename(title='Please select the path of the image to create.',
                                 defaultextension='.png',
                                 filetypes=[('PNG File', '*.png'), ('JPEG File', '*.jpg')])
        if not path:
            return None
        
        self.file_output = path

        self.speed_scale.state(['!disabled'])
        self.btn_start['state'] = 'normal'

    def show_options(self) -> None:
        ''' Show the options window
        '''
        if self.options_window:
            self.options_window.master.destroy()

        master = tk.Toplevel(self.master)
        self.options_window = OptionsWindow(master)

    def show_preview(self) -> None:
        ''' Show the preview window
        '''
        if self.preview_window:
            self.preview_window.master.destroy()

        master = tk.Toplevel(self.master)
        self.preview_window = PreviewWindow(master)

        # Set the preview window of the rolling-shutter instance
        self.rolling_shutter.set_preview_window(self.preview_window)
        
    def start(self) -> None:
        ''' Called by the start button 'btn_start'
        '''
        self.disable_buttons()

        rs = self.rolling_shutter
        rs.setup(self.vid, self.tk_speed_val.get(), self.file_output, IMAGE_QUALITY)

        lines_covered = rs.frame_count * self.tk_speed_val.get()
        if lines_covered > rs.size[1]:
            lines_covered = rs.size[1]

        if lines_covered < rs.size[1]:
            m = ('The number of iterations ({}) is lower than the height'
                 ' of the resulting image ({}px).\n\nMissing spots ({} lines)'
                 ' will be filled with black.\n\n'
                 'Do you want to continue?')
            message = m.format(lines_covered,
                               rs.size[1],
                               rs.size[1]-lines_covered)
            choice = askyesno('Proceed?', message)
                              
            if not choice:
                self.enable_buttons()
                return None

        self.progress_bar.config(maximum=lines_covered)
        self.progress_bar.state(['!disabled'])

        rs.start(self)

    def update_speed(self, event=None) -> None:
        self.label_speed.config(text='Shutter Speed: '+str(self.tk_speed_val.get()))

    def update_progress(self, value: float):
        self.tk_progress_val.set(value)

    def enable_buttons(self) -> None:
        self.btn_input['state'] = 'normal'
        self.btn_start['state'] = 'normal'
        self.btn_options['state'] = 'normal'
        self.btn_output['state'] = 'normal'
        #self.btn_preview['state'] = 'normal'
        self.speed_scale.state(['!disabled'])

    def disable_buttons(self) -> None:
        self.btn_input['state'] = 'disabled'
        self.btn_start['state'] = 'disabled'
        self.btn_options['state'] = 'disabled'
        self.btn_output['state'] = 'disabled'
        #self.btn_preview['state'] = 'disabled'
        self.speed_scale.state(['disabled'])

    def on_closing(self) -> None:
        if self.rolling_shutter and self.rolling_shutter.running:
            return None

        self.master.destroy()

class PreviewWindow(object):
    ''' The window for live-preview
    '''

    def __init__(self, master):
        self.master = master # Master tkinter object
        self.version = __version__
        self.open = True

        # Window settings
        master.protocol('WM_DELETE_WINDOW', self.on_closing)
        master.resizable(False, False)
        master.title('RS-Preview')

        self.image = None

        self.populate_panel()

    def populate_panel(self) -> None:
        ''' Populate the window with things
        '''
        master = self.master

        # Window frame
        self.frame_main = tk.Frame(master)
        self.frame_main.pack(fill='both', expand=True)
        
        self.frame_footer = tk.Frame(master)
        self.frame_footer.pack(fill='both', anchor='s')

        # Window title
        self.label_title = ttk.Label(self.frame_main,
                                     text='Rolling-Shutter-Simulator',
                                     font=('Tahoma', 18))
        self.label_title.pack(pady=(8, 20))
        
        # Preview canvas
        im = Image.new("RGB",(512,512)) # Black temp image
        self.image = ImageTk.PhotoImage(im)

        self.image_panel = tk.Label(self.frame_main, image = self.image)
        self.image_panel.pack(side = "bottom", fill = "both", expand = "yes")

        # Version label
        self.label_version = tk.Label(self.frame_footer,
                                      text='Version '+self.version,
                                      font=('Tahoma', 10),
                                      fg='grey60')
        self.label_version.pack(anchor='e', padx=(0, 5))
    
    def update_image(self,im):
        ''' Update the image on canvas
        '''
        self.image = ImageTk.PhotoImage(im.resize((512,512), Image.ANTIALIAS))
        self.image_panel.configure(image = self.image)
        self.image_panel.image = self.image

    def on_closing(self) -> None:
        self.open = False
        self.master.destroy()

class OptionsWindow(object):
    ''' The window for setting up options
    '''

    def __init__(self, master):
        self.master = master # Master tkinter object
        self.version = __version__
        self.open = True

        # Window settings
        master.protocol('WM_DELETE_WINDOW', self.on_closing)
        master.resizable(False, False)
        master.title('RS-Options')

        self.shutter_speed = tk.IntVar()
        self.shutter_speed.set(1)

        self.populate_panel()

    def populate_panel(self) -> None:
        ''' Populate the window with things
        '''
        master = self.master

        # Window frame
        self.frame_main = tk.Frame(master)
        self.frame_main.pack(fill='both', expand=True)
        
        self.frame_footer = tk.Frame(master)
        self.frame_footer.pack(fill='both', anchor='s')

        # Window title
        self.label_title = ttk.Label(self.frame_main,
                                     text='Rolling-Shutter-Simulator',
                                     font=('Tahoma', 18))
        self.label_title.pack(pady=(8, 20))
        
        # Buttons
        self.speed_scale = ttk.Scale(self.frame_main,
                                     variable=self.shutter_speed,
                                     command=self.update_speed,
                                     from_=1, to=MAX_SPEED,
                                     length=310,
                                     takefocus=0)
        self.speed_scale.pack(pady=(8, 0))
        self.speed_scale.state(['!disabled'])

        self.label_speed = ttk.Label(self.frame_main,
                                     text='Shutter Speed: 1',
                                     font=('Tahoma', 13))
        self.label_speed.pack(pady=(0, 8))

        # Version label
        self.label_version = tk.Label(self.frame_footer,
                                      text='Version '+self.version,
                                      font=('Tahoma', 10),
                                      fg='grey60')
        self.label_version.pack(anchor='e', padx=(0, 5))

    def update_speed(self, event=None) -> None:
        ''' Update speed label with the current value
        '''
        text = 'Shutter Speed: {}'.format(self.shutter_speed.get())
        self.label_speed.config(text=text)

    def on_closing(self) -> None:
        self.open = False
        self.master.destroy()

def main() -> None:
    root = tk.Tk()
    MainApp(root)
    root.mainloop()
    
if __name__ == '__main__':
    main()
