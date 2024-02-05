from instagram_processor import InstagramProcessor
from tiktok_processor import TikTokProcessor
import cv2

from tqdm import tqdm
import os
import shutil
import pandas as pd

# # # # Example usage
# video_url = 'video_IG2.mp4'


# For Instagram
def instagram_wrapper(video_url):
    template_heart = cv2.imread('IG_heart_template.png', 0)
    template_comment = cv2.imread('IG_comment_template.png', 0)
    template_share = cv2.imread('IG_share_template.png', 0)

    ig_processor = InstagramProcessor(video_url, template_heart, template_comment, template_share)
    ig_processor.process_video()


# # For TikTok
# video_url = 'video_TK.mp4'

def tiktok_wrapper(video_url):
    template_heart = cv2.imread('TK_heart_template.png', 0)
    template_share = cv2.imread('TK_share_template.png', 0)
    template_save = cv2.imread('TK_save_template.png', 0)

    tk_processor = TikTokProcessor(video_url, template_heart, template_share, template_save)
    tk_processor.process_video()


def split_video_wrapper(folder_path):
    all_files = [ "/scratch/project_2009497/MobileBackup/Finland/FI2/Synthetic/Instagram/az_recorder_20240613_163541.mp4", "/scratch/project_2009497/MobileBackup/Finland/FI2/Synthetic/Instagram/az_recorder_20240609_183757.mp4", "/scratch/project_2009497/MobileBackup/Finland/FI2/Organic/Tiktok/az_recorder_20240615_192852.mp4", "/scratch/project_2009497/MobileBackup/Finland/FI2/Organic/Tiktok/az_recorder_20240613_165230.mp4", "/scratch/project_2009497/MobileBackup/Finland/FI2/Organic/Instagram/az_recorder_20240615_194238.mp4", "/scratch/project_2009497/MobileBackup/Finland/FI2/Organic/Instagram/az_recorder_20240609_191229.mp4", "/scratch/project_2009497/MobileBackup/Finland/FI2/Organic/Instagram/az_recorder_20240610_223541.mp4"]

    # # Walk through the directory tree
    # for root, dirs, files in os.walk(folder_path):
    #     for file in files:
    #         file_name = os.path.join(root, file)
    #         file_name_list = file_name.split('/')  
    #         account_type = file_name_list[-2]
    #         if account_type == 'Instagram' or account_type == 'Tiktok':
    #             all_files.append(file_name)
    # file_type_dic = {}


    for file_name in tqdm(all_files):
        file_name_list = file_name.split('/')  
        account_type = file_name_list[-2]
        
        if account_type== 'Instagram':
            print(file_name,account_type)
            instagram_wrapper(file_name)

        elif account_type == 'Tiktok':
            print(file_name,account_type)
            tiktok_wrapper(file_name)



# folder_path = "/scratch/project_2009497/GrapheneOS/Sweden/SE1"
conutry_code_dic ={
'Bulgaria':'BG',
# 'Croatia':'HR',
# 'Finland':'FI',
# 'France':'FR',
# 'Germany':'DE',
# 'Hungary':'HU',
# 'Poland':'PL',
# 'Portugal':'PT',
# 'Spain':'ES',
# 'Sweden':'SE'
}



# for country in conutry_code_dic.keys():
#     for i in range(1):
#         print('/scratch/project_2009497/MobileBackup/'+country+'/'+conutry_code_dic[country]+str(i+1))
#         folder_path = '/scratch/project_2009497/MobileBackup/'+country+'/'+conutry_code_dic[country]+str(i+1)
split_video_wrapper('folder_path')