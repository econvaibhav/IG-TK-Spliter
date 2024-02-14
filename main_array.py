from instagram_processor import InstagramProcessor
from tiktok_processor import TikTokProcessor
import cv2

from tqdm import tqdm
import os
import shutil
import pandas as pd
import json
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


def generate_file_list(folder_path, output_file):
    all_files = []

    # Walk through the directory tree
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_name = os.path.join(root, file)
            file_name_list = file_name.split('/')  
            account_type = file_name_list[-2]
            
            if (account_type == 'Instagram' or account_type == 'Tiktok') and (file_name_list[-3] !='Others'):
                all_files.append(file_name)

    # Save the list to a file
    with open(output_file, 'w') as f:
        json.dump(all_files, f)


def process_video(file_list_path):
    # Load the list of files
    with open(file_list_path, 'r') as f:
        all_files = json.load(f)
    # print(len(all_files))
    # Get the SLURM_ARRAY_TASK_ID environment variable
    task_id = int(os.getenv('SLURM_ARRAY_TASK_ID')) - 1

    # Ensure the task_id is within the range of all_files
    if task_id < len(all_files):
        file_name = all_files[task_id]
        file_name_list = file_name.split('/')  
        account_type = file_name_list[-2]
        print(f"Task ID {task_id + 1} : {file_name}-> {account_type}")
    
        if account_type == 'Instagram':
            # print(file_name, account_type)
            instagram_wrapper(file_name)

        elif account_type == 'Tiktok':
            # print(file_name, account_type)
            tiktok_wrapper(file_name)
    else:
        print(f"Task ID {task_id + 1} is out of range for the list of files.")



# folder_path = "/scratch/project_2009497/GrapheneOS/Sweden/SE1"
# conutry_code_dic ={
# 'Bulgaria':'BG',
# # 'Croatia':'HR',
# # 'Finland':'FI',
# # 'France':'FR',
# # 'Germany':'DE',
# # 'Hungary':'HU',
# # 'Poland':'PL',
# # 'Portugal':'PT',
# # 'Spain':'ES',
# # 'Sweden':'SE'
# }

# generate_file_list('/scratch/project_2009497/MobileBackup/Finland', 'Finland.txt')
# generate_file_list('/scratch/project_2009497/MobileBackup/Germany', 'France.txt')
process_video('Spain.txt')

# for country in conutry_code_dic.keys():
#     for i in range(1):
#         print('/scratch/project_2009497/MobileBackup/'+country+'/'+conutry_code_dic[country]+str(i+1))
#         folder_path = '/scratch/project_2009497/MobileBackup/'+country+'/'+conutry_code_dic[country]+str(i+1)
#         split_video_wrapper(folder_path)