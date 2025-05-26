from pyannote.core import Annotation, Segment
import argparse
import os

RTTM = "rttm"
RTTM_REF = "rttm_ref"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pyannote Metrics')
    parser.add_argument('-hp', '--hyphoteses_path', type=str, default='E:\Desarrollo\TFM\data\media\rttm', help='Path of the folder with hypotheses rttm files') 
    parser.add_argument('-rp', '--reference_path', type=str, default='E:\Desarrollo\TFM\subtitles\data\rttm_ref', help='Path of the folder with reference rttm files')     
    args = parser.parse_args()
    
    ##rttms_parent_path = os.path.join(args.volume_path, RTTM)
    for folder in os.listdir(args.hyphoteses_path):
        folder_path = os.path.join(args.hyphoteses_path, folder)
        if os.path.isdir(folder_path):
            print(f"Processing folder: {folder_path}")
    
    