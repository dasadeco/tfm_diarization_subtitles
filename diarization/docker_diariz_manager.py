import sys
import docker

class DockerDiarizationManager: 
    def __init__(self, host_volume_path='/data/media', container_volume_path='/media'):        
        self.client = docker.from_env()        
        self.host_volume_path = host_volume_path
        self.container_volume_path = container_volume_path
        
        def init_container(self, image_name: str = 'dasaenzd/pyannote.audio-test1:latest'):
            self.image_name = image_name
            
            try:
                if not image_name.startswith('dasaenzd/'):
                    image = self.client.images.pull(self.image_name)                    
                    self.run_container(image.tag, 'container_'+image.tag)    
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