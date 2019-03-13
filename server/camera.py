from time import time

class Camera(object):
    last_access = 0    # static variable in class
    def __init__(self):
        self.frames = [open(f + '.jpg', 'rb').read() for f in ['1', '2', '3']]

    def get_frame(self):
        # Camera.last_access = time.time()
        return self.frames[int(time()) % 3]