from enum import Enum, auto

class MyEnum(Enum):  # Para permitir alias en Enums
    def __new__(cls, value, model):
       obj = object.__new__(cls)
       obj._value_ = value
       obj.model = model
       return obj 
   
class SegmentationModels(MyEnum):
    v2_1 = (auto(), 'pyannote/segmentation')
    segmentation2_1 = (auto(), 'pyannote/segmentation')
    
    v3_0 = (auto(), 'pyannote/segmentation-3.0')
    segmentation3_0 = (auto(), 'pyannote/segmentation-3.0')
    
    diarizers = (auto(), 'diarizers-community/speaker-segmentation-fine-tuned-callhome-spa')
    callhome = (auto(), 'diarizers-community/speaker-segmentation-fine-tuned-callhome-spa')
    callhome_spain = (auto(), 'diarizers-community/speaker-segmentation-fine-tuned-callhome-spa')
         

class SpeakerModels(MyEnum):
    PYANNOTE = (auto(), 'pyannote/embedding')
    
    WESPEAKER = (auto(), 'pyannote/wespeaker-voxceleb-resnet34-LM')
    RESNET = (auto(), 'pyannote/wespeaker-voxceleb-resnet34-LM')
    RESNET34 = (auto(), 'pyannote/wespeaker-voxceleb-resnet34-LM')
    
    ECAPA = (auto(), "speechbrain/spkrec-ecapa-voxceleb")
    SPKREC = (auto(), "speechbrain/spkrec-ecapa-voxceleb")
    ECAPA_VOXCELEB = (auto(), "speechbrain/spkrec-ecapa-voxceleb")
    
    
class ClusteringMethods(Enum):   
    centroid = 'centroid'
    average = 'average'
    complete = 'complete'
    median = 'median'
    single = 'single'
    ward = 'ward'    