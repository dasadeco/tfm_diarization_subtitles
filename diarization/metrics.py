from pyannote.core import Annotation, Segment
import argparse
import os
import logging
from datetime import datetime

RTTM = "rttm"
RTTM_REF = "rttm_ref"



def executeMetrics(metrics:list):
    for metric in metrics:
        pass    
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pyannote Metrics')
    parser.add_argument('-hp', '--hyphoteses_path', type=str, default='E:\Desarrollo\TFM\data\media\rttm', help='Path of the folder with hypotheses rttm files') 
    parser.add_argument('-rp', '--reference_path', type=str, default='E:\Desarrollo\TFM\subtitles\data\rttm_ref', help='Path of the folder with reference rttm files')     
    parser.add_argument('-me', '--metrics', type=list, help='List of Metrics to apply')
    args = parser.parse_args()
    
    files = []
    logs_path = os.path.join(args.hyphoteses_path, os.path.pardir, "logs")
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename=f'{logs_path}/metrics.log',
                        encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')            
    
    rttms_ref_path = os.path.join(args.reference_path)
    if os.path.exists(args.reference_path):
        ref_rttm_files = [ref_rttm_file for ref_rttm_file in os.listdir(args.reference_path) if ref_rttm_file.lower().endswith(".rttm")]
        logger.info("Rttm Ref files: {ref_rttm_files}")
    
    for folder in os.listdir(args.hyphoteses_path):
        folder_path = os.path.join(args.hyphoteses_path, folder)
        if os.path.isdir(folder_path):
            print(f"Processing folder: {folder_path}")
            logger.info(f"Processing folder: {folder_path}")
            for subfolder in os.listdir(folder_path):
                subfolder_path = os.path.join(folder_path, subfolder)
                print(f"Processing subfolder: {subfolder_path}")
                logger.info(f"Processing subfolder: {subfolder_path}")                
                for rttm_file in os.listdir(subfolder_path):
                    files.append(rttm_file)
                    #rttm_ref_file = rttms_ref_path.resolve(rttm_file)
                    if rttm_file in ref_rttm_files:
                        executeMetrics(args.metrics)
                    