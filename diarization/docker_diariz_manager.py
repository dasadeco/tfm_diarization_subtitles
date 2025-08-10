import argparse
import docker
import os
from pathlib import Path
import logging
import time
from datetime import datetime
from enum import Enum
from docker.models.containers import Container

from pyannote_import import SpeakerModels as SpeakerModelPyannote, SegmentationModels, ClusteringMethods
from nemo_import import SpeakerModels as SpeakerModelNemo, VADModels, MSDDModels

STATUS_FILE = 'status.txt'
FIN="FIN"

class DockerImages(Enum):
    pyannote_pipeline ='dasaenzd/pyannote_pipeline:latest'
    nemo_pipeline = 'dasaenzd/nemo_pipeline:latest'
    speechbrain_pipeline = 'dasaenzd/speechbrain_pipeline:latest'

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
        logging.basicConfig(filename=f'{logs_path}/docker_manager_{datetime.now().strftime("%Y%m%d%H%M%S")}.log', force=True,
                            encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        self.logger = logging.getLogger(__name__)
        self.logger.info("Inicializando el MANAGER DE DOCKER para Diarización !!!!")        
        
        self.client = docker.from_env()  # Docker Engine o Docker Desktop necesitan estar arrancados              
        self.container_volume_path = container_volume_path
        self.containers = {}   # Diccionario de contenedores de los que este manager se va a hacer cargo
        binding = {}
        if image_name_list is not None and len(image_name_list)>0:
            for image_name in image_name_list:
                if type(image_name) == DockerImages:
                    self.image_name = image_name.value
                else:
                    self.image_name = image_name
                container_name = self.image_name.split('/')[1].split(':')[0]            
                try:
                    if not self.host_volume_path in binding:
                        binding[self.host_volume_path] = {"bind" : container_volume_path, "mode" : "rw"}            
                    ## Si el container es de NeMo podría hacer falta un segundo binding ./subtitles/data:/data para los RTTM referenciados en el caso de usar Oracle-VAD
                    if container_name == DockerImages.nemo_pipeline.name:       
                        host_volume_rttm_ref_path = Path('./subtitles/data').absolute() 
                        container_volume_rttm_ref_path = '/data'                        
                        if not host_volume_rttm_ref_path in binding: 
                            binding[host_volume_rttm_ref_path] = {"bind" : container_volume_rttm_ref_path, "mode" : "rw"}  
                    image = self._get_or_pull_image(self.client, self.image_name)                                    
                    self.containers[container_name] = self.run_container(image.tags[0], container_name, binding)    
                except docker.errors.ImageNotFound as e:
                    print(f"Image not found: {e}")
                    self.logger.error(f"Image not found: {container_name} : {e}")
                    exit(1)
                except docker.errors.APIError as e:
                    print(f"API error: {e}")
                    self.logger.error(f"API error: {container_name} : {e}")    
                    exit(1)
                except Exception as e:
                    print(f"An error occurred: {e}")
                    self.logger.error(f"An error occurred: {container_name} : {e}")
                    exit(1)
            

    def stop_if_running(self, container_name):
        try:
            container = self.client.containers.get(container_name)
            self.logger.info(f"Status del contenedor {container_name}: {container.status}")
            print(f"Status del contenedor {container_name}: {container.status}")
            if container.status == 'running':
                self.logger.info(f"Deteniendo el contenedor {container_name} ...")
                print(f"Deteniendo el contenedor {container_name} ...")
                container.stop()
                self.logger.info(f"Contenedor {container_name} detenido.")
                print(f"Contenedor {container_name} detenido.")
            container.remove(force=True)    
        except docker.errors.NotFound:            
            self.logger.info(f"Contenedor {container_name} no está ejecutandose ahora.")
            print(f"Contenedor {container_name} no está ejecutandose ahora.")
        except Exception as e:
            self.logger.error(f"Un error ha ocurrido mienstras se detenía el contenedor: {e}")
            print(f"Un error ha ocurrido mienstras se detenía el contenedor: {e}")            
            exit(1)     

    def run_container(self, image_name: str, container_name:str, volume_binding=None, command=None, detach=True):        
        try:
            self.stop_if_running(container_name)
            container = self.client.containers.run(image_name, name=container_name, 
                                                   volumes=volume_binding, command=command, detach=detach)
            if isinstance(container, Container):
                self.logger.info(f"Contenedor {container_name} iniciado con ID: {container.id}")
            else:    
                self.logger.info(f"Contenedor {container_name} iniciado.")
            return container
        except docker.errors.ContainerError as e:
            print(f"Error en Contenedor: {e}")
            self.logger.error(f"Error en Contenedor: {e}")
            exit(1)
        except docker.errors.ImageNotFound as e:
            print(f"Imagen no encontrada: {e}")
            self.logger.error(f"Imagen no encontrada: {e}")
            exit(1)
        except Exception as e:
            print(f"An error occurred: {e}")
            self.logger.error(f"An error occurred: {e}")
            exit(1)

   
    ## En principio este contenedor tiene parámetros fijos, a excepción del valor de delta, se reutiliza `run_container` para ejecutar un contenedor
    ## 
    def run_converter_rttm_container(self, image_name:str='dasaenzd/converter_java_subtitles:latest', container_name:str='converter_java_subtitles', delta=0.0):
        binding = {}            
        host_volume_converter_path = Path('./subtitles/data').absolute() 
        if not os.path.exists(host_volume_converter_path):
            print(f"No se ha encontrado la ruta compartida en el host para subtitulos!!: {host_volume_converter_path}")
            self.logger.error(f"No se ha encontrado la ruta compartida en el host para subtitulos!!: {host_volume_converter_path}")
            exit(1)
        container_volume_converter_path =  '/data'                        
        binding[host_volume_converter_path] = {"bind" : container_volume_converter_path, "mode" : "rw"}  
        image = self._get_or_pull_image(self.client, image_name)
        self.run_container(image.tags[0], container_name, binding, command="-d="+str(delta), detach=False)


    # Este método puede ejecutar más de un contenedor distinto con sus parámetros correspondientes   
    def execute_command(self, container_name, params:dict): 
        try:
            with open(os.path.join(self.host_volume_path, container_name+'_'+STATUS_FILE), 'w', encoding="utf-8") as status_file:
                status_file.write('Inicializado el archivo de estado')
                self.logger.info('Inicializado el archivo de estado')
                status_file.close()
            cmd_list = ["python", container_name + ".py", "--volume_path", self.container_volume_path]
            if container_name == DockerImages.pyannote_pipeline.name:
                if 'pipeline_version' in params and params['pipeline_version'] is not None:
                    cmd_list.extend([ "--pipeline_version", params['pipeline_version'] ])
                if 'huggingface_token' in params and params['huggingface_token'] is not None:
                    cmd_list.extend([ "--huggingface_token", params['huggingface_token'] ])  
                if 'segmentation_model' in params and params['segmentation_model'] is not None:                    
                    cmd_list.extend([ "--segmentation_model", params['segmentation_model'] ]) 
                if 'speaker_model_pyannote' in params and params['speaker_model_pyannote'] is not None:
                    cmd_list.extend([ "--speaker_model", params['speaker_model_pyannote'] ])
                if 'min_cluster_size' in params and params['min_cluster_size'] is not None:
                    cmd_list.extend([ "--min_cluster_size", params['min_cluster_size'] ])
                if 'method_cluster' in params and params['method_cluster'] is not None:
                    cmd_list.extend([ "--method_cluster", params['method_cluster'] ])
                if 'threshold_cluster' in params and params['threshold_cluster'] is not None:
                    cmd_list.extend([ "--threshold_cluster", params['threshold_cluster'] ])                    
                                       
            elif container_name == DockerImages.nemo_pipeline.name:
                if 'vad_model' in params and params['vad_model'] is not None:
                    cmd_list.extend([ "--vad_model", params['vad_model'] ])
                if 'speaker_model_nemo' in params and params['speaker_model_nemo'] is not None:
                    cmd_list.extend([ "--speaker_model", params['speaker_model_nemo'] ])
                if 'reference_path' in params and params['reference_path'] is not None:
                    cmd_list.extend([ "--reference_path", params['reference_path'] ])
                if 'msdd_model' in params and params['msdd_model'] is not None:
                    cmd_list.extend([ "--msdd_model", params['msdd_model'] ])
                if 'window_lengths' in params and params['window_lengths'] is not None:
                    cmd_list.extend([ "--window_lengths", params['window_lengths'] ])                    

            else:
                print(f"No se ha podido preparar un comando de ejecución al contenedor {container_name}")
                self.logger.info(f"No se ha podido preparar un comando de ejecución al contenedor {container_name}")
                exit(1)
                
            if 'min_duration_off' in params and params['min_duration_off'] is not None:
                cmd_list.extend([ "--min_duration_off", params['min_duration_off'] ])
            if 'num_speakers' in params and params['num_speakers'] is not None:
                cmd_list.extend([ "--num_speakers", params['num_speakers'] ])
            exec_command = self.client.api.exec_create(self.containers[container_name].id, cmd_list)    
            
            self.client.api.exec_start(exec_command['Id'], detach=False)
            print(f"Ejecutando comando: {exec_command} en contenedor {self.containers[container_name].name} ...")    
            self.logger.info(f"Ejecutando comando: {exec_command} en contenedor {self.containers[container_name].name} ...")            

            self._check_status_file(container_name)         
            self.stop_if_running(self.containers[container_name].name)                        
            return 0
        except docker.errors.NotFound:
            print(f"Container {self.containers[container_name].name} not found.")
            self.logger.error(f"Container {self.containers[container_name].name} not found.")
            self.stop_if_running(self.containers[container_name].name) 
            exit(1)
        except Exception or TypeError as e:
            print(f"An error occurred while executing the command: {e}")
            self.logger.error(f"An error occurred while executing the command: {e}")
            self.stop_if_running(self.containers[container_name].name) 
            exit(1)  
            
            
    def _check_status_file(self, container_name):        
                        
        def _in_process(visual_anim):
            if len(visual_anim) == 60:
                visual_anim = "_"       
            else:    
                visual_anim += "_"   
            return visual_anim        
        
        result_path = os.path.join(self.host_volume_path, container_name+'_'+STATUS_FILE)
        status = 0
        visual_anim = "_"
        while(status != FIN):
            if(os.path.exists(result_path)):
                with open(result_path, 'r') as file:
                    status = file.readline()                    
                visual_anim = _in_process(visual_anim)
                termin = '\n' if len(visual_anim) == 60 else '\r'
                print(f"Running {container_name} {visual_anim}", end=termin, flush=True)                
                time.sleep(1)
        file.close()                                
            
if __name__ == '__main__':
    speakerModels = list(SpeakerModelPyannote.__members__.values())
    speakerModels.extend(list(SpeakerModelNemo.__members__.values()))
    
    parser = argparse.ArgumentParser(description="Docker Diarization Manager")
    parser.add_argument('-hvp', '--host_volume_path', type=str, default='E:\\Desarrollo\\TFM\\data\\media', help='Path de la maquina host ( P. ej. mi Windows 10)')        
    parser.add_argument('-cvp', '--container_volume_path', type=str, default='/media', help='Path en el contenedor donde se guardan los archivos wav')
    parser.add_argument('-img', '--image_name', type=str, help='Nombre de la imagen docker de Pyannote o de NeMo')        
    parser.add_argument('-pv', '--pipeline_version', type=str, help='Versión de la Pipeline Pyannote, (sólo para efecto informativo en los logs, debe concordar con el modelo de segmentación y de embedding)')
    parser.add_argument('-hft', '--huggingface_token', type=str, help='Token de Huggingface para Pyannote')
    parser.add_argument('-vad', '--vad_model', type=str, help='Indicamos el nombre del modelo VAD a utilizar para NeMo')
    parser.add_argument('-sem', '--segmentation_model', type=str, help="Modelo de segmentacion para Pyannote")
    parser.add_argument('-sm', '--speaker_model', help='Indicamos el nombre del modelo para obtener embeddings a utilizar para Pyannote o para NeMo')
    parser.add_argument('-mdo', '--min_duration_off', type=float, help="Tiempo mínimo que tienen que alcanzar los silencios o se eliminan, para Pyannote o para NeMo")    
    parser.add_argument('-mtc', '--min_cluster_size', type=int, help="Tamaño mínimo de clusters,si no se alcanza en alguno, se fusiona con el más similar, para Pyannote")
    parser.add_argument('-mec', '--method_cluster', type=str, help="Método utilizado en el clustering aglomerativo para Pyannote")
    parser.add_argument('-thr', '--threshold_cluster', type=float, help="Método utilizado en el clustering aglomerativo para Pyannote")
    parser.add_argument('-ns', '--num_speakers', default=None, type=int, help='Indicamos el numero de speakers (pero tendría que ser el mismo número en todos los archivos tanto para Pyannote como para NeMo)')    
    parser.add_argument('-mm', '--msdd_model', type=str, help='Indicamos el nombre del modelo Multiescala Diarization Decoder para NeMo')
    parser.add_argument('-wl', '--window_lengths', type=str, help='Lista de longitudes de ventana para el modelo Multiscale Diarization Decoder para NeMo')    
    parser.add_argument('-rp', '--reference_path', type=str, help='Ruta de la carpeta con archivos rttm de referencia si disponemos de ellos y se selecciona `oracle_vad` para NeMo')
    
    args = parser.parse_args()

    images_name_list = []
    if args.image_name is None:      
            images_name_list.append(DockerImages.nemo_pipeline.value)
            images_name_list.append(DockerImages.pyannote_pipeline.value)            
    elif args.image_name.lower() in [di.name for di in DockerImages.__members__.values()]:
            images_name_list.append(DockerImages._member_map_[args.image_name.lower()].value)
    elif args.image_name.lower() in [di.value for di in DockerImages.__members__.values()]:
            images_name_list.append(args.image_name.lower())                            
    else:
        for di in DockerImages.__members__.values():
            if di.name.find( args.image_name.lower()) > -1:
                 images_name_list.append(di.value)
    container_name = None                 
    if len(images_name_list) == 1:
        container_name =  images_name_list[0].split('/')[1].split(':')[0]             
    dockerManager = DockerDiarizationManager(host_volume_path=args.host_volume_path, container_volume_path=args.container_volume_path, 
                                             image_name_list=[images_name_list])                     
    params = {}
    if args.pipeline_version is not None: #Pyannote
        params['pipeline_version'] = args.pipeline_version
        
    if args.huggingface_token is not None: #Pyannote
        params['huggingface_token'] = args.huggingface_token
        
    if args.vad_model is not None:  #Nemo
        if args.vad_model.upper() in [vm.name for vm in VADModels.__members__.values()]:
            params['vad_model'] = VADModels._member_map_[args.vad_model.upper()].model
        elif args.vad_model.lower() in [vm.model for vm in VADModels.__members__.values()]:
            params['vad_model'] = args.vad_model.lower()     
        
    if args.segmentation_model is not None: #Pyannote
        if args.segmentation_model.lower() in [sm.name for sm in SegmentationModels.__members__.values()]:
            params['segmentation_model'] = SegmentationModels._member_map_[args.segmentation_model.lower()].model
        elif args.segmentation_model.lower() in [sm.model for sm in SegmentationModels.__members__.values()]:
            params['segmentation_model'] = args.segmentation_model.lower()     
        else:
            for sm in SegmentationModels.__members__.values():
                if args.segmentation_model.lower() == sm.model.split('/')[1]:
                    params['segmentation_model'] = args.segmentation_model.lower()
        
    if args.speaker_model is not None: #Ambos
        speak_models = args.speaker_model.split(',')
        for speak_model in speak_models:
            if speak_model.upper() in [sp.name for sp in SpeakerModelPyannote.__members__.values()]:
                params['speaker_model_pyannote'] = SpeakerModelPyannote._member_map_[speak_model.upper()].model
            elif speak_model.upper() in [sp.name for sp in SpeakerModelNemo.__members__.values()]:
                params['speaker_model_nemo'] = SpeakerModelNemo._member_map_[speak_model.upper()].model
            elif speak_model.lower() in [sp.model for sp in SpeakerModelPyannote.__members__.values()]:
                    params['speaker_model_pyannote'] = speak_model.lower()
            elif speak_model.lower() in [sp.model for sp in SpeakerModelNemo.__members__.values()]:
                params['speaker_model_nemo'] = speak_model.lower()
            else:
                for sp in SpeakerModelPyannote.__members__.values():
                    if speak_model.lower()==sp.model.split('/')[1]:
                        params['speaker_model_pyannote'] =sp.model
                    
    if args.min_duration_off is not None:  #Ambos
        if type(args.min_duration_off) != float:
            print("Duración mínima debe ser un real!")
        else:
            params['min_duration_off'] = args.min_duration_off            
    if args.min_cluster_size is not None: #Pyannote
        if type(args.min_cluster_size) != int:
            print("Mínimo tamaño de cluster debe ser un entero!")
        else:
            params['min_cluster_size'] = str(args.min_cluster_size)
    if args.method_cluster is not None:  #Pyannote
        if args.method_cluster.lower() in [cm.value for cm in ClusteringMethods.__members__.values()]:
            params['method_cluster'] = args.method_cluster.lower()
        
    if args.threshold_cluster is not None: #Pyannote
        if type(args.threshold_cluster) != float:
            print("Umbral de clustering debe ser un real!")
        else:
            params['threshold_cluster'] = args.threshold_cluster
    if args.num_speakers is not None:  #Ambos
        if type(args.num_speakers) != int:
            print("Número de speakers debe ser un entero!")
        else:
            params['num_speakers'] = str(args.num_speakers)
            
    if args.msdd_model is not None:    #Nemo
        if args.msdd_model.upper() in [msd.name for msd in MSDDModels.__members__.values()]:
            params['msdd_model'] = MSDDModels._member_map_[args.msdd_model.upper()].model
        else:    
            msd_set = {msd.model for msd in MSDDModels.__members__.values() if msd.model.find(args.msdd_model.lower()) > -1}
            if len(msd_set) == 1:
                params['msdd_model'] = list(msd_set)[0]
        
    if args.reference_path is not None: #Nemo
        params['reference_path'] = args.reference_path

    if args.window_lengths is not None: #Nemo
        params['window_lengths'] = [i.lstrip(' ').rstrip(' ') for i in args.window_lengths.lstrip('[').rstrip(']').split(',')]
    
    if container_name is not None: 
        dockerManager.execute_command(container_name, params)
    else:
        for container_name in dockerManager.containers.keys():
            dockerManager.execute_command(container_name, params)
    exit(0)