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
    
    files = []
    rttms_ref_path = os.path.join(args.reference_path)
    for folder in os.listdir(args.hyphoteses_path):
        folder_path = os.path.join(args.hyphoteses_path, folder)
        if os.path.isdir(folder_path):
            print(f"Processing folder: {folder_path}")
            for subfolder in os.listdir(folder_path):
                subfolder_path = os.path.join(folder_path, subfolder)
                for rttm_file in os.listdir(subfolder_path):
                    files.append(rttm_file)
                    rttm_ref_file = rttms_ref_path.resolve(rttm_file)
                    