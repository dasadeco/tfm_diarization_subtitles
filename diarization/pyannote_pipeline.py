## Pipeline de Pyannote la cual está usando por defecto un modelo de SpeechBrain ###

# 1. visit hf.co/pyannote/speaker-diarization and accept user conditions
# 2. visit hf.co/pyannote/segmentation and accept user conditions
# 3. visit hf.co/settings/tokens to create an access token
# 4. instantiate pretrained speaker diarization pipeline
from pyannote.audio import Pipeline
from pyannote.audio import Model
import argparse, logging
from enum import Enum

class PipelineVersions(Enum):
    V2_1 ='speaker-diarization@2.1'
    V3_1 ='speaker-diarization-3.1'



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pyannote PIPELINE Audio Speaker Diarization')
    parser.add_argument('-vm', '--version_model', type=str, default=PipelineVersions.V3_1, help='Pipeline version')  
    
    args = parser.parse_args()  
    if type(args.version_model) == PipelineVersions:
        version_model = args.version_model.value         
    else:
        version_model = args.version_model  
        
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename='./data/reg_pipeline'+version_model+'.log', encoding='utf-8', level=logging.DEBUG)
    logger.debug("pyannote/"+version_model+" ...  ")
    
    pipeline = Pipeline.from_pretrained("pyannote/"+version_model, cache_dir="./models", 
                                        use_auth_token="args.huggingface_token",)


    # apply the pipeline to an audio file
    for file in ["./data/media/"]:
        # apply the pipeline to an audio file
        diarization = pipeline(file)

        # print the result
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")

        # dump the diarization output to disk using RTTM format
        with open("./datasets/sample.rttm", "w") as rttm:
            diarization.write_rttm(rttm)     
    diarization = pipeline("./data/media/sample.wav")

    # print the result
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")

    # dump the diarization output to disk using RTTM format
    with open("./datasets/sample.rttm", "w") as rttm:
        diarization.write_rttm(rttm)
        

logger.debug("pyannote/"+version_model+" END\n  ")        
    
    

