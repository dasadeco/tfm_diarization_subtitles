from enum import Enum, auto

class MyEnum(Enum):
    def __new__(cls, value, model):
       obj = object.__new__(cls)
       obj._value_ = value
       obj.model = model
       return obj 

class VADModels(MyEnum):
    ORACLE = (auto(), 'oracle_vad')
    
    MARBLE = (auto(), 'vad_multilingual_marblenet') 
    MARBLENET = (auto(), 'vad_multilingual_marblenet')
    MULTILINGUAL = (auto(),'vad_multilingual_marblenet')
  
    
class SpeakerModels(MyEnum):
    TITANET_LARGE = (auto(), "titanet_large")
    LARGE = (auto(), "titanet_large")
    TITANET_L = (auto(), "titanet_large")
    TITANET = (auto(), "titanet_large")
    
    TITANET_SMALL = (auto(), "titanet_small")
    SMALL = (auto(), "titanet_small")
    TITANET_S = (auto(), "titanet_small")
    
    ECAPA_TDNN = (auto(), "ecapa_tdnn")
    ECAPA = (auto(), "ecapa_tdnn")
    TDNN = (auto(), "ecapa_tdnn")
    
    VERIFICATION = (auto(), "speakerverification_speakernet")
    SPEAKERVERIFICATION = (auto(), "speakerverification_speakernet")
    SPEAKER_VERIFICATION = (auto(), "speakerverification_speakernet")
    SPEAKERNET = (auto(), "speakerverification_speakernet")
 
     
class MSDDModels(MyEnum):
    GENERAL = (auto(), 'diar_infer_general')
    INFER_GENERAL = (auto(), 'diar_infer_general')
    DIAR_INFER_GENERAL  = (auto(), 'diar_infer_general')
    
    MEETING = (auto(), 'diar_infer_meeting')
    INFER_MEETING = (auto(), 'diar_infer_meeting')
    DIAR_INFER_MEETING  = (auto(), 'diar_infer_meeting')
    
    TELEPHONIC = (auto(), 'diar_infer_telephonic')
    INFER_TELEPHONIC = (auto(), 'diar_infer_telephonic')
    DIAR_INFER_TELEPHONIC  = (auto(), 'diar_infer_telephonic')