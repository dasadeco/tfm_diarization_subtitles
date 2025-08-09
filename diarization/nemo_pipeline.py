import os, argparse, logging
import shutil
from datetime import datetime
import time
import json
from omegaconf import OmegaConf
import wget
import numpy as np
from nemo.collections.asr.models import ClusteringDiarizer
from nemo_import import VADModels as VADModels
from pydub import AudioSegment
import torch

STATUS_FILE = 'nemo_pipeline_status.txt'
EXECUTION_TIME_FILE = "NEMO_exec_time.txt"
PATH_BASE_DATASETS = "datasets"
FIN="FIN"

#CONFIG_GENERAL_DIAR_INF_FILENAME = "diar_infer_general.yaml"
CONFIG_DIAR_INF_URL = "https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/inference/"
#CONFIG_GENERAL_DIAR_INF_URL = CONFIG_DIAR_INF_URL + CONFIG_GENERAL_DIAR_INF_FILENAME

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

    parser = argparse.ArgumentParser(description='Pyannote NEMO Audio Speaker Diarization')
    parser.add_argument('-vp', '--volume_path', type=str, help='Ruta de la carpeta con archivos de audio(.wav)')
    parser.add_argument('-vad', '--vad_model', type=str, default='oracle_vad', help='Indicamos el nombre del modelo VAD a utilizar')
    parser.add_argument('-rp', '--reference_path', type=str, help='Ruta de la carpeta con archivos rttm de referencia si disponemos de ellos y se selecciona `oracle_vad`')
    parser.add_argument('-sm', '--speaker_model', type=str, default='titanet_large', help='Indicamos el nombre del modelo para obtener embeddings a utilizar')
    parser.add_argument('-mdo', '--min_duration_off', type=float,  default=0.0, help="Tiempo mínimo que tienen que alcanzar los silencios o se eliminan")            
    parser.add_argument('-ns', '--num_speakers', default=None,  type=int, help='Indicamos el numero de speakers (pero tendría que ser el mismo número en todos los archivos)')    
    parser.add_argument('-mm', '--msdd_model', type=str, default='diar_infer_general', help='Indicamos el nombre del modelo Multiscala Diarization Decoder')
    parser.add_argument('-wl', '--window_lengths', type=str, default='[1.5]', help='Lista de longitudes de ventana modelo Multiscale Diarization Decoder')
    args = parser.parse_args()
    
    logs_path = os.path.join(args.volume_path, "logs")
    if not os.path.exists( logs_path):
        os.makedirs( logs_path, exist_ok=True)
    logging.basicConfig(filename=f'{logs_path}/reg_pipeline_nemo_{datetime.now().strftime("%Y%m%d%H%M%S")}.log', force=True,
                        encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')   
    logger = logging.getLogger(__name__)
    logger.info(f"Iniciando el Pipeline de Nemo. Parseados los parámetros...") 
    print(f"Iniciando el Pipeline de Nemo. Parseados los parámetros...") 

    vad_model = args.vad_model         
    
    if type(args.window_lengths) != list:
        window_lengths = [(i.lstrip(' ').rstrip(' ')) for i in args.window_lengths.lstrip('[').rstrip(']').split(',')]
        window_lengths = np.fromiter( window_lengths, dtype=float).tolist()
    else:
        window_lengths = args.window_lengths
    window_steps = [i/2 for i in window_lengths]
    window_weights =[1 for _ in window_lengths]    
         
    if not os.path.exists(args.volume_path) or not os.path.isdir(args.volume_path):
        logger.info(f'No existe la carpeta {args.volume_path}')    
        print(f'No existe la carpeta {args.volume_path}')    
        exit(1)             

    print(f'START iniciando el pipeline de NeMo')    
    logger.info(f'START iniciando el pipeline de NeMo')        
    if not args.reference_path or not os.path.exists(args.reference_path):
        args.reference_path = '/data/rttm_ref' 
        if not os.path.exists(args.reference_path) and vad_model==VADModels.ORACLE.value:       
            print("No hay carpeta de archivos RTTM de referencia con VAD_MODEL seleccionado!")
            logger.warning(f"No hay carpeta de archivos RTTM de referencia con VAD_MODEL seleccionado!")
            vad_model= VADModels.MARBLE.value            
     
    provide_num_speakers = False
    if args.num_speakers is not None:
        if type(args.num_speakers) != int:
            print("Número de speakers debe ser un entero!")
            logger.warning(f"Número de speakers debe ser un entero!")
            args.num_speakers = None    
        else:    
            args.num_speakers = str(args.num_speakers)
            provide_num_speakers = True

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')   
    print(f'Determinando el device')
    logger.info(f'Determinando el device')
    # aplica la pipeline iterativamente en el volumen de archivos de audio
    datasets_path = os.path.join(args.volume_path, PATH_BASE_DATASETS)
    if not os.path.exists(datasets_path):
         print(f'No existe la carpeta {datasets_path}')
         logger.error(f'No existe la carpeta {datasets_path}')        
         exit(1)
    tuplas = _buscar_by_extension_in_dataset(datasets_path, ".wav") 
    if os.path.exists(os.path.join(args.volume_path, "rttm", EXECUTION_TIME_FILE)):
        os.remove(os.path.join(args.volume_path, "rttm", EXECUTION_TIME_FILE))
    combined_models_subfolder_name = ''
    ## INICIO Configuración general para todos los archivos de audio 
    config_diar_inf_filename = args.msdd_model + '.yaml'
    if not os.path.exists(os.path.join(datasets_path, config_diar_inf_filename)):
        print("Descargamos el archivo YAML para la configuración de Inferencia de Diarización de Nemo")
        logger.info("Descargamos el archivo YAML para la configuración de Inferencia de Diarización de Nemo")
        wget.download(CONFIG_DIAR_INF_URL + config_diar_inf_filename, os.path.join(datasets_path, config_diar_inf_filename))
    config = OmegaConf.load(os.path.join(datasets_path, config_diar_inf_filename))
    #print(OmegaConf.to_yaml(config))  ## Descomentar si queremos ver la config. por defecto.
    print(f"El tipo de dispositivo de proceso es {device.type}")
    logger.info(f"El tipo de dispositivo de proceso es {device.type}")
    if device.type == 'cpu':
        config.num_workers = 0 # Avoiding error with SpeakerLabel                
    config.verbose = False
    config.diarizer.msdd_model.model_path = args.msdd_model    
    config.diarizer.speaker_embeddings.model_path = args.speaker_model
    config.diarizer.speaker_embeddings.parameters.window_length_in_sec = window_lengths
    config.diarizer.speaker_embeddings.parameters.shift_length_in_sec = window_steps
    config.diarizer.speaker_embeddings.parameters.multiscale_weights= window_weights
    config.diarizer.clustering.parameters.oracle_num_speakers = provide_num_speakers    
    ## FIN Configuración general para todos los archivos de audio 
    for tupla in tuplas:
        rttm_ref_not_found = False
        wav_audio_file = tupla[0]   
        print(f"Archivo a procesar: {wav_audio_file}")
        logger.info(f"Archivo a procesar: {wav_audio_file}")
        rttm_filename = wav_audio_file.replace('.wav', '.rttm')
        input_manifest_json_path = wav_audio_file.replace('.wav', '_input_manifest.json')
        if args.volume_path != tupla[1]:
            if PATH_BASE_DATASETS==tupla[1]:
                dataset_subfolder = '.'
                wav_file_path = os.path.join(datasets_path, wav_audio_file)
                print(f'El audio {wav_audio_file} no tiene una carpeta de Datasets asociada')
                logger.warning(f'El audio {wav_audio_file} no tiene una carpeta de Datasets asociada')
            else:                        
                dataset_subfolder = tupla[1]             
                wav_file_path = os.path.join(datasets_path, dataset_subfolder, wav_audio_file)
                print(f'El audio {wav_audio_file} está en la carpeta de Datasets asociada')
                logger.info(f'El audio {wav_audio_file} está en la carpeta de Datasets asociada')                
            if vad_model == VADModels.ORACLE.value:
                ###### SI ESTAMOS EN EL CASO --ORACLE_VAD--  ######
                rttm_ref_filepath = os.path.join(args.reference_path, dataset_subfolder, rttm_filename)
                if not os.path.exists(rttm_ref_filepath):
                    print(f"Con Oracle-VAD no se encuentran el archivo con los RTTM de referencia para el archivo {wav_audio_file} , se seleccionará "\
                        + "VAD Marble Net")                    
                    logger.warning(f"Con Oracle-VAD no se encuentran el archivo con los RTTM de referencia para el archivo "\
                                   + f"{wav_audio_file} , se seleccionará VAD Marble Net")
                    rttm_ref_not_found = True
                    rttm_ref_filepath = None
            else:
                rttm_ref_filepath = None
            if rttm_ref_not_found:    
                combined_models_subfolder_name=str('NeMo__' + VADModels.MARBLE.value + '+' + args.speaker_model)
            else:    
                combined_models_subfolder_name=str('NeMo__' + vad_model + '+' + args.speaker_model)
            print(f'La carpeta de salida del rttm de hipótesis será {combined_models_subfolder_name} para el audio {wav_audio_file}')
            logger.info(f'La carpeta de salida del rttm de hipótesis será {combined_models_subfolder_name} para el audio {wav_audio_file}')
            rttm_hyp_model_path = os.path.join(args.volume_path, "rttm", dataset_subfolder, combined_models_subfolder_name)
            if not os.path.exists(rttm_hyp_model_path):
                os.makedirs(rttm_hyp_model_path, exist_ok=True)
                print(f'Se crea la carpeta de salida para los RTTM: {rttm_hyp_model_path}.')
                logger.info(f'Se crea la carpeta de salida para los RTTM: {rttm_hyp_model_path}.')                
                                          
            this_json = {
                'audio_filepath': wav_file_path,
                'offset': 0,
                'duration': None,
                'label': 'infer',
                'text': '-',
                'num_speakers': args.num_speakers,
                'rttm_filepath': rttm_ref_filepath,
                'uem_filepath' : None
            }
            with open(os.path.join(rttm_hyp_model_path, input_manifest_json_path),'w') as manif_file:
                json.dump(this_json, manif_file)
                manif_file.write('\n')
                print(f"Preparado el archivo de manifiesto en {input_manifest_json_path}")
                logger.info(f"Preparado el archivo de manifiesto en {input_manifest_json_path}")

            config.diarizer.manifest_filepath = os.path.join(rttm_hyp_model_path, input_manifest_json_path)
            config.diarizer.out_dir = rttm_hyp_model_path # Directory to store intermediate files and prediction outputs
                        
            config.diarizer.oracle_vad = vad_model==VADModels.ORACLE.value and not rttm_ref_not_found #----> ORACLE VAD o MARBLENET VAD
            if vad_model != VADModels.ORACLE.value:
                config.diarizer.vad.model_path = vad_model
            if vad_model == VADModels.ORACLE.value and rttm_ref_not_found:
                config.diarizer.vad.model_path = VADModels.MARBLE.value # --> MARBLENET VAD asignado si no es posible ORACLE VAD
                ## Posibles parámetros de configuración extra de un VAD que no sea Oracle.
                #config.diarizer.vad.parameters.onset = 0.8
                #config.diarizer.vad.parameters.offset = 0.6
                #config.diarizer.vad.parameters.pad_offset = -0.05
                #config.diarizer.vad.parameters.min_duration_on = 0.5 # Threshold for short speech segment deletion
                config.diarizer.vad.parameters.min_duration_off = args.min_duration_off # Threshold for small non_speech deletion                

            start_time = time.time()
            ##### INICIO DE LA DIARIZACION ###########
            oracle_vad_clusdiar_model = ClusteringDiarizer(cfg=config)            
            oracle_vad_clusdiar_model.diarize()                            
            ##### FIN DE LA DIARIZACION ###########
            diarization_time = time.time() - start_time            
            print(f'Tiempo de diarización realizada con NeMo de {wav_file_path} : {diarization_time} segundos')            
            logger.info(f'Tiempo de diarización realizada con NeMo de {wav_file_path} : {diarization_time} segundos')
            
            # El Pipeline de NeMo copia los RTTM inferidos a una subcarpeta que crea, llamada "pred_rttms"; pero los queremos en la carpeta padre
            shutil.copy2(os.path.join(rttm_hyp_model_path, 'pred_rttms', rttm_filename), os.path.join(rttm_hyp_model_path, rttm_filename))            
            shutil.rmtree(os.path.join(rttm_hyp_model_path, 'pred_rttms'))
                
            with open( os.path.join(args.volume_path, "rttm", EXECUTION_TIME_FILE), "a", encoding="utf-8") as execution_time_file:                       
                audio_Segment = AudioSegment.from_file(wav_file_path)            
                print(f"Duración del audio: {audio_Segment.duration_seconds}")                                          
                logger.info(f"Duración del audio: {audio_Segment.duration_seconds}")                                          
                execution_time_file.write(f"{rttm_filename} {combined_models_subfolder_name} {dataset_subfolder} {diarization_time} {audio_Segment.duration_seconds}\n")            
            print(f'FIN de la diarización por NeMo del audio {wav_file_path}.')       # Imprime a stdout el fin de la diarización de uno de los archivos       
            logger.info(f'FIN de la diarización por NeMo del audio {wav_file_path}.') # Imprime al archivo de logging el fin de la diarización de uno de los archivos               
            save_status(f'FIN de la diarizacion por NeMo del audio {wav_file_path}.') # Imprime al archivo de estado el fin de la diarización de uno de los archivos, 
            # Este archivo es la manera que tiene el gestor de contenedores de saber que ha terminado la ejecución del script.                          
    logger.info(f'NeMo {combined_models_subfolder_name} FIN\n')
    print(f'NeMo {combined_models_subfolder_name} FIN\n')
    save_status(FIN)   
    exit(0)                         