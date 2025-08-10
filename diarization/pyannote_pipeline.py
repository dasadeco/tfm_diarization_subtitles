## Pipeline de Pyannote la cual está usando por defecto un modelo de SpeechBrain ###
# 1. visit hf.co/pyannote/speaker-diarization and accept user conditions
# 2. visit hf.co/pyannote/segmentation and accept user conditions
# 3. visit hf.co/settings/tokens to create an access token
# 4. instantiate pretrained speaker diarization pipeline
from pyannote.audio import Model
from pyannote.audio.pipelines import SpeakerDiarization
from pyannote.audio.pipelines.utils.hook import ProgressHook
import os, argparse, logging
from enum import Enum
from datetime import datetime
import time
from pydub import AudioSegment
import torch
from diarizers.models.model import SegmentationModel

STATUS_FILE = 'pyannote_pipeline_status.txt'
EXECUTION_TIME_FILE = "PYANNOTE_exec_time.txt"
PATH_BASE_DATASETS = "datasets"
FIN="FIN"

class PipelineVersions(Enum):
    V2_1 ='speaker-diarization@2.1'
    V3_1 ='speaker-diarization-3.1'   


## Para guardar en un archivo el estado de la ejecución del script, este archivo es la manera que tiene el gestor de contenedores 
# de saber que ha terminado la ejecución del script.
def save_status(info_text):
    with open(os.path.join(args.volume_path, STATUS_FILE), 'w', encoding="utf-8") as info_file:        
        info_file.write(info_text)
        info_file.close()
        
def _buscar_by_extension_in_dataset(path, extension):
    resultados = []
    for carpeta_actual, subcarpetas, archivos in os.walk(path):
        nombre_carpeta = os.path.basename(carpeta_actual)
        for archivo in archivos:
            if archivo.lower().endswith(extension):
                resultados.append((archivo, nombre_carpeta))
    return resultados        

if __name__ == '__main__':
    print("Llamado el Pipeline de Pyannote ... ")
## usage: pyannote_pipeline.py [-h] [-hft HUGGINGFACE_TOKEN] [-vp DOCKER_VOLUME_PATH] [params ...]
    parser = argparse.ArgumentParser(description='Pyannote PIPELINE Audio Speaker Diarization')
    parser.add_argument('-pv', '--pipeline_version', type=str, default=PipelineVersions.V3_1, help="Versión de la Pipeline Pyannote")
    parser.add_argument('-hft', '--huggingface_token', type=str, help="Token de Huggingface")
    parser.add_argument('-sem', '--segmentation_model', type=str, default='pyannote/segmentation-3.0', help="Modelo de segmentacion")
    parser.add_argument('-sm', '--speaker_model', type=str, default='pyannote/embedding', help="Modelo de embedding o del hablante")
    parser.add_argument('-mdo', '--min_duration_off', type=float,  default=0.0, help="Tiempo mínimo que tienen que alcanzar los silencios o se eliminan")
    parser.add_argument('-mtc', '--min_cluster_size', type=int,  default=12, help="Tamaño mínimo de clusters,si no se alcanza en alguno, se fusiona con el más similar")
    parser.add_argument('-mec', '--method_cluster', type=str, default='centroid', help="Método utilizado en el clustering aglomerativo")
    parser.add_argument('-thr', '--threshold_cluster', type=float, default=0.7045654963945799, help="Umbral utilizado en el clustering aglomerativo")
    parser.add_argument('-ns', '--num_speakers', default=None,  type=int, help='Indicamos el numero de speakers (pero tendría que ser el mismo número en todos los archivos de esta pasada)')
    parser.add_argument('-vp', '--volume_path', type=str, help='Carpeta con los archivos de audio(.wav)')
    args = parser.parse_args()  
    print("Parseados los argumentos en el Pipeline de Pyannote ... ")
    if type(args.pipeline_version) == PipelineVersions:
        pipeline_version = args.pipeline_version.value         
    else:
        pipeline_version = args.pipeline_version 
                         
    logs_path = os.path.join(args.volume_path, "logs")
    if not os.path.exists( logs_path):
        os.makedirs( logs_path, exist_ok=True)
    logging.basicConfig(filename=f'{logs_path}/reg_pipeline_{pipeline_version}_{datetime.now().strftime("%Y%m%d%H%M%S")}.log', force=True,
                        encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')   
    logger = logging.getLogger(__name__)
    logger.info(f'pyannote/{pipeline_version} START obtención del modelo')    
    print(f'pyannote/{pipeline_version} START obtención del modelo')   
    
    datasets_path = os.path.join(args.volume_path, PATH_BASE_DATASETS)
    if not os.path.exists(datasets_path):
         print(f'No existe la carpeta {datasets_path}')
         logger.error(f'No existe la carpeta {datasets_path}')        
         exit(1)        

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    if not args.segmentation_model.startswith("pyannote/"):
        segmentation_model = SegmentationModel().from_pretrained(args.segmentation_model,).to_pyannote_model()    
    else:
        segmentation_model = args.segmentation_model        
    if args.speaker_model.startswith("pyannote/"):
        embedding_model = Model.from_pretrained(args.speaker_model, use_auth_token=args.huggingface_token)
    else:    
        embedding_model = args.speaker_model
        
    pipeline_params_dict = {
        "segmentation": {
            "min_duration_off": args.min_duration_off
        },
        "clustering": {
            "method": args.method_cluster,
            "min_cluster_size": args.min_cluster_size,
            "threshold": args.threshold_cluster
        }
    }
    if args.segmentation_model == "pyannote/segmentation": ##Pipeline 2.1
        pipeline_params_dict["segmentation"]["threshold"] = 0.5
    pipeline = SpeakerDiarization(embedding=embedding_model, segmentation=segmentation_model, 
                                  clustering="AgglomerativeClustering" , 
                                  use_auth_token=args.huggingface_token).instantiate(pipeline_params_dict) \
                .to(device=device)        
                
    combined_models_subfolder_name = str('Pyannote__' + args.segmentation_model + '+' + args.speaker_model).replace('/', '-') 
    if os.path.isdir(args.volume_path):
        tuplas = _buscar_by_extension_in_dataset(datasets_path, ".wav") 
        if os.path.exists(os.path.join(args.volume_path, "rttm", EXECUTION_TIME_FILE)):
            os.remove(os.path.join(args.volume_path, "rttm", EXECUTION_TIME_FILE))
    # aplica la pipeline iterativamente en el volumen de archivos de audio            
        for tupla in tuplas:
            wav_audio_file = tupla[0]   
            if args.volume_path != tupla[1]:
                if PATH_BASE_DATASETS==tupla[1]:
                    dataset_subfolder = '.'
                    print(f'El audio {wav_audio_file} no tiene una carpeta de Datasets asociada')
                    logger.warning(f'El audio {wav_audio_file} no tiene una carpeta de Datasets asociada')                    
                else:    
                    dataset_subfolder = tupla[1]                   
                wav_file_path = os.path.join(datasets_path, dataset_subfolder, wav_audio_file)                                    
                start_time = time.time()

                with ProgressHook() as hook:
                    if args.num_speakers is None:
                        diarization = pipeline(wav_file_path, hook=hook)
                    else:                           
                        diarization = pipeline(wav_file_path, hook=hook, num_speakers=args.num_speakers)         
                    
                diarization_time = time.time() - start_time
                logger.info(f'Tiempo de diarización realizada con Pyannote de {wav_file_path} : {diarization_time} segundos')
                print(f'Tiempo de diarización realizada con Pyannote de {wav_file_path} : {diarization_time} segundos')
                # dump the diarization output to disk using RTTM format
                rttm_filename = wav_audio_file.replace('.wav', '.rttm')
                
                logger.info(f'INICIO de la escritura de la diarización del audio {wav_file_path} ...')
                print(f'INICIO de la escritura de la diarización del audio {wav_file_path} ...')
                rttm_hyp_model_path = os.path.join(args.volume_path, "rttm", dataset_subfolder, combined_models_subfolder_name)
                if not os.path.exists(rttm_hyp_model_path):
                    os.makedirs(rttm_hyp_model_path, exist_ok=True)
                    logger.info(f'Se crea la carpeta de salida para los RTTM: {rttm_hyp_model_path}.')
                    print(f'Se crea la carpeta de salida para los RTTM: {rttm_hyp_model_path}.')
                    
                with open( os.path.join(rttm_hyp_model_path, rttm_filename), "w", encoding="utf-8") as rttm_file:
                    diarization.write_rttm(rttm_file)                 
                with open( os.path.join(args.volume_path, "rttm", EXECUTION_TIME_FILE), "a", encoding="utf-8") as execution_time_file:                       
                    audio_Segment = AudioSegment.from_file(wav_file_path)            
                    print(f"Duración del audio: {audio_Segment.duration_seconds}")                                          
                    execution_time_file.write(f"{rttm_filename} {combined_models_subfolder_name} {dataset_subfolder} {diarization_time} {audio_Segment.duration_seconds}\n")
                    
                for turn, _, speaker in diarization.itertracks(yield_label=True):                
                    logger.debug(f'start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}')
                    print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")
                logger.info(f'FIN de la diarización por Pyannote del audio {wav_file_path}.') # Imprime al archivo de logging el fin de la diarización de uno de los archivos   
                print(f'FIN de la diarización por Pyannote del audio {wav_file_path}.')       # Imprime a stdout el fin de la diarización de uno de los archivos   
                save_status(f'FIN de la diarizacion por Pyannote del audio {wav_file_path}.') # Imprime al archivo de estado el fin de la diarización de uno de los archivos, 
                            # este archivo es la manera que tiene el gestor de contenedores de saber que ha terminado la ejecución del script.  
        logger.info(f'pyannote/{pipeline_version} FIN\n')
        print(f'pyannote/{pipeline_version} FIN\n')
        save_status(FIN)   
        exit(0)         
    else:        
        logger.error(f'No existe la carpeta {args.volume_path}')    
        print(f'No existe la carpeta {args.volume_path}')    
        exit(1)