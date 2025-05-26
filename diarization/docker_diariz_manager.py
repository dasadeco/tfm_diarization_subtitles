import sys
import argparse
import docker
import os
from pathlib import Path
import logging
import json
import time
from datetime import datetime
from enum import Enum


## Esto podría estar en una clase que inicie todo el paquete, y no delegar esta responsabilidad al Docker manager

STATUS_FILE = 'status.txt'
FIN="FIN"

class DockerImages(Enum):
    pyannote_pipeline ='dasaenzd/pyannote_pipeline:latest'

class DockerDiarizationManager: 
    
    def __init__(self, image_name, host_volume_path, container_volume_path='/media'):
        self.host_volume_path = Path(host_volume_path).absolute()          
        logs_path = os.path.join(self.host_volume_path, "logs")
        if not os.path.exists(logs_path):
            os.makedirs( logs_path, exist_ok=True)        
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(filename=f'{logs_path}/docker_manager_{datetime.now().strftime("%Y%m%d%H%M%S")}.log',
                            encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')        
        self.logger.info("Empezando el MANAGER DE DOCKER para  Diarización !!!!")        
        
        self.client = docker.from_env()                
        self.container_volume_path = container_volume_path
        self.containers = {}   # Diccionario de contenedores de los que este manager se va a hacer cargo
        if type(image_name) == DockerImages:
            self.image_name = image_name.value
        else:
            self.image_name = image_name
        container_name = self.image_name.split('/')[1].split(':')[0]            
        try:
            binding = {}
            binding[self.host_volume_path] = {"bind" : container_volume_path, "mode" : "rw"}            

            def get_or_pull_image(client, image_name):
                try:
                    return client.images.get(image_name)
                except docker.errors.ImageNotFound:
                    return client.images.pull(image_name)

            image = get_or_pull_image(self.client, self.image_name)                                    
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

    def run_container(self, image_name: str, container_name:str, volume_binding=None):        
        try:
            self.stop_if_running(container_name)
            container = self.client.containers.run(image_name, name=container_name, 
                                                   volumes=volume_binding, detach=True)
            self.logger.info(f"Container {container_name} started with ID: {container.id}")
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
   
    def execute_command(self, container_name, param_vm, param_hft): 
        try:
            exec_command = self.client.api.exec_create(self.containers[container_name].id, 
                          ["python", container_name + ".py", "--version_model", param_vm, "--huggingface_token", param_hft, "--volume_path", self.container_volume_path])
            #exec_command = self.client.api.exec_create(self.container_pyannote_pipeline.id, ["python", command])
            self.logger.info(f"Executing command: {exec_command} in container {self.containers[container_name].name} ...")
            self.client.api.exec_start(exec_command['Id'], detach=True)
            with open(os.path.join(self.host_volume_path, STATUS_FILE), 'w') as status_file:
                status_file.write('Inicializado el archivo de estado')
                self.logger.info('Inicializado el archivo de estado')
                status_file.close
            self._check_status_file()         
            self.stop_if_running(self.containers[container_name].name)                        
            return 0
        except docker.errors.NotFound:
            print(f"Container {self.containers[container_name].name} not found.")
            self.logger.error(f"Container {self.containers[container_name].name} not found.")
            self.stop_if_running(self.containers[container_name].name) 
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred while executing the command: {e}")
            self.logger.error(f"An error occurred while executing the command: {e}")
            self.stop_if_running(self.containers[container_name].name) 
            sys.exit(1)         
            
            
    def _check_status_file(self):        
                        
        def _in_process(visual_anim):
            if len(visual_anim) == 8:
                visual_anim="_"
            else: 
                visual_anim = visual_anim + "_"   
            return visual_anim        
        
        result_path = os.path.join(self.host_volume_path, STATUS_FILE)
        status = 0
        visual_anim = "_"
        while(status != FIN):
            if(os.path.exists(result_path)):
                with open(result_path, 'r') as file:
                    status = file.readline()                    
                visual_anim = _in_process(visual_anim)
                self.logger.info(f"{visual_anim}\n")
                print(f"{visual_anim}", end="\r")                
                time.sleep(1)
        file.close()          
                        
    
    def execute_java_command():
        pass
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Docker Diarization Manager")
    parser.add_argument('-hvp', '--host_volume_path', type=str, default='E:\Desarrollo\TFM\data\media', help='Path de la maquina host ( P. ej. mi Windows 10)')        
    parser.add_argument('-cvp', '--container_volume_path', type=str, default='/media', help='Path en el contenedor donde se guardan los archivos wav')
    parser.add_argument('-img', '--image_name', type=str, default='dasaenzd/pyannote_pipeline:latest', help='Nombre de la imagen docker')    
    parser.add_argument('-par', '--params', type=str,  help='Parámetros propios para el script ') 
    parser.add_argument('-con', '--converter', action='store_true', help='Previamente, se convierten archivos de audio y video al fomrato WAV para disponer de datasets')
    args = parser.parse_args()
                       
    dockerManager = DockerDiarizationManager(host_volume_path=args.host_volume_path, container_volume_path=args.container_volume_path, 
                                             image_name=args.image_name) 
    if args.image_name is not None:   
        container_name =  args.image_name.split('/')[1].split(':')[0]  ## TODO: Podría fallar si la imagen no empieza por dasaenzd? probarlo...                      
        args.params = json.loads(args.params) if args.params is not None else {}
        if args.params:
            dockerManager.execute_command(container_name, args.params['version_model'], args.params['huggingface_token'])
    logging.disable(logging.ERROR)        
    sys.exit(0)