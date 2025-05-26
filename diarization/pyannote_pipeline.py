## Pipeline de Pyannote la cual está usando por defecto un modelo de SpeechBrain ###

# 1. visit hf.co/pyannote/speaker-diarization and accept user conditions
# 2. visit hf.co/pyannote/segmentation and accept user conditions
# 3. visit hf.co/settings/tokens to create an access token
# 4. instantiate pretrained speaker diarization pipeline
from pyannote.audio import Pipeline
from pyannote.audio import Model
import os, sys, argparse, logging
from enum import Enum
from datetime import datetime
import torchaudio

STATUS_FILE = 'status.txt'
FIN="FIN"

class PipelineVersions(Enum):
    V2_1 ='speaker-diarization@2.1'
    V3_0 ='speaker-diarization-3.0'
    V3_1 ='speaker-diarization-3.1'

## Para guardar en un archivo el estado de la ejecución del script, este archivo es la manera que tiene el gestor de contenedores 
# de saber que ha terminado la ejecución del script.
def save_status(info_text):
    with open(os.path.join(args.volume_path, STATUS_FILE), 'w') as info_file:
        logger.info("abierto el archivo de estado")
        info_file.write(info_text)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pyannote PIPELINE Audio Speaker Diarization')
    parser.add_argument('-vm', '--version_model', type=str, default=PipelineVersions.V3_1, help='Pipeline version')
    parser.add_argument('-hft', '--huggingface_token', type=str, help='Huggingface token')
    parser.add_argument('-vp', '--volume_path', type=str, help='Path of the folder with the audio(.wav) files')   
        
    args = parser.parse_args()  
    if type(args.version_model) == PipelineVersions:
        version_model = args.version_model.value         
    else:
        version_model = args.version_model  
        
    logger = logging.getLogger(__name__)
    logs_path = os.path.join(args.volume_path, "logs")
    if not os.path.exists( logs_path):
        os.makedirs( logs_path, exist_ok=True)
    logging.basicConfig(filename=f'{logs_path}/reg_pipeline_{version_model}_{datetime.now().strftime("%Y%m%d%H%M%S")}.log', 
                        encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')   
    
    logger.info(f'pyannote/{version_model} START obtención del modelo')    
    print(f'pyannote/{version_model} START obtención del modelo')    
    pipeline = Pipeline.from_pretrained("pyannote/"+version_model, use_auth_token=args.huggingface_token)
    
    # apply the pipeline to an audio file
    if os.path.isdir(args.volume_path):
        wav_files = [wav for wav in os.listdir(args.volume_path) if wav.split('.')[-1] == 'wav']
        for wav_file in wav_files:
            # apply the pipeline to an audio file
            wav_file_path = os.path.join(args.volume_path, wav_file)
            
            #waveform, sample_rate = torchaudio.load(wav_file_path)
            
            diarization = pipeline(wav_file_path)                        
            #diarization = pipeline({"waveform":waveform, "sample_rate":sample_rate})            
            logger.info(f'Pipeline preparada para el audio {wav_file_path} ...')
            print(f'Pipeline preparada para el audio {wav_file_path} ...')
            # dump the diarization output to disk using RTTM format
            rttm_filename = wav_file.replace('.wav', '.rttm')
            logger.info(f'INICIO de la diarización del audio {wav_file_path} ...')
            print(f'INICIO de la diarización del audio {wav_file_path} ...')
            rttm_model_path = os.path.join(args.volume_path, "rttm", version_model)
            if not os.path.exists(rttm_model_path):
                os.makedirs(rttm_model_path, exist_ok=True)
                logger.info(f'Se crea la carpeta de salida para los RTTM: {rttm_model_path}.')
                print(f'Se crea la carpeta de salida para los RTTM: {rttm_model_path}.')
            with open( os.path.join(rttm_model_path, rttm_filename), "w") as rttm_file:
                diarization.write_rttm(rttm_file)                 
    
            for turn, _, speaker in diarization.itertracks(yield_label=True):                
                logger.debug(f'start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}')
                print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")
            logger.info(f'FIN de la diarización del audio {wav_file_path}.') # Imprime al archivo de logging el fin de la diarización de uno de los archivos   
            print(f'FIN de la diarización del audio {wav_file_path}.')       # Imprime a stdout el fin de la diarización de uno de los archivos   
            save_status(f'FIN de la diarizacion del audio {wav_file_path}.') # Imprime al archivo de estado el fin de la diarización de uno de los archivos, 
                            # este archivo es la manera que teiene el gestor de contenedores de saber que ha terminado la ejecución del script.  
        logger.info(f'pyannote/{version_model} FIN\n')
        print(f'pyannote/{version_model} FIN\n')
        save_status(FIN)   
        sys.exit(0)         
    else:        
        logger.error(f'No existe la carpeta {args.volume_path}')    
        print(f'No existe la carpeta {args.volume_path}')    
        exit