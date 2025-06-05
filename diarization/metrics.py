from enum import Enum
from io import FileIO

from pyannote.core import Annotation, Segment
import argparse
import os
import logging
from datetime import datetime
import math
import pandas as pd

from pyannote.metrics.diarization import DiarizationErrorRate
from pyannote.metrics.detection import DetectionErrorRate

RTTM = "rttm"
RTTM_REF = "rttm_ref"
COLLAR = 0.250

class DatasetEnum(Enum):
    canaluned = "canal.uned"
    fiapas = "FIAPAS"
    fundaciononce = "Fundacion ONCE"

class MetricsEnum(Enum):
  DER = "Diarization Error Rate"
  DetER = "Detection Error Rate"
  Cobertura = "Cobertura"
  
class PipelineVersions(Enum):
    V2_1 ='speaker-diarization@2.1'
    V3_0 ='speaker-diarization-3.0'
    V3_1 ='speaker-diarization-3.1'  


class MetricsByAudioFile():    
    #Solo Pipelines de Pyannote de momento
    def __init__(self, rttm_file:str, modelo:PipelineVersions, metrics_map:dict, dataset=DatasetEnum.canaluned):
        self.rttm_file = rttm_file
        self.modelo = modelo
        self.metrics_map = metrics_map
        self.dataset = dataset

logger = None
total_metrics:list[MetricsByAudioFile] = []                   
  
def executeMetrics(metrics:list, subfolder_path, rttms_ref_path, rttm_file):
      
    def _create_annot(file:FileIO, annot:Annotation)->Annotation:              
      for line in file:
        if line.strip() != "":
            data_list = line.split(" ")
            annot[Segment( math.trunc(float(data_list[3])*100),     
                math.trunc(float(data_list[3])*100) + math.trunc(float(data_list[4])*100))] = \
                data_list[7]
      return annot
                      
    model = os.path.basename(subfolder_path)
    hyp_rttm_file_path = os.path.join(subfolder_path, rttm_file)
    ref_rttm_file_path = os.path.join(rttms_ref_path, rttm_file)
    hypothesis = Annotation(rttm_file, model)
    with open(hyp_rttm_file_path, 'r') as hyp_file:
        hypothesis = _create_annot(hyp_file, hypothesis)
    hyp_file.close()    
        
    reference = Annotation(rttm_file, RTTM_REF)
    with open(ref_rttm_file_path, 'r') as ref_file:
        reference = _create_annot(ref_file, reference)
    ref_file.close()    
     
    metrics_map = {}                                      
    for metric in metrics:        
        if metric.strip() == MetricsEnum.DER or metric.strip() == MetricsEnum.DER.name:
            der_metric = DiarizationErrorRate(COLLAR)                 
            metrics_map[ MetricsEnum.DER.value] = der_metric(reference, hypothesis)            
        elif metric.strip() == MetricsEnum.DetER or metric.strip() == MetricsEnum.DetER.name:    
            deter_metric = DetectionErrorRate(COLLAR)                 
            metrics_map[MetricsEnum.DetER.value] = deter_metric(reference, hypothesis)            
    mbaf = MetricsByAudioFile(rttm_file, model, metrics_map)
    total_metrics.append(mbaf)

def write_metrics(hypotheses_path):    
    index = [ i for i, _ in enumerate(total_metrics)]
    columns = ["Audios", "Modelos"] 
    rttm_files = [ mbaf.rttm_file for mbaf in total_metrics]
    modelos = [ mbaf.modelo for mbaf in total_metrics]        
    data = {"Audios": rttm_files, "Modelos": modelos}
    list_metrics = [mbaf.metrics_map for mbaf in total_metrics]
    for metrics in list_metrics:
        for metric in metrics.keys():
            if metric not in columns:
                columns += [metric]
            if not metric in data:
               data[metric]=[metrics[metric]]
            else: 
               data[metric].append(metrics[metric])

    metrics_df = pd.DataFrame(data, index = index, columns=columns)
    logs_path = os.path.join(hypotheses_path, os.path.pardir, "logs")
    
    export_path = os.path.join(hypotheses_path, os.path.pardir, "metrics", "metrics.xlsx")
    metrics_df.to_excel(export_path,  index=False)
    
    

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
    
    rttm_files_list = []
    for model_folder in os.listdir(args.hyphoteses_path):
        model_folder_path = os.path.join(args.hyphoteses_path, model_folder)
        if os.path.isdir(model_folder_path):
            print(f"Processing folder: {model_folder_path}")
            logger.info(f"Processing folder: {model_folder_path}")
            for rttm_file in os.listdir(model_folder_path):
                files.append(rttm_file)
                if rttm_file in ref_rttm_files:
                    rttm_files_list.append(rttm_file +" - "+ model_folder)
                    executeMetrics(args.metrics.split(','), model_folder_path, args.reference_path, rttm_file)

    write_metrics( args.hyphoteses_path )