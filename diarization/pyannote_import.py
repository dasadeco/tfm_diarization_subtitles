from enum import Enum

class SegmentationModels(Enum):
    v2_1, segmentation2_1 = 'pyannote/segmentation'
    v3_0, segmentation3_0 = 'pyannote/segmentation-3.0'        
    diarizers, callhome, callhome_spain = 'diarizers-community/speaker-segmentation-fine-tuned-callhome-spa'

class SpeakerModels(Enum):
    PYANNOTE = 'pyannote/embedding'    
    WESPEAKER, RESNET, RESNET34 = 'pyannote/wespeaker-voxceleb-resnet34-LM'
    ECAPA, SPKREC, ECAPA_VOXCELEB = "speechbrain/spkrec-ecapa-voxceleb"
    
class ClusteringMethods(Enum):   
    centroid = 'centroid'
    average = 'average'
    complete = 'complete'
    median = 'median'
    single = 'single'
    ward = 'ward'    