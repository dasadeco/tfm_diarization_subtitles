import sys
import argparse
import docker
from enum import Enum

class DockerImages(Enum):
    pyannote_pipeline ='dasaenzd/pyannote.audio-test1:0.1'


class DockerDiarizationManager: 
    def __init__(self, host_volume_path='/data/media', container_volume_path='/media', 
                 image_name = 'dasaenzd/pyannote.audio-test1:0.1'):        
        self.client = docker.from_env()        
        self.host_volume_path = host_volume_path
        self.container_volume_path = container_volume_path                    
        if type(image_name) == DockerImages:
            self.image_name = image_name.value
        else:
            self.image_name = image_name
        
        try:
            if not image_name.startswith('dasaenzd/'):
                image = self.client.images.pull(self.image_name)                    
                self.run_container(image.tag, 'container_'+image.tag)    
            else:
                image = self.client.images.get(self.image_name)                    
                self.run_container(image.tags[0], 'container_'+image.tags[0])    
        except docker.errors.ImageNotFound as e:
            print(f"Image not found: {e}")
            sys.exit(1)
        except docker.errors.APIError as e:
            print(f"API error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)

    def run_container(self,  image_name: str, container_name:str, volume_binding:dict={'/data/media':{'bind:':'/media', 'mode':'rw'}}):
        try:
            container = self.client.containers.run(image_name, name=container_name, volumes=volume_binding, detach=True, auto_remove=True)
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
            
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Docker Diarization Manager")
    parser.add_argument('-hvp', '--host_volume_path', type=str, default='/data/media', help='Path de la maquina host ( P. ej. mi Windows 10)')        
    parser.add_argument('-cvp', '--container_volume_path', type=str, default='/media', help='Path en el contenedor donde se guardan los archivos wav')
    parser.add_argument('-img', '--image_name', type=str, default='dasaenzd/pyannote.audio-test1:0.1', help='Nombre de la imagen docker')    
    args = parser.parse_args()
    dockerManager = DockerDiarizationManager(host_volume_path=args.host_volume_path, container_volume_path=args.container_volume_path, image_name=args.image_name)
    