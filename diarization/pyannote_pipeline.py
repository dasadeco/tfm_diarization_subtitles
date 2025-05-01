## Pipeline de Pyannote la cual está usando por defecto un modelo de SpeechBrain ###

# 1. visit hf.co/pyannote/speaker-diarization and accept user conditions
# 2. visit hf.co/pyannote/segmentation and accept user conditions
# 3. visit hf.co/settings/tokens to create an access token
# 4. instantiate pretrained speaker diarization pipeline
from pyannote.audio import Pipeline
from pyannote.audio import Model
import os, argparse, logging
from enum import Enum
from datetime import datetime

class PipelineVersions(Enum):
    V2_1 ='speaker-diarization@2.1'
    V3_0 ='speaker-diarization-3.0'
    V3_1 ='speaker-diarization-3.1'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pyannote PIPELINE Audio Speaker Diarization')
    parser.add_argument('-vm', '--version_model', type=str, default=PipelineVersions.V3_1, help='Pipeline version')
    parser.add_argument('-hft', '--huggingface_token', type=str, help='Huggingface token')
        
    args = parser.parse_args()  
    if type(args.version_model) == PipelineVersions:
        version_model = args.version_model.value         
    else:
        version_model = args.version_model  
        
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename=f'/data/reg_pipeline_{version_model}_{datetime.now().strftime("%Y%m%d%H%M%S")}.log', 
                        encoding='utf-8', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')    
    logger.info(f' --- pyannote/{version_model} START obtención del modelo')
    
    pipeline = Pipeline.from_pretrained("pyannote/"+version_model, use_auth_token=args.huggingface_token)
    #pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=args.huggingface_token)
    
    # apply the pipeline to an audio file
    if os.path.isdir("/data/media/"):
        wav_files = [wav for wav in os.listdir("/data/media/") if wav.split('.')[-1] == 'wav']
        for wav_file in wav_files:
            # apply the pipeline to an audio file
            wav_file_path = os.path.join("/data/media/", wav_file)            
            diarization = pipeline(wav_file_path)            

            # dump the diarization output to disk using RTTM format
            rttm_filename = wav_file.replace('.wav', '.rttm')
            #logger.info(f'{datetime.now().strftime("%Y%m%d%H%M%S")}---INICIO de la diarización del audio {wav_file_path} ...')
            logger.info(f' --- INICIO de la diarización del audio {wav_file_path} ...')
            rttm_model_path = os.path.join("/data/media/rttm", version_model)
            if not os.path.exists(rttm_model_path):
                os.makedirs(rttm_model_path, exist_ok=True)
                logger.info(f'Se crea la carpeta de salida para los RTTM: {rttm_model_path}.')
            with open( os.path.join(rttm_model_path, rttm_filename), "w") as rttm_file:
                diarization.write_rttm(rttm_file)                 
    
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")
                logger.debug(f'---start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}')
            logger.info(f'{datetime.now().strftime("%Y%m%d%H%M%S")}---FIN de la diarización del audio {wav_file_path}.')   
    else:        
        logger.error(f'{datetime.now().strftime("%Y%m%d%H%M%S")}---No existe la carpeta /data/media/')    
        
logger.info(f'{datetime.now().strftime("%Y%m%d%H%M%S")}---pyannote/{version_model} END\n')            