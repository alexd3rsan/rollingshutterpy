''' lorem ipsum
'''
from tkinter.messagebox import showinfo
from threading import Thread
from PIL import Image, ImageDraw

class RollingShutter(object):
    ''' Class for simulating the 'Rolling-Shutter Effect'
    '''

    def __init__(self):
        ''' Initilaise empty class
        '''
        # Init empty containers
        self.thread = None
        self.speed = None
        self.path_output = None
        self.video_reader = None
        self.frame_count = 0
        self.size = None
        self.img_output = None
        self.quality = 0

        # Is the processing thread running
        self.running = False

        # Is the setup done
        self.setup_done = False

    def setup(self, video_reader, speed: int, path_output: str, quality=95):
        ''' Setup self for procesing
        '''
        self.speed = speed
        self.path_output = path_output

        self.video_reader = video_reader
        self.frame_count = len(video_reader)

        self.size = self.video_reader._meta['size']
        self.img_output = Image.new('RGB', self.size)
        self.quality = quality

        self.current_row = 0

        self.setup_done = True
    
    def set_preview_window(self, preview_window) -> None:
        ''' Set the preview window reference
        '''
        self.preview_window = preview_window
        
    def __processing_thread(self, main_window) -> None:
        ''' Process video in a separate thread
        '''
        
        # Don't do anything if the 'setup' methd hasn't been called
        if not self.setup_done:
            return
        
        w, h = self.size
        speed = self.speed
        
        self.running = True
          
        try:
            for frame in self.video_reader:
                cr = self.current_row
                frame = Image.fromarray(frame) # Convert to Pillow image

                new_line = frame.crop((0,cr,w,cr + speed))
                
                self.img_output.paste(new_line, (0, cr))

                # Show preview if the preview window is open
                if self.preview_window.open:
                    preview_frame = self.__make_preview_frame(frame)
                    try:
                        self.preview_window.update_image(preview_frame)
                    except:
                        pass
                
                frame.close()

                main_window.update_progress(cr)
                
                self.current_row += speed
                if self.current_row > h:
                    break
                
            self.img_output.save(self.path_output, quality=self.quality)
            
            main_window.progress_bar.state(['disabled'])
            main_window.enable_buttons()
            
            showinfo('Process Complete.', 'The shutter-rolled image has been created!')

        finally:
            self.running = False
            self.setup_done = False

            main_window.update_progress(0)
            main_window.progress_bar.state(['disabled'])
            main_window.enable_buttons()

    def __make_preview_frame(self,frame: Image) -> Image:
        '''Make a frame to display in preview window
        '''
        im = frame
        cr = self.current_row
        w, h = self.size
        speed = self.speed

        # Replace the top part of the frame with the output image
        top_part = (0,0,w,cr + speed)
        im.paste(self.img_output.crop(top_part), top_part)

        # Draw a line to show the current shutter position
        draw = ImageDraw.Draw(im)
        draw.line([(0, cr),(w,cr)], fill=128, width=speed)
        
        # convert back to RGB to draw
        im = im.convert('RGB')

        return im

    def start(self, main_window):
        '''Start processing the movie is a separate thread 
        '''
        self.thread = Thread(target=self.__processing_thread, args=(main_window,))
        self.thread.setDaemon(True)
        self.thread.start()
