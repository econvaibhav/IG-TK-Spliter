import cv2
import numpy as np
import os
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import ffmpeg
# _________________________________ Parent Class ______________________________________
class VideoProcessor:
    def __init__(self, video_url):
        
        self.video_url = video_url
        self.video = VideoFileClip(video_url)

        self.cap = cv2.VideoCapture(video_url)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.fps  

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.new_height = 960

        self.aspect_ratio = self.width / self.height
        self.new_width = int(self.new_height * self.aspect_ratio)
        self.frame_counter = 0
        self.part_counter = 1
        self.start_time = 0



        
        # Create a directory based on the video URL
        self.output_dir = self.sanitize_filename(video_url)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        print(self.fps)

    def sanitize_filename(self, filename):
        return filename.split('.mp4')[0]
        # return filename.split('/')[-1].split('.mp4')[0]

    # def split_video(self,input_file, start_time, end_time, output_file):
    #     ffmpeg_extract_subclip(input_file, 10, 20, targetname=output_file)
    




    def split_video(self, input_file, start_time, end_time, output_file):
        # Check if the output file already exists
        if os.path.exists(output_file):
            print(f"File {output_file} already exists. Skipping splitting.")
            return

        # Run the FFmpeg command and capture stderr
        # try:
        out, err = (
            ffmpeg
            .input(input_file, ss=start_time, to=end_time)
            .output(output_file, acodec='aac', strict='experimental', audio_bitrate='192k')
            .run(capture_stdout=True, capture_stderr=True)
        )
        print(f"File {output_file} created successfully.")
        # except ffmpeg.Error as e:
        #     print('An error occurred:')
        #     print('Saving video only without audio...')
        #     (
        #         ffmpeg
        #         .input(input_file, ss=start_time, to=end_time)
        #         .output(output_file,  c='copy', an=None)  
        #         .run(capture_stdout=True, capture_stderr=True)
        #     )



    def match_template(self, frame, gray_frame, template, threshold=0.90):
        w, h = template.shape[::-1]
        res = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        first_y = None
        if np.any(res >= threshold):
            for pt in zip(*loc[::-1]):
                cv2.rectangle(gray_frame, pt, (pt[0] + w, pt[1] + h), (255, 255, 255), 2)
                # cv2.rectangle(frame, pt, (pt[0] + w, pt[1] + h), (0, 255, 0), 2)
                if first_y is None and pt[0] > 360:
                    first_y = pt[1]
    

        return gray_frame, first_y

    def process_frame(self, frame):
        raise NotImplementedError("Subclasses should implement this method")

    def process_video(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                end_time = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                self.split_video(self.video_url, self.start_time,self.duration, f'{self.output_dir}/part_{self.part_counter}.mp4')

                os.remove(self.video_url) 
                break

            frame = cv2.resize(frame, (self.new_width, self.new_height))
            frame1,frame2 = self.process_frame(frame)
            self.frame_counter+=1


        self.cap.release()


