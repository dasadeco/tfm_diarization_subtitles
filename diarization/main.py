import argparse
import os
import logging
from datetime import datetime

from converter_audio import ConverterToAudio 
from docker_diariz_manager import DockerDiarizationManager
from docker_diariz_manager import DockerImages
from metrics import MetricsCalculator
from pyannote_import import SpeakerModels as SpeakerModelPyannote, SegmentationModels
from nemo_import import SpeakerModels as SpeakerModelNemo, VADModels, MSDDModels

def call_manager_to_execute_container(image_name, params):
    container_name =  image_name.split('/')[1].split(':')[0]  ## TODO: Podría fallar si la imagen no empieza por dasaenzd? probarlo...  
    if params:
        dockerManager.execute_command(container_name, params)

if __name__ == '__main__':    
    parser = argparse.ArgumentParser(description="Módulo principal")
    parser.add_argument('-mp', '--media_path', type=str, default='./datasets', help='Carpeta de entrada con los archivos de video(.mp4) y audio a convertir')
    parser.add_argument('-hvp', '--host_volume_path',  type=str, default="./data/media", help='Path de la maquina host ( P. ej. mi Windows 10)')        
    parser.add_argument('-cvp', '--container_volume_path', type=str, default='/media', help='Path en el contenedor donde se guardan los archivos wav')
    parser.add_argument('-nd', '--no_diarize', action='store_true', help='Si se indica, no realiza diarización')                   
    parser.add_argument('-con', '--converter', action='store_true', help='Previamente, se pueden convierten archivos de audio y video al formato WAV para disponer de datasets')
    parser.add_argument('-gen_ref', '--genera_all_rttm', action='store_true', help='También previamente, si se desea, se pueden tratar los archivos de subtítulos existentes en su carpeta para convertirlos a RTTM de referencia') 
    parser.add_argument('-d', '--delta', type=int, default=0, help='(hiper)parámetro Delta para establecer cuando consideramos que termina un speech del mismo hablante')    
    
    parser.add_argument('-img', '--image_name', type=str, help='Nombre de la imagen docker cuando sólo elegimos una')    
    parser.add_argument('-pv', '--pipeline_version', type=str, help='Versión de la Pipeline Pyannote, (sólo para efecto informativo en los logs, debe concordar con el modelo de segmentación y de embedding)')
    parser.add_argument('-hft', '--huggingface_token', type=str, help='Token de Huggingface para Pyannote')
    parser.add_argument('-vad', '--vad_model', type=str, help='Indicamos el nombre del modelo VAD a utilizar para NeMo')
    parser.add_argument('-sem', '--segmentation_model', type=str, help="Modelo de segmentacion para Pyannote")    
    parser.add_argument('-smp', '--speaker_model_pyannote', type=str, help='Indicamos el nombre del modelo para obtener embeddings a utilizar para Pyannote')
    parser.add_argument('-smn', '--speaker_model_nemo', type=str, help='Indicamos el nombre del modelo para obtener embeddings a utilizar para NeMo') 
    parser.add_argument('-mdo', '--min_duration_off', type=float, help="Tiempo mínimo que tienen que alcanzar los silencios o se eliminan, mismo valor tanto para Pyannote como para NeMo")   
    parser.add_argument('-mtc', '--min_cluster_size', type=int, help="Tamaño mínimo de clusters para Pyannote,si no se alcanza en alguno, se fusiona con el más similar")
    parser.add_argument('-mec', '--method_cluster', type=str, help="Método utilizado en el clustering aglomerativo para Pyannote")    
    parser.add_argument('-thr', '--threshold_cluster', type=float, help="Umbral utilizado en el clustering aglomerativo para Pyannote")    
    parser.add_argument('-ns', '--num_speakers', default=None,  type=int, help='Indicamos el numero de speakers (pero tendría que ser el mismo número en todos los archivos). Mismo valor tanto para Pyannote como para NeMo')    
    parser.add_argument('-mm', '--msdd_model', type=str, help='Indicamos el nombre del modelo Multiescala Diarization Decoder para NeMo')
    parser.add_argument('-wl', '--window_lengths', type=str, help='Lista de longitudes de ventana para el modelo Multiscale Diarization Decoder para NeMo')    

    parser.add_argument('-hp', '--hypotheses_path', type=str, help='Ruta de la carpeta con archivos rttm hipotesis.') 
    parser.add_argument('-rp', '--reference_path', type=str, help='Ruta de la carpeta con archivos rttm de referencia si disponemos de ellos (necesarios si se selecciona `oracle_vad` en la pipeline NeMo )')    
    parser.add_argument('-me', '--metrics_list', type=str, help='Lista de Metricas de Diarización a aplicar')
    parser.add_argument('-co', '--collar', type=float, default=0.0, help='Collar (Umbral de tiempo que se concede al principio y al final de cada segmento)')
    parser.add_argument('-so', '--skip_overlap', type=bool, default=False, help='Si se ignora el habla solapada o no')    
        
    args = parser.parse_args()

    logs_path = os.path.join(args.host_volume_path, "logs")
    if not os.path.exists(logs_path):
        os.makedirs( logs_path, exist_ok=True )
    logger = logging.getLogger('MAIN')
    logging.basicConfig(filename=f'{logs_path}/main_log_{datetime.now().strftime("%Y%m%d%H%M%S")}.log',
                        encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')        
    logger.info("Empezando Módulo principal...")
    print("Empezando Módulo principal...")
    
    if args.converter:
        converter = ConverterToAudio(args.media_path, args.media_path, os.path.join(args.host_volume_path, 'datasets'))
        converter.convert()  
        
    images_name_list = []
    if not args.no_diarize:
        if args.image_name is None:      
            images_name_list.append(DockerImages.nemo_pipeline.value)
            images_name_list.append(DockerImages.pyannote_pipeline.value)            
        elif args.image_name.lower() in [di.name for di in DockerImages.__members__.values()]:
            images_name_list.append(DockerImages._member_map_[args.image_name.lower()].value)
        else:
            for di in DockerImages.__members__.values():
                if di.name.find( args.image_name.lower()) > -1:
                    images_name_list.append(di.value)
    if not args.no_diarize or args.genera_all_rttm:            
        dockerManager = DockerDiarizationManager(host_volume_path=args.host_volume_path, container_volume_path=args.container_volume_path, 
                                             image_name_list=images_name_list)     
    if args.genera_all_rttm:
        dockerManager.run_converter_rttm_container(image_name='dasaenzd/converter_subtitles:latest', container_name='converter_java_subtitles', delta=args.delta)
    
    if not args.no_diarize:    
        params = {}
        for img in images_name_list:
            if img == DockerImages.pyannote_pipeline.value:
                params['pipeline_version'] = args.pipeline_version
                params['huggingface_token'] = args.huggingface_token
                
                if args.segmentation_model is not None: #Pyannote
                    if args.segmentation_model.lower() in [sm.name for sm in SegmentationModels.__members__.values()]:
                        params['segmentation_model'] = SegmentationModels._member_map_[args.segmentation_model.lower()].model
                    elif args.segmentation_model.lower() in [sm.model for sm in SegmentationModels.__members__.values()]:
                        params['segmentation_model'] = args.segmentation_model.lower()     
                    else:
                        for sm in SegmentationModels.__members__.values():
                            if args.segmentation_model.lower() == sm.model.split('/')[1]:
                                params['segmentation_model'] = args.segmentation_model.lower()
                    
                if args.speaker_model_pyannote is not None: #Ambos
                        if args.speaker_model_pyannote.upper() in [sp.name for sp in SpeakerModelPyannote.__members__.values()]:
                            params['speaker_model_pyannote'] = SpeakerModelPyannote._member_map_[args.speaker_model_pyannote.upper()].model
                        elif args.speaker_model_pyannote.lower() in [sp.model for sp in SpeakerModelPyannote.__members__.values()]:
                                params['speaker_model_pyannote'] = args.speaker_model_pyannote.lower()
                        else:
                            for sp in SpeakerModelPyannote.__members__.values():
                                if args.speaker_model_pyannote.lower()==sp.model.split('/')[1]:
                                    params['speaker_model_pyannote'] =sp.model
                
                params['method_cluster'] = args.method_cluster
                if args.min_cluster_size is not None:
                    if type(args.min_cluster_size) != int:                
                        print("Mínimo tamaño de cluster debe ser un entero!")    
                    else:    
                        params['min_cluster_size'] = str(args.min_cluster_size)                
                if args.threshold_cluster is not None:
                    if type(args.threshold_cluster) != float:                
                        print("Umbral de cluster debe ser un número decimal!")    
                    else:    
                        params['threshold_cluster'] = str(args.threshold_cluster)
                
            if img == DockerImages.nemo_pipeline.value:                            
                if args.vad_model is not None:  #Nemo
                    if args.vad_model.upper() in [vm.name for vm in VADModels.__members__.values()]:
                        params['vad_model'] = VADModels._member_map_[args.vad_model.upper()].model
                    elif args.vad_model.lower() in [vm.model for vm in VADModels.__members__.values()]:
                        params['vad_model'] = args.vad_model.lower() 
                         
                if args.speaker_model_nemo is not None: #Ambos
                    if args.speaker_model_nemo.upper() in [sp.name for sp in SpeakerModelNemo.__members__.values()]:
                        params['speaker_model_nemo'] = SpeakerModelNemo._member_map_[args.speaker_model_nemo.upper()].model
                    elif args.speaker_model_nemo.lower() in [sp.model for sp in SpeakerModelNemo.__members__.values()]:
                        params['speaker_model_nemo'] = args.speaker_model_nemo.lower()
                        
                if args.msdd_model is not None:    #Nemo
                    if args.msdd_model.upper() in [msd.name for msd in MSDDModels.__members__.values()]:
                        params['msdd_model'] = MSDDModels._member_map_[args.msdd_model.upper()].model
                    else:    
                        msd_set = {msd.model for msd in MSDDModels.__members__.values() if msd.model.find(args.msdd_model.lower()) > -1}
                        if len(msd_set) == 1:
                            params['msdd_model'] = list(msd_set)[0]
                
                params['window_lengths'] = args.window_lengths
                params['reference_path'] = '/data/rttm_ref'  # Pasamos el valor de la carpeta en el contenedor con los rttm de referencia              
            
            if args.min_duration_off is not None and not 'min_duration_off' in params:
                params['min_duration_off'] = str(args.min_duration_off)
                
            if args.num_speakers is not None and not 'num_speakers' in params:
                if type(args.num_speakers) != int:
                    print("Número de speakers debe ser un entero!")
                else:    
                    params['num_speakers'] = str(args.num_speakers)  
            #else:        
            #    params['num_speakers'] = None
                
            call_manager_to_execute_container(img, params)
        
    if args.hypotheses_path is None or not os.path.exists(args.hypotheses_path): 
        args.hypotheses_path = os.path.join(args.host_volume_path, "rttm")
        
    if args.reference_path is None or not os.path.exists(args.reference_path):  #args.reference_path es usada para el cálculo de métricas
        args.reference_path = os.path.join(os.path.curdir, "subtitles/data/rttm_ref")
        
    if args.metrics_list is not None and len(args.metrics_list)>0:
        if os.path.exists(args.hypotheses_path) and os.path.exists(args.reference_path):
            metrics_calc = MetricsCalculator(hypotheses_path=args.hypotheses_path, reference_path = args.reference_path, metrics_list = args.metrics_list, 
                            collar=args.collar, skip_overlap = args.skip_overlap)
            metrics_calc.calculate_and_write_metrics()            
        else:
            print("No existe la carpeta de archivos RTTM de hipótesis o la carpeta de archivos de referencia. NO se pueden calcular las métricas.")        
    exit(0)