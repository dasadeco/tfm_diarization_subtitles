from converter_audio import ConverterToAudio 
from docker_diariz_manager import DockerDiarizationManager
from docker_diariz_manager import DockerImages
from metrics import MetricsCalculator

import argparse
import os
import logging
from datetime import datetime

def call_manager_to_execute_container(image_name, params):
    container_name =  image_name.split('/')[1].split(':')[0]  ## TODO: Podría fallar si la imagen no empieza por dasaenzd? probarlo...  
    if params:
        dockerManager.execute_command(container_name, params)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Módulo principal")
    parser.add_argument('-hvp', '--host_volume_path', type=str, help='Path de la maquina host ( P. ej. mi Windows 10)')        
    parser.add_argument('-cvp', '--container_volume_path', type=str, default='/media', help='Path en el contenedor donde se guardan los archivos wav')
    parser.add_argument('-nd', '--no_diarize', action='store_true', help='Si se indica, no realiza diarización')                   
    parser.add_argument('-img', '--image_name', type=str, help='Nombre de la imagen docker cuando sólo elegimos una')    
    parser.add_argument('-pv', '--pipeline_version', type=str, help='Versión de la Pipeline Pyannote')
    parser.add_argument('-hft', '--huggingface_token', type=str, help='Token de Huggingface')
    parser.add_argument('-vad', '--vad_model', type=str, help='Indicamos el nombre del modelo VAD a utilizar')
    parser.add_argument('-sm', '--speaker_model', type=str, help='Indicamos el nombre del modelo para obtener embeddings a utilizar')    
    parser.add_argument('-ns', '--num_speakers', default=None,  type=int, help='Indicamos el numero de speakers (pero tendría que ser el mismo número en todos los archivos)')    
    parser.add_argument('-con', '--converter', action='store_true', help='Previamente, se pueden convierten archivos de audio y video al formato WAV para disponer de datasets')
    parser.add_argument('-gen_ref', '--genera_all_rttm', action='store_true', help='También previamente, si se desea, se pueden tratar los archivos de subtítulos existentes en su carpeta para convertirlos a RTTM de referencia') 
    parser.add_argument('-d', '--delta', type=int, default=0, help='(hiper)parámetro Delta para establecer cuando consideramos que termina un speech del mismo hablante')
    parser.add_argument('-hp', '--hypotheses_path', type=str, help='Ruta de la carpeta con archivos rttm hipotesis.') 
    parser.add_argument('-rp', '--reference_path', type=str, help='Ruta de la carpeta con archivos rttm de referencia si disponemos de ellos (necesarios si se selecciona `oracle_vad` en la nemo pipeline)')    
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
        converter = ConverterToAudio('.\\datasets', '.\\datasets', './data/media/datasets')
        converter.convert()  
        
    images_pipe_list = []
    if not args.no_diarize:
        if args.image_name is None:      
            images_pipe_list.append(DockerImages.nemo_pipeline.value)
            images_pipe_list.append(DockerImages.pyannote_pipeline.value)            
        else:
            images_pipe_list.append(args.image_name)
    if not args.no_diarize or args.genera_all_rttm:            
        dockerManager = DockerDiarizationManager(host_volume_path=args.host_volume_path, container_volume_path=args.container_volume_path, 
                                             image_name_list=images_pipe_list) 
    
    if args.genera_all_rttm:
        dockerManager.run_converter_rttm_container(image_name='dasaenzd/converter_subtitles:latest', container_name='converter_java_subtitles', delta=args.delta)
    
    if not args.no_diarize:    
        params = {}
        for img in images_pipe_list:
            if img == DockerImages.pyannote_pipeline.value:            
                params['pipeline_version'] = args.pipeline_version
                params['huggingface_token'] = args.huggingface_token        
            if img == DockerImages.nemo_pipeline.value:                            
                params['vad_model'] = args.vad_model
                params['speaker_model'] = args.speaker_model
                params['reference_path'] = '/data/rttm_ref'  # Pasamos el valor de la carpeta en el contenedor con los rttm de referencia              
                if args.num_speakers is not None:
                    if type(args.num_speakers) != int:
                        print("Número de speakers debe ser un entero!")
                    else:    
                        params['num_speakers'] = str(args.num_speakers)  
                else:        
                    params['num_speakers'] = None
            call_manager_to_execute_container(img, params)
        
    if args.hypotheses_path is None or not os.path.exists(args.hypotheses_path): 
        args.hypotheses_path = os.path.join(args.host_volume_path, "rttm")
        
    if args.reference_path is None or not os.path.exists(args.reference_path):  #args.reference_path es usada para el cálculo de métricas
        args.reference_path = os.path.join(os.path.curdir, "subtitles/data/rttm_ref")
        
    if args.metrics_list is not None and len(args.metrics_list)>0:
        metrics_calc = MetricsCalculator(hypotheses_path=args.hypotheses_path, reference_path = args.reference_path, metrics_list = args.metrics_list, 
                        collar=args.collar, skip_overlap = args.skip_overlap)
        metrics_calc.calculate_and_write_metrics()            
    exit(0)