import sys
import argparse
import docker
import os
from pathlib import Path
import logging
import time
from datetime import datetime
from enum import Enum
from docker.models.containers import Container

## Esto podría estar en una clase que inicie todo el paquete, y no delegar esta responsabilidad al Docker manager

STATUS_FILE = 'status.txt'
FIN="FIN"

class DockerImages(Enum):
    pyannote_pipeline ='dasaenzd/pyannote_pipeline:latest'
    nemo_pipeline = 'dasaenzd/nemo_pipeline:latest'

class DockerDiarizationManager: 
    
    def _get_or_pull_image(self, client, image_name):
     try:
        return client.images.get(image_name)
     except docker.errors.ImageNotFound:
        return client.images.pull(image_name)
    
    def __init__(self, image_name_list, host_volume_path, container_volume_path='/media'):
        self.host_volume_path = Path(host_volume_path).absolute()          
        logs_path = os.path.join(self.host_volume_path, "logs")
        if not os.path.exists(logs_path):
            os.makedirs( logs_path, exist_ok=True)        
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(filename=f'{logs_path}/docker_manager_{datetime.now().strftime("%Y%m%d%H%M%S")}.log',
                            encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')        
        self.logger.info("Inicializando el MANAGER DE DOCKER para  Diarización !!!!")        
        
        self.client = docker.from_env()                
        self.container_volume_path = container_volume_path
        self.containers = {}   # Diccionario de contenedores de los que este manager se va a hacer cargo
        if image_name_list is not None and len(image_name_list)>0:
            for image_name in image_name_list:
                if type(image_name) == DockerImages:
                    self.image_name = image_name.value
                else:
                    self.image_name = image_name
                container_name = self.image_name.split('/')[1].split(':')[0]            
                try:
                    binding = {}
                    binding[self.host_volume_path] = {"bind" : container_volume_path, "mode" : "rw"}            
                    ## Si el container es de NeMo podría hacer falta un segundo binding ./subtitles/data:/data para los RTTM referenciados en el caso de usar Oracle-VAD
                    if container_name == DockerImages.nemo_pipeline.name:       
                        host_volume_rttm_ref_path = Path('./subtitles/data').absolute() 
                        container_volume_rttm_ref_path = '/data'                        
                        binding[host_volume_rttm_ref_path] = {"bind" : container_volume_rttm_ref_path, "mode" : "rw"}  
                    image = self._get_or_pull_image(self.client, self.image_name)                                    
                    self.containers[container_name] = self.run_container(image.tags[0], container_name, binding)    
                except docker.errors.ImageNotFound as e:
                    print(f"Image not found: {e}")
                    self.logger.error(f"Image not found: {container_name} : {e}")
                    sys.exit(1)
                except docker.errors.APIError as e:
                    print(f"API error: {e}")
                    self.logger.error(f"API error: {container_name} : {e}")    
                    sys.exit(1)
                except Exception as e:
                    print(f"An error occurred: {e}")
                    self.logger.error(f"An error occurred: {container_name} : {e}")
                    sys.exit(1)
            

    def stop_if_running(self, container_name):
        try:
            container = self.client.containers.get(container_name)
            if container.status == 'running':
                self.logger.info(f"Stopping container {container_name} ...")
                container.stop()
                self.logger.info(f"Container {container_name} stopped.")
            container.remove(force=True)    
        except docker.errors.NotFound:
            print(f"Container {container_name} not found. No need to stop.")
            self.logger.info(f"Container {container_name} not found. No need to stop.")
        except Exception as e:
            print(f"An error occurred while stopping the container: {e}")            
            self.logger.error(f"An error occurred while stopping the container: {e}")
            sys.exit(1)     

    def run_container(self, image_name: str, container_name:str, volume_binding=None, command=None, detach=True):        
        try:
            self.stop_if_running(container_name)
            container = self.client.containers.run(image_name, name=container_name, 
                                                   volumes=volume_binding, command=command, detach=detach)
            if isinstance(container, Container):
                self.logger.info(f"Container {container_name} started with ID: {container.id}")
            else:    
                self.logger.info(f"Container {container_name} started.")
            return container
        except docker.errors.ContainerError as e:
            print(f"Container error: {e}")
            self.logger.error(f"Container error: {e}")
            sys.exit(1)
        except docker.errors.ImageNotFound as e:
            print(f"Image not found: {e}")
            self.logger.error(f"Image not found: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred: {e}")
            self.logger.error(f"An error occurred: {e}")
            sys.exit(1)
   
    ## En principio este contenedor tiene parámetros fijos, a excepción del valor de delta, se reutiliza `run_container` para ejecutar un contenedor
    ## 
    def run_converter_rttm_container(self, image_name:str='dasaenzd/converter_java_subtitles:latest', container_name:str='converter_java_subtitles', 
                                     volume_binding=None, delta=0.0):
        if volume_binding is None:
            binding = {}
            host_volume_converter_path = Path('./subtitles/data').absolute() 
            container_volume_converter_path =  '/data'                        
            binding[host_volume_converter_path] = {"bind" : container_volume_converter_path, "mode" : "rw"}  
        image = self._get_or_pull_image(self.client, image_name)                                    
        #self.containers[container_name] = self.run_container(image.tags[0], container_name, binding, command="-d="+str(delta), detach=False)            
        self.run_container(image.tags[0], container_name, binding, command="-d="+str(delta), detach=False)

    # Este método puede ejecutar más de un contenedor distinto con sus parámetros correspondientes   
    def execute_command(self, container_name, params:dict): 
        try:
            with open(os.path.join(self.host_volume_path, STATUS_FILE), 'w', encoding="utf-8") as status_file:
                status_file.write('Inicializado el archivo de estado')
                self.logger.info('Inicializado el archivo de estado')
                status_file.close                                      
            if container_name == DockerImages.pyannote_pipeline.name:
                exec_command = self.client.api.exec_create(self.containers[container_name].id, 
                          ["python", container_name + ".py", "--pipeline_model", params['pipeline_model'], "--huggingface_token", params['huggingface_token'], 
                           "--volume_path", self.container_volume_path])
            elif container_name == DockerImages.nemo_pipeline.name:       
                if not 'num_speakers' in params:
                    exec_command = self.client.api.exec_create(self.containers[container_name].id, 
                          ["python", container_name + ".py", "--vad_model", params['vad_model'], "--speaker_model", params['speaker_model'],
                           "--reference_path", params['reference_path'], "--volume_path", self.container_volume_path])
                else:  
                    exec_command = self.client.api.exec_create(self.containers[container_name].id, 
                          ["python", container_name + ".py", "--vad_model", params['vad_model'], "--speaker_model", params['speaker_model'],
                           "--reference_path", params['reference_path'], "--num_speakers", params['num_speakers'], "--volume_path", self.container_volume_path])
            else:
                print(f"No se ha podido preparar un comando de ejecución al contenedor {container_name}")
                self.logger.info(f"No se ha podido preparar un comando de ejecución al contenedor {container_name}")
                exit(1)
            self.client.api.exec_start(exec_command['Id'], detach=False)
            print(f"Ejecutando comando: {exec_command} en contenedor {self.containers[container_name].name} ...")    
            self.logger.info(f"Ejecutando comando: {exec_command} en contenedor {self.containers[container_name].name} ...")            

            self._check_status_file()         
            self.stop_if_running(self.containers[container_name].name)                        
            return 0
        except docker.errors.NotFound:
            print(f"Container {self.containers[container_name].name} not found.")
            self.logger.error(f"Container {self.containers[container_name].name} not found.")
            self.stop_if_running(self.containers[container_name].name) 
            sys.exit(1)
        except Exception or TypeError as e:
            print(f"An error occurred while executing the command: {e}")
            self.logger.error(f"An error occurred while executing the command: {e}")
            self.stop_if_running(self.containers[container_name].name) 
            sys.exit(1)  
            
            
    def _check_status_file(self):        
                        
        def _in_process(visual_anim):
            if len(visual_anim) == 60:
                visual_anim = "_"       
            else:    
                visual_anim += "_"   
            return visual_anim        
        
        result_path = os.path.join(self.host_volume_path, STATUS_FILE)
        status = 0
        visual_anim = "_"
        while(status != FIN):
            if(os.path.exists(result_path)):
                with open(result_path, 'r') as file:
                    status = file.readline()                    
                visual_anim = _in_process(visual_anim)
                termin = '\n' if len(visual_anim) == 60 else '\r'
                print(f"Running {visual_anim}", end=termin, flush=True)                
                time.sleep(1)
        file.close()          
                        
    
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Docker Diarization Manager")
    parser.add_argument('-hvp', '--host_volume_path', type=str, default='E:\\Desarrollo\\TFM\\data\\media', help='Path de la maquina host ( P. ej. mi Windows 10)')        
    parser.add_argument('-cvp', '--container_volume_path', type=str, default='/media', help='Path en el contenedor donde se guardan los archivos wav')
    parser.add_argument('-img', '--image_name', type=str, default='dasaenzd/pyannote_pipeline:latest', help='Nombre de la imagen docker')        
    #parser.add_argument('-par', '--params', type=str,  help='Parámetros propios para el script ') 
    parser.add_argument('-pm', '--pipeline_model', type=str, help='Versión de la Pipeline Pyannote')
    parser.add_argument('-hft', '--huggingface_token', type=str, help='Token de Huggingface')
    parser.add_argument('-vad', '--vad_model', type=str, help='Indicamos el nombre del modelo VAD a utilizar')
    parser.add_argument('-sm', '--speaker_model', type=str, help='Indicamos el nombre del modelo para obtener embeddings a utilizar')
    parser.add_argument('-rp', '--reference_path', type=str, help='Ruta de la carpeta con archivos rttm de referencia si disponemos de ellos y se selecciona `oracle_vad`')
    parser.add_argument('-ns', '--num_speakers', default=None,  type=int, help='Indicamos el numero de speakers (pero tendría que ser el mismo número en todos los archivos)')
    args = parser.parse_args()

    dockerManager = DockerDiarizationManager(host_volume_path=args.host_volume_path, container_volume_path=args.container_volume_path, 
                                             image_name_list=[args.image_name]) 
    if args.image_name is not None:   
        container_name =  args.image_name.split('/')[1].split(':')[0]                     
        params = {}
        if args.pipeline_model is not None:
            params['pipeline_model'] = args.pipeline_model
        if args.huggingface_token is not None:
            params['huggingface_token'] = args.huggingface_token
        if args.vad_model is not None:
            params['vad_model'] = args.vad_model
        if args.speaker_model is not None:
            params['speaker_model'] = args.speaker_model
        if args.reference_path is not None:
            params['reference_path'] = args.reference_path
        if args.num_speakers is not None:
            if type(args.num_speakers) != int:
                print("Número de speakers debe ser un entero!")
            else:    
                params['num_speakers'] = str(args.num_speakers)
        dockerManager.execute_command(container_name, params)
    logging.disable(logging.ERROR)        
    sys.exit(0)