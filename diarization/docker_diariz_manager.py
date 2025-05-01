import sys
import argparse
import docker
from enum import Enum

class DockerImages(Enum):
    pyannote_pipeline ='dasaenzd/pyannote_pipeline:latest'


class DockerDiarizationManager: 
    def __init__(self, host_volume_path='/data/media', container_volume_path='/media', 
                 image_name = 'dasaenzd/pyannote_pipeline:latest'):        
        self.client = docker.from_env()        
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
            self.container_pyannote_pipeline = self.run_container(image.tags[0], container_name, binding)    
        except docker.errors.ImageNotFound as e:
            print(f"Image not found: {e}")
            sys.exit(1)
        except docker.errors.APIError as e:
            print(f"API error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)

    def stop_if_running(self, container_name):
        try:
            container = self.client.containers.get(container_name)
            if container.status == 'running':
                print(f"Stopping container {container_name}...")
                container.stop()
                print(f"Container {container_name} stopped.")
            container.remove(force=True)    
        except docker.errors.NotFound:
            print(f"Container {container_name} not found. No need to stop.")
        except Exception as e:
            print(f"An error occurred while stopping the container: {e}")
            sys.exit(1)     

    def run_container(self,  image_name: str, container_name:str, volume_binding=None):        
        try:
            self.stop_if_running(container_name)

            container = self.client.containers.run(image_name, name=container_name, volumes=volume_binding, detach=True)
            print(f"Container {container_name} started with ID: {container.id}")
            return container
        except docker.errors.ContainerError as e:
            print(f"Container error: {e}")
            sys.exit(1)
        except docker.errors.ImageNotFound as e:
            print(f"Image not found: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)
   
    def execute_command(self, command):
        try:
            #container = self.client.containers.get(container_name)
            exec_command = self.client.api.exec_create(self.container_pyannote_pipeline.id, ["python", command])
            output = self.client.api.exec_start(exec_command['Id'])
            return output.decode('utf-8')
        except docker.errors.NotFound:
            print(f"Container {self.container_pyannote_pipeline.name} not found.")
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred while executing the command: {e}")
            sys.exit(1)         
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Docker Diarization Manager")
    parser.add_argument('-hvp', '--host_volume_path', type=str, default='/data/media', help='Path de la maquina host ( P. ej. mi Windows 10)')        
    parser.add_argument('-cvp', '--container_volume_path', type=str, default='/media', help='Path en el contenedor donde se guardan los archivos wav')
    parser.add_argument('-img', '--image_name', type=str, default='dasaenzd/pyannote_pipeline:latest', help='Nombre de la imagen docker')    
    args = parser.parse_args()
    dockerManager = DockerDiarizationManager(host_volume_path=args.host_volume_path, container_volume_path=args.container_volume_path, image_name=args.image_name)
    dockerManager.execute_command("pyannote_pipeline.py")
    