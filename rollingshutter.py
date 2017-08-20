#!/usr/bin/env python
"""This script creates a 'rolling-shutter' effect image from a video clip"""

__author__ = 'Alex Zeising'
__version__ = '0.13.0 - direct movie'

# import os
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import asksaveasfilename, askopenfile
# from tkinter.messagebox import showerror, showinfo, askyesno
from tkinter.messagebox import showinfo, askyesno
from threading import Thread

from PIL import Image, ImageDraw, ImageTk # will get removed 

import imageio # for direct movie input

MAX_SPEED = 30
IMAGE_QUALITY = 95  # effective range stops at 100


class MainApp(object):
    # contains GUI (tkinter) structure and logic
    
    def __init__(self, master):
        self.master = master

        # executes self.on_closing on program exit
        master.protocol('WM_DELETE_WINDOW', self.on_closing)
        master.resizable(False, False)
        master.minsize(width=400, height=380)
        master.title('The RSE-Simulator')

        self.rolling_shutter = None

        self.vid = None
        self.file_output = ''

        self.preview_window = None
        self.thread = None

        self.tk_speed_val = tk.IntVar()
        self.tk_speed_val.set(1)
        self.tk_progress_val = tk.DoubleVar()
        self.tk_progress_val.set(0.0)

        # <- FRAME SECTION ->
        
        self.frame_main = tk.Frame(master)
        self.frame_main.pack(fill='both', expand=True)
        
        self.frame_footer = tk.Frame(master)
        self.frame_footer.pack(fill='both', anchor='s')

        # <- WIDGET SECTION ->
       
        self.label_title = ttk.Label(self.frame_main,
                                     text='Rolling-Shutter-Simulator',
                                     font=('Tahoma', 18))
        self.label_title.pack(pady=(8, 20))

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
                                            variable=self.tk_progress_val)
        self.progress_bar.pack(fill='x', padx=20, pady=(30, 0))
        self.progress_bar.state(['disabled'])
        
        self.btn_start = ttk.Button(self.frame_main,
                                    text='Give it a go!',
                                    command=self.start,
                                    state='disabled',
                                    takefocus=0)
        self.btn_start.pack(fill='both', padx=140, pady=(8, 0), expand=True)
        
        
        self.label_version = tk.Label(self.frame_footer,
                                      text='Version '+__version__,
                                      font=('Tahoma', 10),
                                      fg='grey60')
        self.label_version.pack(anchor='e', padx=(0, 5))

    def select_input(self) -> None:
        """
        Select input file
        """
        file = askopenfile(title='Please select the video to process',
                           filetypes=[('Video files',
                           ['.mov','.avi','.mpg','.mpeg','.mp4','.mkv','.wmv'])])
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
        """
        Select output file
        """
        path = asksaveasfilename(title='Please select the path of the image to create.',
                                 defaultextension='.png',
                                 filetypes=[('PNG File', '*.png'), ('JPEG File', '*.jpg')])
        if not path:
            return None
        
        self.file_output = path

        self.speed_scale.state(['!disabled'])
        self.btn_start['state'] = 'normal'
        
    def show_preview(self) -> None:
        
        if self.preview_window:
            self.preview_window.on_closing()

        newWindow = tk.Toplevel(self.master)
        self.preview_window = PreviewWindow(newWindow,self.vid._meta['size'])
        
    def start(self) -> None:
        rs = self.rolling_shutter = RollingShutter(self.vid,
                                                   self.tk_speed_val.get(),
                                                   self.file_output,self.preview_window)
        
        lines_covered = rs.frame_count * self.tk_speed_val.get()
        
        if lines_covered < rs.height:
            m = ('The number of iterations ({}) is lower than the height'
                 ' of the resulting image ({}px).\n\nMissing spots ({} lines)'
                 ' will be filled with black.\n\n'
                 'Do you want to continue?')
            message = m.format(lines_covered,
                               rs.height,
                               rs.height-lines_covered)
            choice = askyesno('Proceed?', message)
                              
            if not choice:
                return None
            
        self.disable_buttons()
        self.progress_bar.config(maximum=lines_covered)
        self.progress_bar.state(['!disabled'])

        self.thread = Thread(target=rs.thread, args=(self,))
        self.thread.setDaemon(True)
        self.thread.start()

    def update_speed(self, event=None) -> None:
        self.label_speed.config(text='Shutter Speed: '+str(self.tk_speed_val.get()))

    def update_progress(self, value: float):
        self.tk_progress_val.set(value)

    def enable_buttons(self) -> None:
        """
        Enable UI buttons
        """
        self.btn_input['state'] = 'normal'
        self.btn_start['state'] = 'normal'
        self.btn_output['state'] = 'normal'
        self.btn_preview['state'] = 'normal'
        self.speed_scale.state(['!disabled'])

    def disable_buttons(self) -> None:
        """
        Disable UI buttons
        """
        self.btn_input['state'] = 'disabled'
        self.btn_start['state'] = 'disabled'
        self.btn_output['state'] = 'disabled'
        self.btn_preview['state'] = 'disabled'
        self.speed_scale.state(['disabled'])

    def on_closing(self) -> None:
        """
        Closing method
        """
        if self.rolling_shutter and self.rolling_shutter.running:
            return None

        self.master.destroy()

class PreviewWindow(object):
    # contains GUI (tkinter) structure and logic
    
    def __init__(self, master, size):
        self.master = master

        # executes self.on_closing on program exit
        master.protocol('WM_DELETE_WINDOW', self.on_closing)
        master.resizable(False, False)
        master.minsize(width=400, height=380)
        master.title('Preview')

        self.image = None

        # <- FRAME SECTION ->
        
        self.frame_main = tk.Frame(master)
        self.frame_main.pack(fill='both', expand=True)
        
        self.frame_footer = tk.Frame(master)
        self.frame_footer.pack(fill='both', anchor='s')

        # <- WIDGET SECTION ->
       
        self.label_title = ttk.Label(self.frame_main,
                                     text='Rolling-Shutter-Simulator',
                                     font=('Tahoma', 18))
        self.label_title.pack(pady=(8, 20))

        # canvas for image
        #self.canvas = tk.Canvas(self.frame_main, width=512, height=512)
        #self.canvas.pack()
        #self.canvas.grid(row=0, column=0)

        # Balck temp image
        im = Image.new("RGB",(512,512))
        self.image = ImageTk.PhotoImage(im)

        # put balck image on canvas
        #self.image_on_canvas = self.canvas.create_image((0,0), anchor = 'nw', image = self.image)

        self.image_panel = tk.Label(self.frame_main, image = self.image)
        #self.can
        self.image_panel.pack(side = "bottom", fill = "both", expand = "yes")
        
        self.label_version = tk.Label(self.frame_footer,
                                      text='Version '+__version__,
                                      font=('Tahoma', 10),
                                      fg='grey60')
        self.label_version.pack(anchor='e', padx=(0, 5))
    
    def update_image(self,im):
        new_image = ImageTk.PhotoImage(im.resize((512,512), Image.ANTIALIAS))
        self.image = new_image
        self.image_panel.configure(image = self.image)
        self.image_panel.image = self.image
        #self.image = ImageTk.PhotoImage("RGB",(1,1))
        #self.canvas.itemconfig(self.image_on_canvas, image = new_image)
        #self.canvas.pack()
        #self.canvas.update_idletasks()

    def on_closing(self) -> None:
        """
        Closing method
        """
        self.master.destroy()

class RollingShutter(object):
    """
    Simulates the well-known 'Rolling-Shutter-Parker-Effect'
    """
    
    ## WIP: Add typechecking for video_reader
    def __init__(self, video_reader, speed: int, path_output: str, preview_window = None):
        self.speed = speed
        self.path_output = path_output
        self.preview_window = preview_window

        self.video_reader = video_reader
        self.frame_count = len(video_reader)

        self.current_row = 0

        #self.writer = imageio.get_writer(path_output)
        #WIP: replace Image with imageio's image output
        width, height = self.video_reader._meta['size']
        self.img_output = Image.new('RGB', (width, height))
        
        self.width, self.height = width, height

        self.running = False
        
    def thread(self, app_obj) -> None:
        width, height = self.video_reader._meta['size']
        speed = self.speed
        
        self.running = True
          
        try:
            for _, frame in enumerate(self.video_reader):
                
                frame = Image.fromarray(frame)

                new_line = frame.crop((0,
                                       self.current_row,
                                       width,
                                       self.current_row + speed))
                
                self.img_output.paste(new_line, (0, self.current_row))

                if self.preview_window:
                    im = frame

                    # Replace 
                    top_part = (0,0,width-1,self.current_row+speed-1)
                    im.paste(self.img_output.crop(top_part), top_part)

                    # Draw a line to show the current shutter position
                    draw = ImageDraw.Draw(im)
                    draw.line([(0, self.current_row),(width,self.current_row)], fill=128, width=speed)
                    
                    # cOnvert back to RGB to draw
                    im = im.convert('RGB')

                    self.preview_window.update_image(im)

                frame.close()

                app_obj.update_progress(self.current_row)
                
                self.current_row += speed
                if self.current_row > height:
                    app_obj.update_progress(height)
                    break
                
            #app_obj.update_progress(self.current_row)
            
            self.img_output.save(self.path_output, quality=IMAGE_QUALITY)
            
            app_obj.progress_bar.state(['disabled'])
            app_obj.enable_buttons()
            
            showinfo('Process Complete.', 'The shutter-rolled image has been created!')

        finally:
            self.running = False
            
            app_obj.update_progress(0)
            app_obj.progress_bar.state(['disabled'])
            app_obj.enable_buttons()
    
            
def main() -> None:
    root = tk.Tk()

    MainApp(root)
    root.mainloop()
    
if __name__ == '__main__':
    main()
