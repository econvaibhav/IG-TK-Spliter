from video_processor import VideoProcessor
import cv2
import numpy as np
from moviepy.editor import VideoFileClip
import os
from moviepy.video.io.VideoFileClip import VideoFileClip
import math
import subprocess
import datetime

#_________________________________ Instagram__________________________________________________________________
class InstagramProcessor(VideoProcessor):
    def __init__(self, video_url, template_heart, template_comment, template_share):
        """
        Initializes the InstagramProcessor with video URL and templates for heart, comment, and share icons.
        
        Args:
            video_url (str): URL of the video to be processed.
            template_heart (numpy.ndarray): Template image for the heart icon.
            template_comment (numpy.ndarray): Template image for the comment icon.
            template_share (numpy.ndarray): Template image for the share icon.
        """
        super().__init__(video_url)
        self.template_heart = template_heart
        self.template_comment = template_comment
        self.template_share = template_share





    def IG_Reels_Split(self, frame):
        """
        Processes a video frame to detect transitions based on template matching for heart, comment, and share icons.
        
        Args:
            frame (numpy.ndarray): The current video frame.
        
        Returns:
            numpy.ndarray: The processed frame.
        """
        frame_save = frame.copy() # version to be saved

        # Define color range for masking
        lower_color = np.array([230, 230, 230])
        upper_color = np.array([255, 255, 255])
        mask = cv2.inRange(frame, lower_color, upper_color)
        res = cv2.bitwise_and(frame, frame, mask=mask)

        # Convert to grayscale and apply morphological transformations
        gray_frame = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        gray_frame = cv2.morphologyEx(gray_frame, cv2.MORPH_CLOSE, kernel, iterations=1)

        # Filling the countours found so we have complete symbols to detect
        contours, _ = cv2.findContours(gray_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            epsilon = 0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            if cv2.contourArea(cnt) > 50:
                cv2.drawContours(gray_frame, [approx], 0, (255, 255, 255), -1)

        # Template matching for heart, comment, and share icons
        gray_frame, yCord = self.match_template(frame, gray_frame, self.template_heart, 0.85)
        gray_frame, yCord2 = self.match_template(frame, gray_frame, self.template_comment, 0.85)
        gray_frame, yCord3 = self.match_template(frame, gray_frame, self.template_share,0.85)


        current_frame_number = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
        # end_time = current_frame_number / self.fps
        end_time = timestamp_ms = float(self.cap.get(cv2.CAP_PROP_POS_MSEC) + ((1.5*1000.0) / self.fps))/ 1000.0
        enough_gaps = (end_time - self.start_time > 0.4)
        # Define thresholds for detecting transitions
        heart_threshold = yCord is not None and (90 < yCord < 860) and (yCord < gray_frame.shape[0] / 3 or yCord > (gray_frame.shape[0] - gray_frame.shape[0] / 6.3) )
        comment_threshold = yCord2 is not None and (90 < yCord2 < 860) and (yCord2 < gray_frame.shape[0] / 3 or yCord2 > (gray_frame.shape[0] - gray_frame.shape[0] / 6.3))
        share_threshold = yCord3 is not None and (90 < yCord3 < 860) and (yCord3 < gray_frame.shape[0] / 3  or yCord3 > (gray_frame.shape[0] - gray_frame.shape[0] / 6.3))

        # Check if a transition is detected
        # print(f"Start time: {self.start_time}, End time: {end_time}, -- self.fps: {self.fps}, {1000.0 / (2*self.fps)}")
        if enough_gaps and (heart_threshold or comment_threshold or share_threshold):
            minutes = int(end_time // 60)
            seconds =  end_time % 60
            print(f"{self.part_counter})transition detected at {minutes}:{seconds} ---{gray_frame.shape[0]-gray_frame.shape[0]/3.5} < {yCord} <{ gray_frame.shape[0]/2} --- {gray_frame.shape[0]-gray_frame.shape[0]/4.6} < {yCord2} <{ gray_frame.shape[0]/2} --- {gray_frame.shape[0]-gray_frame.shape[0]/6} < {yCord3} <{ gray_frame.shape[0]/2}")


            # segment 

            # Calculate end time and check for sufficient gaps between transitions
            # print(current_frame_number,self.frame_counter,self.fps)
            # print(self.start_time, end_time)

            # cv2.imwrite(f'frame_{self.part_counter}.jpg', frame)

            
            # video_segment = self.video.subclip(self.start_time, end_time)
            # video_segment.write_videofile(f'{self.output_dir}/part_{self.part_counter}.mp4', codec='libx264')
            
            self.split_video(self.video_url, self.start_time,end_time, f'{self.output_dir}/part_{self.part_counter}_reel.mp4')
            self.part_counter += 1
            self.start_time = end_time


        return frame


    def IG_Videos_Split(self, frame):
        """
        Processes a video frame to detect transitions based on edge detection and contour analysis.
        
        Args:
            frame (numpy.ndarray): The current video frame.
        
        Returns:
            numpy.ndarray: The processed frame.
        """
        
        frame_save = frame.copy() # version to be saved

        # Draw white lines on the frame
        # cv2.line(frame, (0, 0), (0, self.new_height), (255, 255, 255), 2)
        # cv2.line(frame, (self.new_width, 0), (self.new_width, self.new_height), (255, 255, 255), 2)

        # Define color range for masking
        lower_color = np.array([250, 250, 250])
        upper_color = np.array([255, 255, 255])
        mask = cv2.inRange(frame, lower_color, upper_color)
        res = cv2.bitwise_and(frame, frame, mask=mask)

        # Convert to grayscale, blur, and detect edges
        # gray_frame = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
        # blurred = cv2.GaussianBlur(gray_frame, (5, 5), 0)
        # edges = cv2.Canny(blurred, 50, 150)
        # dilated = cv2.dilate(edges, None, iterations=2)
        # eroded = cv2.erode(dilated, None, iterations=2)

        # Convert to grayscale and apply morphological transformations
        gray_frame = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        gray_frame = cv2.morphologyEx(gray_frame, cv2.MORPH_CLOSE, kernel, iterations=1)

        # Filling the countours found so we have complete symbols to detect
        contours, _ = cv2.findContours(gray_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            epsilon = 0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            if cv2.contourArea(cnt) > 50:
                cv2.drawContours(gray_frame, [approx], 0, (255, 255, 255), -1)

        dilated = cv2.dilate(gray_frame, None, iterations=2)
        eroded = cv2.erode(dilated, None, iterations=2) 
        # Invert the colors
        cv2.line(eroded, (0, 0), (0, self.new_height), (255, 255, 255), 2)
        cv2.line(eroded, (self.new_width, 0), (self.new_width, self.new_height), (255, 255, 255), 2)
        eroded = cv2.bitwise_not(eroded)






        # Calculate end time and convert to minutes and seconds
                # Calculate end time and check for sufficient gaps between transitions
        current_frame_number = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        # end_time = current_frame_number / self.fps
        end_time = timestamp_ms = float(self.cap.get(cv2.CAP_PROP_POS_MSEC) + ((1.5*1000.0) / self.fps))/ 1000.0 
        minutes = int(end_time // 60)
        seconds = int(end_time % 60)

        # Find contours and check for transitions
        contours, _ = cv2.findContours(eroded.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * peri, True)

            if len(approx) == 4:
                (x, y, w, h) = cv2.boundingRect(approx)

                if w > self.new_width - 20:
                    # cv2.drawContours(frame, [approx], -1, (0, 255, 0), 2)

                    if (end_time - self.start_time > 1) and 45 <= y <= 120 and 150<= h <= 200:
                        print(f"{self.part_counter}) transition detected at {minutes}:{seconds} --- y == {y}  --- h < {h}")
                        # segment 
                        
                        # video_segment = self.video.subclip(self.start_time, end_time)
                        # video_segment.write_videofile(f'{self.output_dir}/part_{self.part_counter}.mp4', codec='libx264')
                        
                        self.split_video(self.video_url, self.start_time,end_time, f'{self.output_dir}/part_{self.part_counter}_video.mp4')
                        self.part_counter += 1
                        self.start_time = end_time

        return frame

    def process_frame(self, frame):
        """
        Processes each frame of the video using IG_Reels_Split and IG_Videos_Split methods.
        
        Args:
            frame (numpy.ndarray): The current video frame.
        
        Returns:
            tuple: The processed frames from IG_Reels_Split and IG_Videos_Split.
        """
        frame_save = frame.copy()
        frame1 = self.IG_Reels_Split(frame)

        frame= frame_save
        frame2 = self.IG_Videos_Split(frame)
        return frame1, frame2
