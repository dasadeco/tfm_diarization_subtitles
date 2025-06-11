from converter_audio import ConverterToAudio 
from docker_diariz_manager import DockerDiarizationManager
import argparse
import os, sys, json
import logging
from datetime import datetime


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Docker Diarization Manager")
    parser.add_argument('-hvp', '--host_volume_path', type=str, default='E:\Desarrollo\TFM\data\media', help='Path de la maquina host ( P. ej. mi Windows 10)')        
    parser.add_argument('-cvp', '--container_volume_path', type=str, default='/media', help='Path en el contenedor donde se guardan los archivos wav')
    parser.add_argument('-img', '--image_name', type=str, default='dasaenzd/pyannote_pipeline:latest', help='Nombre de la imagen docker')    
    parser.add_argument('-par', '--params', type=str,  help='Parámetros propios para la ejecución de un comando en el contenedor') 
    parser.add_argument('-con', '--converter', action='store_true', help='Previamente, se pueden convierten archivos de audio y video al fomrato WAV para disponer de datasets')
    parser.add_argument('-gen_ref', '--genera_all_rttm', action='store_true', help='También previamente, si se desea, se pueden tratar los archivos de subtítulos existentes en su carpeta para convertirlos a RTTM de referencia') 
    parser.add_argument('-d', '--delta', type=int, default=0, help='(hiper)parámetro Delta para establecer cuando consideramos que termina un speech del mismo hablante')
    parser.add_argument('-hp', '--hyphoteses_path', type=str, default='E:\Desarrollo\TFM\data\media\rttm', help='Path de la carpeta con archivos rttm hipotesis.') 
    parser.add_argument('-rp', '--reference_path', type=str, default='E:\Desarrollo\TFM\subtitles\data\rttm_ref', help='Path de la carpeta con archivos rttm de referencia.')     
    parser.add_argument('-me', '--metrics', type=str, default='all', help='Lista de Metricas de Diarización a aplicar')
    parser.add_argument('-co', '--collar', type=float, default=0.0, help='Collar (Umbral de tiempo que se concede al principio y al final de cada segmento de los RTTM)')
        
    args = parser.parse_args()

    logs_path = os.path.join(args.host_volume_path, "logs")
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename=f'{logs_path}/main_log_{datetime.now().strftime("%Y%m%d%H%M%S")}.log',
                        encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')        
    logger.info("Empezando la  Diarización !!!!")                
    
    if args.converter:
        converter = ConverterToAudio('.\\datasets', '.\\datasets', './data/media/datasets')
        converter.convert()    

    dockerManager = DockerDiarizationManager(host_volume_path=args.host_volume_path, container_volume_path=args.container_volume_path, 
                                             image_name=args.image_name) 
    
    if args.genera_all_rttm:
        dockerManager.run_converter_rttm_container(image_name='dasaenzd/converter_subtitles:latest', container_name='converter_java_subtitles', delta=args.delta)
    
    if args.image_name is not None:   
        container_name =  args.image_name.split('/')[1].split(':')[0]  ## TODO: Podría fallar si la imagen no empieza por dasaenzd? probarlo...                      
        args.params = json.loads(args.params) if args.params is not None else {}
        if args.params:
            dockerManager.execute_command(container_name, args.params['version_model'], args.params['huggingface_token'])
            
    sys.exit(0)

