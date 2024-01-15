from video_processor import VideoProcessor
import cv2
import numpy as np
from moviepy.editor import VideoFileClip

class TikTokProcessor(VideoProcessor):
    def __init__(self, video_url, template_heart, template_share, template_save):
        super().__init__(video_url)
        self.template_heart = template_heart
        self.template_share = template_share
        self.template_save = template_save

    def TK_Reels_Split(self, frame):
        """
        Processes a video frame to detect transitions based on template matching for heart, share, and save icons.
        
        Args:
            frame (numpy.ndarray): The current video frame.
        
        Returns:
            numpy.ndarray: The processed grayscale frame.
        """
        # Define color range for masking
        lower_color = np.array([220, 220, 220])
        upper_color = np.array([255, 255, 255])
        mask = cv2.inRange(frame, lower_color, upper_color)
        res = cv2.bitwise_and(frame, frame, mask=mask)

        # Convert to grayscale and apply morphological transformations
        gray_frame = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        gray_frame = cv2.morphologyEx(gray_frame, cv2.MORPH_CLOSE, kernel, iterations=1)

        # Template matching for heart, share, and save icons
        gray_frame, yCord = self.match_template(frame, gray_frame, self.template_heart,0.85)
        gray_frame, yCord2 = self.match_template(frame, gray_frame, self.template_share,0.85)
        gray_frame, yCord3 = self.match_template(frame, gray_frame, self.template_save,0.85)

        # Calculate end time and check for sufficient gaps between transitions
        # current_frame_number = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        # end_time = current_frame_number / self.fps
        end_time = timestamp_ms = float(self.cap.get(cv2.CAP_PROP_POS_MSEC) + ((1.5*1000.0) / self.fps))/ 1000.0
        # enoughGaps = (end_time - self.start_time > 1)
        enoughGaps = (end_time - self.start_time > 0.4)

        # Define thresholds for detecting transitions
        heartThreshold = yCord is not None and (yCord <= gray_frame.shape[0] / 2 or yCord > (gray_frame.shape[0] - gray_frame.shape[0] / 6.3))
        shareThreshold = yCord2 is not None and (yCord2 <= gray_frame.shape[0] / 1.6 or yCord2 > (gray_frame.shape[0] - gray_frame.shape[0] / 6.3))
        saveThreshold = yCord3 is not None and (yCord3 <= gray_frame.shape[0] / 1.7  or yCord3 > (gray_frame.shape[0] - gray_frame.shape[0] / 6.3))


        # Check if a transition is detected
        if enoughGaps and (heartThreshold or shareThreshold or saveThreshold):
            minutes = int(end_time // 60)
            seconds = int(end_time % 60)
            print(f"{self.part_counter})transition detected at {minutes}:{seconds} ---{gray_frame.shape[0]-gray_frame.shape[0]/2.5} < {yCord} <{ gray_frame.shape[0]/2.5} --- {gray_frame.shape[0]-gray_frame.shape[0]/4.85} < {yCord2} <{ gray_frame.shape[0]/2} --- {gray_frame.shape[0]-gray_frame.shape[0]/3.7} < {yCord3} <{ gray_frame.shape[0]/2}")


            # Release the current video writer and start a new one
            # segment 
            # video_segment = self.video.subclip(self.start_time, end_time)
            # video_segment.write_videofile(f'{self.output_dir}/part_{self.part_counter}.mp4', codec='libx264')

            self.split_video(self.video_url, self.start_time, end_time, f'{self.output_dir}/part_{self.part_counter}.mp4')
            print(self.start_time, end_time)

            self.part_counter += 1
            self.start_time = end_time


        return frame

    def process_frame(self, frame):
        """
        Processes each frame of the video.
        
        Args:
            frame (numpy.ndarray): The current video frame.
        
        Returns:
            tuple: The processed frame and None.
        """
        frame = self.TK_Reels_Split(frame)
        return frame, None
