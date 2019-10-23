import cv2
import numpy as np
import time
import threading
import queue
from tx2_config import qsize
import math

class VideoStream(threading.Thread):

    def __init__(self, url, pos, parent, frame_q, resolution=(360, 640), threaded=False):
        super(VideoStream, self).__init__()
        self.cam = cv2.VideoCapture(url)
        self.pos = pos
        self.parent = parent
        self.url = url
        self.resolution = resolution
        self.threaded = threaded
        self.emptyframe = self.make_empty_frame()
        self.num_empty_frames = 0
        self.frame_q = frame_q
        self.stoprequest = threading.Event()
        self.daemon = True

    def __repr__(self):
        return "VideoStream object at url: {}".format(self.url)

    def make_empty_frame(self):
        frame=np.zeros((*self.resolution, 3), dtype=np.uint8)
        empty_msg='Cannot read camera at {}'.format(self.url)
        cv2.putText(frame, empty_msg, (50, 50),cv2.FONT_HERSHEY_COMPLEX, 0.6, (255, 255, 255))
        return frame

    def read(self, framebuffer, threaded=False):

        ret, frame = self.cam.read()

        if ret:
            this_frame = frame
        else:
            self.num_empty_frames += 1
            this_frame = self.emptyframe
            if self.num_empty_frames >= 10:
                self.reset()

        if self.threaded:
            return this_frame

        else:
            
            #TODO
            # numframes = self.parent.num_frames
            
            #for x in range(numframes +1):
                
            
            if self.pos == 1:
                framebuffer[:self.resolution[0],
                            :self.resolution[1]] = this_frame

            elif self.pos == 2:
                framebuffer[:self.resolution[0],
                            self.resolution[1]:] = this_frame
            elif self.pos == 3:
                framebuffer[self.resolution[0]:,
                            :self.resolution[1]] = this_frame
            elif self.pos == 4:
                framebuffer[self.resolution[0]:,
                            self.resolution[1]:] = this_frame

    def cleanup(self):
        self.cam.release()

    def reset(self):
        self.cleanup()
        self.cam = cv2.VideoCapture(self.url)
        self.num_empty_frames = 0
        print(self.__repr__(), ' was reset')

    def run(self):
        print('Running stream for ', self.__repr__())
        if self.threaded:
            while not self.stoprequest.isSet():
                # framebuffer is just a dummy here
                frame = self.read(0, threaded=True)
                if self.frame_q.full():
                    _ = self.frame_q.get_nowait()
                # this will never raise an exception
                self.frame_q.put_nowait(frame)
                # if this thread is the only producer using this queue

    def join(self, timeout=None):
        self.stoprequest.set()
        self.cleanup()
        super(VideoStream, self).join(timeout)


class VideoStreamHandler(object):

    def __init__(self, cam_urls, threaded=False, resolution=(360, 640)):
        
        self.threaded = threaded
        self.resolution = resolution
        self.urls = []
        self.queue = []
        self.streams =[]
        self.emptyframes = []

        index = 0
        for it in cam_urls:
            self.urls.append(it)
            self.queue.append( self.setup_queue() )
            self.streams.append( self.setup_stream(index) )
            self.emptyframes.append(self.streams[index].emptyframe)
            index = index+1
        self.num_frames = index
        
        self.framebuffer = np.zeros(
            ( math.floor( math.sqrt (self.num_frames) ) * resolution[0], math.ceil( math.sqrt (self.num_frames) )  * resolution[1], 3), dtype=np.uint8)
        
        if self.threaded:
            self.start_streams()

    def setup_stream(self, index):
        return VideoStream(self.urls[index], index , self.queue[index],
                              self.resolution, self.threaded)

    def setup_queue(self):
        if self.threaded:
            return queue.Queue(maxsize=qsize)
        else:
            return None

    def start_streams(self):
        for stream in self.streams:
            stream.start()

    def join_streams(self):
        for stream in self.streams:
            stream.join()


    def read_streams(self):
        if self.threaded:
            
            index = 1
            for q in self.queue:
                self.read_queue(q,index)
                index = index + 1
        else:
            
            for stream in self.streams:
                stream.read(self.framebuffer)

        return self.framebuffer

    def read_queue(self, q, pos):
        if q.empty():
            frame=self.emptyframes[pos-1]
        else:
            frame = q.get_nowait()  # this will never raise an exception
            # if this thread is the only consumer using this queue

        if pos == 1:
            self.framebuffer[:self.resolution[0], :self.resolution[1]] = frame
        elif pos == 2:
            self.framebuffer[:self.resolution[0], self.resolution[1]:] = frame
        elif pos == 3:
            self.framebuffer[self.resolution[0]:, :self.resolution[1]] = frame
        elif pos == 4:
            self.framebuffer[self.resolution[0]:, self.resolution[1]:] = frame

    def run(self):
        while not self.stoprequest.isSet():
            frame1 = self.read_queue(self.q1)
            frame2 = self.read_queue(self.q2)
            frame3 = self.read_queue(self.q3)
            frame4 = self.read_queue(self.q4)
            self.framebuffer[:self.resolution[0], :self.resolution[1]] = frame1
            self.framebuffer[:self.resolution[0], self.resolution[1]:] = frame2
            self.framebuffer[self.resolution[0]:, :self.resolution[1]] = frame3
            self.framebuffer[self.resolution[0]:, self.resolution[1]:] = frame4

    def close(self):
        self.s1.cleanup()
        self.s2.cleanup()
        self.s3.cleanup()
        self.s4.cleanup()


def main():
    fps = 0
    url1 = 'http://pi1.local:8000/stream.mjpg'
    url2 = 'http://pi2.local:8000/stream.mjpg'
    url3 = 'http://pi3.local:8000/stream.mjpg'
    url4 = 'http://pi4.local:8000/stream.mjpg'

    stream_handler = VideoStreamHandler(
        [url1, url2, url3, url4],threaded=False, resolution=(360, 640))

    tic = time.time()
    while True:
        frame = stream_handler.read_streams()
        toc = time.time()
        fps = 0.9 * fps + 0.1 / (toc - tic)
        tic = time.time()
        fps_text = 'FPS:{:.2f}'.format(fps)
        font = cv2.FONT_HERSHEY_PLAIN
        line = cv2.LINE_AA
        cv2.putText(frame, fps_text, (20, 60), font,
                    4.0, (255, 255, 255), 4, line)
        cv2.imshow('Streams', frame)
        k = cv2.waitKey(1)

        if k == ord('q'):
            break


if __name__ == '__main__':
    main()
