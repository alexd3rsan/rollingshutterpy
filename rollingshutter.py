__author__ = 'Alex Zeising'
__version__ = '0.12'

import os
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import asksaveasfilename, askopenfile
from tkinter.messagebox import showerror, showinfo, askyesno
from threading import Thread

from PIL import Image


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

        self.files = []
        self.file_output = ''

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
        self.btn_output.pack(fill='both', padx=40, expand=True)
        
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
        file = askopenfile(title='Please select one (any) frame from your set of images.',
                           filetypes=[('Image Files', ['.jpeg', '.jpg', '.png', '.gif',
                                                       '.tiff', '.tif', '.bmp'])])
        if not file:
            return None
        
        dir_ = os.path.dirname(file.name)
        filetype = os.path.splitext(file.name)
        
        self.files = [os.path.abspath(os.path.join(dir_, f))
                      for f in os.listdir(dir_)
                       if f.endswith(filetype)]
        self.files.sort()
        
        self.btn_output['state'] = 'normal'

    def select_output(self) -> None:
        path = asksaveasfilename(title='Please select the path of the image to create.',
                                 defaultextension='.png',
                                 filetypes=[('PNG File', '*.png'), ('JPEG File', '*.jpg')])
        if not path:
            return None
        
        self.file_output = path

        self.speed_scale.state(['!disabled'])
        self.btn_start['state'] = 'normal'
        
        
    def start(self) -> None:
        rs = self.rolling_shutter = RollingShutter(self.files,
                                                   self.tk_speed_val.get(),
                                                   self.file_output)
        
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
        
        t1 = Thread(target=rs.thread, args=(self,))
        t1.setDaemon(True)
        t1.start()

    def update_speed(self, event=None) -> None:
        self.label_speed.config(text='Shutter Speed: '+str(self.tk_speed_val.get()))

    def update_progress(self, value: float):
        self.tk_progress_val.set(value)

    def enable_buttons(self) -> None:
        self.btn_input['state'] = 'normal'
        self.btn_start['state'] = 'normal'
        self.btn_output['state'] = 'normal'
        self.speed_scale.state(['!disabled'])

    def disable_buttons(self) -> None:
        self.btn_input['state'] = 'disabled'
        self.btn_start['state'] = 'disabled'
        self.btn_output['state'] = 'disabled'
        self.speed_scale.state(['disabled'])
        
    def on_closing(self) -> None:
        if self.rolling_shutter and self.rolling_shutter.running:
            return None
        
        self.master.destroy()

        
class RollingShutter(object):
    # simulates the well-known 'Rolling-Shutter-Parker-Effect'
    
    def __init__(self, frame_paths: list, speed: int, path_output: str):
        self.frame_paths = frame_paths
        self.speed = speed
        self.path_output = path_output

        self.frame_count = len(frame_paths)

        self.current_row = 0

        width, height = Image.open(frame_paths[0]).size
        self.img_output = Image.new('RGB', (width, height))

        self.width, self.height = width, height
        
        self.running = False
        
    def thread(self, app_obj) -> None:
        width, height = self.width, self.height
        speed = self.speed
        
        self.running = True
        
        try:
            for path in self.frame_paths:
                frame = Image.open(path)
                
                new_line = frame.crop((0,
                                       self.current_row,
                                       width,
                                       self.current_row + speed))
                
                self.img_output.paste(new_line, (0, self.current_row))
                frame.close()

                app_obj.update_progress(self.current_row)
                
                self.current_row += speed
                
            app_obj.update_progress(self.current_row)
            
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
