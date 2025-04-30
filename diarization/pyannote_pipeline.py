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
    logging.basicConfig(filename=f'./data/reg_pipeline_{version_model}_{datetime.now().strftime("%Y%m%d%H%M%S")}.log', 
                        encoding='utf-8', level=logging.DEBUG)    
    logger.debug("pyannote/"+version_model+" ...  ")
    
    pipeline = Pipeline.from_pretrained("pyannote/"+version_model, cache_dir="./models")
    
    # apply the pipeline to an audio file
    if os.path.isdir("./data/media/"):
        wav_files = [wav for wav in os.listdir("./data/media/") if wav.split('.')[-1] == 'wav']
        for wav_file in wav_files:
            # apply the pipeline to an audio file
            wav_file_path = os.path.join("./data/media/", wav_file)            
            diarization = pipeline(wav_file_path)            

            # dump the diarization output to disk using RTTM format
            rttm_filename = wav_file.replace('.wav', '.rttm')
            logger.info(f"INICIO de la diarización del audio {wav_file_path} ...")
            with open( os.path.join("./data/media/", rttm_filename), "w") as rttm_file:
                diarization.write_rttm(rttm_file)     
            
    
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")
                logger.info(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")
            logger.info(f"FIN de la diarización del audio {wav_file_path} ...")   
        
logger.debug("pyannote/"+version_model+" END\n  ")            