''' lorem ipsum
'''
from tkinter.messagebox import showinfo
from threading import Thread
from PIL import Image, ImageDraw
from math import ceil

import time

class RollingShutter(object):
    ''' Class for simulating the 'Rolling-Shutter Effect'
    '''

    def __init__(self):
        ''' Initilaise empty class
        '''        
        # Is the setup done
        self.setup_done = False

    def setup(self, video_reader, speed: int, quality=95):
        '''
        Setup self for procesing. Having setup separate allows one to initialises the class
        without having to have an instance of the video_reader on hand
        '''
        self.speed = speed
        self.video_reader = video_reader

        self.size = self.video_reader._meta['size']
        
        # Minimum of the number of frames in the video_reader and expected number of slices
        #self.frame_count = min(len(video_reader), int(ceil(float(self.size[1])/speed)))
        self.frame_count = len(video_reader)

        self.quality = quality
        self.rolledImage = Image.new('RGBA', self.size, color=0)

        self.current_row = 0
        self.current_frame = 0

        self.setup_done = True

    def __iter__(self):
        ''' Declare iterable object
        '''
        return self
    
    def __next__(self):
        ''' Return next element of iteration
        '''
        w, h = self.size
        speed = self.speed
        cr = self.current_row

        if cr > h:
            self.setup_done = False
            raise StopIteration
        elif self.current_frame < self.frame_count:
            # Read the next frame
            frame = self.video_reader.get_next_data()
            frame = Image.fromarray(frame, mode='RGB') # Convert to Pillow image
            self.current_frame += 1

            # Get the next line from it
            new_line = frame.crop((0, cr, w, h)) 
            new_line = new_line.convert('RGBA')

            # Paste into the rolledImage
            self.rolledImage.paste(new_line, (0, cr), new_line)
        else:
            # It does not work without sleep because Tkinter is not threading safe
            # In principle it should be done with queues but too much effort for a time beeing
            time.sleep(0.01) # 10 ms

        self.current_row += speed
        return self.rolledImage

    def process(self):
        for image in self:
            pass # Process self
        return image

class TkinterRollingShutter(RollingShutter):
    ''' Rolling shutter class with bells and whistles for the use of the Tkinter interface
    '''
    def __init__(self, main_window):
        ''' Require main_window object on init
        '''
        RollingShutter.__init__(self)

        # Is the processing thread running
        self.running = False

        # Tkinter window hooks
        self.main_window = main_window
        self.preview_window = None
    
    def setup(self, video_reader, speed: int, path_output: str, quality=95):
        ''' Output the image to path after done
        '''
        RollingShutter.setup(self, video_reader, speed, quality=95)
        self.path_output = path_output

    def __processing_thread(self) -> None:
        ''' Process video in a separate thread
        '''
        w, h = self.size
        speed = self.speed
        
        self.running = True
        try:
            for frame in self:
                # Show preview if the preview window is open
                if self.preview_window and self.preview_window.open:
                    preview_frame = self.__make_preview_frame(frame)
                    self.preview_window.update_image(preview_frame)

                self.main_window.update_progress(self.current_row)

            self.rolledImage.save(self.path_output, quality=self.quality)
            showinfo('Process Complete.', 'The shutter-rolled image has been created!')

        finally:
            self.setup_done = False
            self.main_window.update_progress(0)
            self.main_window.progress_bar.state(['disabled'])
            self.main_window.enable_buttons()

            self.running = False
            self.thread = None

    def __make_preview_frame(self, frame: Image) -> Image:
        ''' Make a frame to display in preview window
        '''
        cr = self.current_row
        w, h = self.size
        speed = self.speed

        # Draw a line to show the current shutter position
        preview_image = frame.copy()
        draw = ImageDraw.Draw(preview_image)
        draw.line([(0, cr), (w, cr)], fill=128, width=speed)
        
        # Convert to RGB to draw
        return preview_image.convert('RGB')

    def set_preview_window(self, preview_window) -> None:
        ''' Set the preview window reference
        '''
        if self.main_window:
            self.preview_window = preview_window

    def start(self):
        '''
        Start processing the movie is a separate thread
        Don't do anything if the 'setup' method hasn't been called
        '''
        if not self.setup_done: 
            return

        self.thread = Thread(target=self.__processing_thread)
        self.thread.setDaemon(True)
        self.thread.start()

    def wait(self):
        ''' Wait for self to finish
        '''
        if self.thread:
            self.thread.join()