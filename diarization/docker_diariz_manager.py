import sys
import argparse
import docker
import os
import logging
import json
from datetime import datetime
from enum import Enum

class DockerImages(Enum):
    pyannote_pipeline ='dasaenzd/pyannote_pipeline:latest'


class DockerDiarizationManager: 
    def __init__(self, host_volume_path, container_volume_path='/media', 
                 image_name = 'dasaenzd/pyannote_pipeline:latest'):        
        self.client = docker.from_env()        
        self.container_volume_path = container_volume_path
        if type(image_name) == DockerImages:
            self.image_name = image_name.value
        else:
            self.image_name = image_name
                    
        try:
            binding = {}
            binding[host_volume_path] = {"bind" : container_volume_path, "mode" : "rw"}            
            if len(self.image_name.split('/')) >1:
                image = self.client.images.pull(self.image_name)                    
            else:
                image = self.client.images.get(self.image_name)
            container_name = image.tags[0].split('/')[1].split(':')[0] + '_container'                        
            
            self.logger = logging.getLogger(__name__)
            logs_path = os.path.join(host_volume_path, "logs")
            if not os.path.exists(logs_path):
                os.makedirs( logs_path, exist_ok=True)
            logging.basicConfig(filename=f'{logs_path}/docker_manager_{container_name}_{datetime.now().strftime("%Y%m%d%H%M%S")}.log', 
                                encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')               
            
            self.container_pyannote_pipeline = self.run_container(image.tags[0], container_name, binding)    
        except docker.errors.ImageNotFound as e:
            print(f"Image not found: {e}")
            self.logger.error(f"Image not found: {e}")
            sys.exit(1)
        except docker.errors.APIError as e:
            print(f"API error: {e}")
            self.logger.error(f"API error: {e}")    
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred: {e}")
            self.logger.error(f"An error occurred: {e}")
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

    def run_container(self,  image_name: str, container_name:str, volume_binding=None):        
        try:
            self.stop_if_running(container_name)
            container = self.client.containers.run(image_name, name=container_name, volumes=volume_binding, detach=True)
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
   
    def execute_command(self, script, param_vm, param_hft): 
        try:
            exec_command = self.client.api.exec_create(self.container_pyannote_pipeline.id, 
                          ["python", script, "--version_model", param_vm, "--huggingface_token", param_hft, "--volume_path", self.container_volume_path])
            #exec_command = self.client.api.exec_create(self.container_pyannote_pipeline.id, ["python", command])
            self.logger.info(f"Executing command: {exec_command} in container {self.container_pyannote_pipeline.name} ...")
            output = self.client.api.exec_start(exec_command['Id'])
            return output.decode('utf-8')
        except docker.errors.NotFound:
            print(f"Container {self.container_pyannote_pipeline.name} not found.")
            self.logger.error(f"Container {self.container_pyannote_pipeline.name} not found.")
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred while executing the command: {e}")
            self.logger.error(f"An error occurred while executing the command: {e}")
            sys.exit(1)         
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Docker Diarization Manager")
    parser.add_argument('-hvp', '--host_volume_path', type=str, default='E:\Desarrollo\TFM\data\media', help='Path de la maquina host ( P. ej. mi Windows 10)')        
    parser.add_argument('-cvp', '--container_volume_path', type=str, default='/media', help='Path en el contenedor donde se guardan los archivos wav')
    parser.add_argument('-img', '--image_name', type=str, default='dasaenzd/pyannote_pipeline:latest', help='Nombre de la imagen docker')    
    parser.add_argument('-par', '--params', type=str,  help='Parámetros propios para el script ') 
    args = parser.parse_args()
    dockerManager = DockerDiarizationManager(host_volume_path=args.host_volume_path, container_volume_path=args.container_volume_path, 
                                             image_name=args.image_name)
    script =  args.image_name.split('/')[1].split(':')[0] + '.py'                        
    args.params = json.loads(args.params) if args.params is not None else {}
    dockerManager.execute_command(script, args.params['version_model'], args.params['huggingface_token'])
    