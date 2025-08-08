from enum import Enum

class VADModels(Enum):
    ORACLE = 'oracle_vad'
    MARBLE, MARBLENET, MULTILINGUAL = 'vad_multilingual_marblenet', 'vad_multilingual_marblenet', 'vad_multilingual_marblenet'

class SpeakerModels(Enum):
    TITANET_LARGE, LARGE, TITANET_L, TITANET = "titanet_large","titanet_large", "titanet_large","titanet_large"  
    TITANET_SMALL, SMALL, TITANET_S = "titanet_small", "titanet_small", "titanet_small"
    ECAPA_TDNN, ECAPA, TDNN = "ecapa_tdnn", "ecapa_tdnn", "ecapa_tdnn"
    VERIFICATION, SPEAKERVERIFICATION, SPEAKER_VERIFICATION, SPEAKERNET = "speakerverification_speakernet", "speakerverification_speakernet", "speakerverification_speakernet", "speakerverification_speakernet"
     
class MSDDModels(Enum):
    GENERAL, INFER_GENERAL, DIAR_INFER_GENERAL  = 'diar_infer_general', 'diar_infer_general', 'diar_infer_general'
    MEETING, INFER_MEETING, DIAR_INFER_MEETING  = 'diar_infer_meeting', 'diar_infer_meeting', 'diar_infer_meeting'
    TELEPHONIC, INFER_TELEPHONIC, DIAR_INFER_TELEPHONIC  = 'diar_infer_telephonic', 'diar_infer_telephonic', 'diar_infer_telephonic'