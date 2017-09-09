''' lorem ipsum
'''

from PIL import Image, ImageDraw, ImageFilter
import math
import numpy as np

class SimpleFanRenderer():
    ''' Create a series of frames of a rotating fan
    '''
    def __init__(self,speed: float, n: int, image_size=128, ratio=0.7):
        self.speed = speed # full rotations per height of the image
        self.image_size = image_size # Image size in pixels (images are square)
        self.fan_radius = self.image_size * max(0, min(ratio, 1)) / 2
        self.current = 1
        self.phase = 0
        self.center = self.image_size / 2 # Center of the image

        self.init_blades(n)

        # Figure out how much to move on each step
        self.delta_angle = 2*math.pi/(self.image_size-1)*self.speed

    def init_blades(self,n: int) -> None:
        ''' Initialise fan blades
        '''
        r = self.fan_radius
        pt = self.__absolute_coords((0,r))
        p = self.phase

        if n == 1:
            self.blades = (self.__rotate_point(pt,p),)
        else:
            angles = (0 + i*(2*math.pi)/(n) for i in range(0,n)) # Uniformly distributed blade angles
            self.blades = tuple((self.__rotate_point(pt,p+angle) for angle in angles))

    def step_blades(self) -> None:
        ''' Apply a timestep to baldes based on speed
        '''
        angle = self.delta_angle
        self.blades = tuple((self.__rotate_point(blade,angle) for blade in self.blades))

    def __rotate_point(self,point,angle):
        ''' Rotates 'point' by 'angle' counterclockwise about self.center
        '''
        x, y = self.__relative_coords(point)
        # http://en.wikipedia.org/wiki/Rotation_(mathematics)#Two_dimensions
        x_rot = x * math.cos(angle) - y * math.sin(angle)
        y_rot = x * math.sin(angle) + y * math.cos(angle)

        x, y = self.__absolute_coords((x_rot,y_rot))
        return x, y
    
    def __relative_coords(self,point):
        ''' Changes 'point' into relative coords
        '''
        return tuple((i - self.center for i in point))

    def __absolute_coords(self,point):
        ''' Changes 'point' into absolute coords
        '''
        return tuple((i + self.center for i in point))
    
    def __next__(self):
        ''' Method used by the loops for iteration
        '''
        if self.current > self.image_size:
            raise StopIteration
        else: # Render the crrent frame
            s = self.image_size
            c = self.center
            
            frame = Image.new('RGB',(s,s),color=(255,255,255))
            
            # Draw all the baldes
            draw = ImageDraw.Draw(frame)
            for blade in self.blades: draw.line((c,c) + blade,fill=(0,0,0),width=3)

            # Apply small blur to the frame
            #frame = frame.filter(ImageFilter.GaussianBlur(radius=0.5))

            # Rotate the blades to the next position
            self.step_blades()
            self.current += 1

            return frame

    def __iter__(self):
        ''' Iterator object declaration
        '''
        return self

def image_to_array(image):
    ''' Converts image to numpy array
    '''        
    im_arr = np.fromstring(image.tobytes(), dtype=np.uint8)
    im_arr = im_arr.reshape((image.size[1], image.size[0], 3))                                   
    return im_arr

def main():
    import imageio

    speed = 5
    blades = 7
    size = 512

    sfr = SimpleFanRenderer(speed,blades,image_size=size)
    directory = '/Users/marcink/Desktop/temp/'
    fps = 30

    filename = 'simple_fan_{}_{}_{}.mp4'.format(speed,blades,size)

    #params1 = ['-c:v r10k']
    #params2 = ['-c:v huffyuv -c:a libmp3lame -b:a 320k']
    writer = imageio.get_writer(filename, fps=fps)#, ffmpeg_params=params1)

    for frame in sfr:
        writer.append_data(image_to_array(frame))
    writer.close()

if __name__ == '__main__': main()
