from enum import Enum
from io import FileIO

from pyannote.core import Annotation, Segment
import argparse
import os
import logging
from datetime import datetime
import math
from pyannote.metrics.diarization import DiarizationErrorRate

RTTM = "rttm"
RTTM_REF = "rttm_ref"

logger = None
map_results = {}

class Metrics(Enum):
  DER = "DER"
  IER = "IER"
  Cobertura = "Cobertura"

  
def executeMetrics(metrics:list, subfolder_path, rttms_ref_path, rttm_file):
      
    def _create_annot(file:FileIO, annot:Annotation)->Annotation:              
      for line in file:
        if line.strip() != "":
            data_list = line.split(" ")
            annot[Segment( math.trunc(float(data_list[3])*100), 
                        math.trunc(float(data_list[3])*100) + 
                        math.trunc(float(data_list[4])*100))] = data_list[7]
      return annot
                      

    hyp_rttm_file_path = os.path.join(subfolder_path, rttm_file)
    ref_rttm_file_path = os.path.join(rttms_ref_path, rttm_file)
    hypothesis = Annotation(rttm_file, os.path.basename(subfolder_path))
    with open(hyp_rttm_file_path, 'r') as hyp_file:
        hypothesis = _create_annot(hyp_file, hypothesis)
    hyp_file.close()    
        
    reference = Annotation(rttm_file, RTTM_REF)
    with open(ref_rttm_file_path, 'r') as ref_file:
        reference = _create_annot(ref_file, reference)
    ref_file.close()    
                                      
    for metric in metrics:        
        if metric.strip() == Metrics.DER or metric.strip() == Metrics.DER.value:
            der_metric = DiarizationErrorRate()                 
            map_results[ref_rttm_file_path] = der_metric(reference, hypothesis)     
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pyannote Metrics')
    parser.add_argument('-hp', '--hyphoteses_path', type=str, default='E:\Desarrollo\TFM\data\media\rttm', help='Path of the folder with hypotheses rttm files') 
    parser.add_argument('-rp', '--reference_path', type=str, default='E:\Desarrollo\TFM\subtitles\data\rttm_ref', help='Path of the folder with reference rttm files')     
    parser.add_argument('-me', '--metrics', type=str, help='List of Metrics to apply')
    args = parser.parse_args()
    
    files = []
    logs_path = os.path.join(args.hyphoteses_path, os.path.pardir, "logs")
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename=f'{logs_path}/metrics.log',
                        encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')            
    
    if os.path.exists(args.reference_path):
        ref_rttm_files = [ref_rttm_file for ref_rttm_file in os.listdir(args.reference_path) if ref_rttm_file.lower().endswith(".rttm")]                
        logger.info("Rttm Ref files: {ref_rttm_files}")
    
    for model_folder in os.listdir(args.hyphoteses_path):
        model_folder_path = os.path.join(args.hyphoteses_path, model_folder)
        if os.path.isdir(model_folder_path):
            print(f"Processing folder: {model_folder_path}")
            logger.info(f"Processing folder: {model_folder_path}")
            for rttm_file in os.listdir(model_folder_path):
                files.append(rttm_file)
                if rttm_file in ref_rttm_files:
                    executeMetrics(args.metrics.split(','), model_folder_path, args.reference_path, rttm_file)
    print(map_results)
                    