from moviepy import AudioFileClip
from pydub import AudioSegment
import os, shutil
import argparse
import logging
from datetime import datetime

class ConverterToAudio:
    def __init__(self, video_media_path, audio_media_path, output_media_path = './data/media/datasets'):
        self.video_media_path = video_media_path
        self.audio_media_path = audio_media_path
        self.output_media_path = output_media_path
        self.logger = logging.getLogger(__name__)
        logs_path = os.path.join(self.output_media_path, os.path.pardir, "logs")
        if not os.path.exists(logs_path):
            os.makedirs( logs_path, exist_ok=True )
        logging.basicConfig(filename=f'{logs_path}/converter_audio_{datetime.now().strftime("%Y%m%d%H%M%S")}.log', 
                                encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')           
              
        
    def convert(self):
        
       def _buscar_by_extension_in_dataset(path, extension):
            resultados = []
            for carpeta_actual, subcarpetas, archivos in os.walk(path):
                # Obtener el nombre de la carpeta actual
                nombre_carpeta = os.path.basename(carpeta_actual)
                for archivo in archivos:
                    if archivo.lower().endswith(extension):
                        resultados.append((archivo, nombre_carpeta))
            return resultados
        
       try:
        if self.audio_media_path is None:
            # Si no se proporciona una carpeta de audio destino, se crea una por defecto si no está ya creada
            audio_media_path = os.path.join(os.getcwd(), 'audio')
            if not os.path.exists(audio_media_path):
                os.mkdir(audio_media_path)
                self.logger.warning(f"Creamos un path de audio de entrada: {self.audio_media_path} puesto que no se ha suministrado ninguno.")
                print(f"Creamos un path de audio de entrada: {self.audio_media_path} puesto que no se ha suministrado ninguno.")
            self.audio_media_path = audio_media_path          
            self.logger.warning(f"El path de audio de entrada será: {self.audio_media_path}.")  
            print(f"El path de audio de entrada será: {self.audio_media_path}.")  

        if self.video_media_path is not None:
            # Existe un path de entrada de video ??            
            if os.path.exists(self.video_media_path):
                #dataset_tuplas_list = [[ (video,video_subfolder) for video in os.listdir(os.path.join(self.video_media_path, video_subfolder))] for video_subfolder in os.listdir(self.video_media_path) if os.path.isdir(os.path.join(self.video_media_path, video_subfolder))]
                tuplas = _buscar_by_extension_in_dataset(self.video_media_path, ".mp4")
                                
                for tupla in tuplas:
                    video_file = tupla[0]   
                    video_subfolder = tupla[1]   
                    video_file_under = video_file.replace(" ","_")
                    os.rename(os.path.join(self.video_media_path, video_subfolder, video_file), os.path.join(self.video_media_path, video_subfolder, video_file_under))    
                    self.convert_video_to_audio(video_file_under, video_subfolder)                
                    
                ## En caso de que los videos MP4 no vengan agrupados en carpetas de Datasets, sino en la misma carpeta 
                video_files = [video for video in os.listdir(self.video_media_path) if video.lower().endswith(".mp4")]
                # Convert the video to audio
                for video_file in video_files:          
                    video_file_under = video_file.replace(" ","_")
                    os.rename(os.path.join(self.video_media_path, video_file), os.path.join(self.video_media_path, video_file_under))    
                    self.convert_video_to_audio(video_file_under)
            else:
                self.logger.warning(f"Path de entrada: {self.video_media_path} con videos para convertir, no existe.")        
                
        tuplas = _buscar_by_extension_in_dataset(self.audio_media_path, ".m4a")
        for tupla in tuplas:
            m4a_audio_file = tupla[0]   
            m4a_audio_subfolder = tupla[1]           
            m4a_audio_file_under = m4a_audio_file.replace(" ","_")
            os.rename(os.path.join(self.audio_media_path, m4a_audio_subfolder, m4a_audio_file), os.path.join(self.audio_media_path, m4a_audio_subfolder, m4a_audio_file_under))    
            self.convert_M4A_to_Wav(m4a_audio_file_under, m4a_audio_subfolder)            
        ## En caso de que los audios M4A no vengan agrupados en carpetas de Datasets, sino en la misma carpeta 
        for m4a_audio_file in [m4a_audio for m4a_audio in os.listdir(self.audio_media_path) if m4a_audio.lower().endswith(".m4a")]:
            m4a_audio_file_under = m4a_audio_file.replace(" ","_")
            os.rename(os.path.join(self.audio_media_path, m4a_audio_file), os.path.join(self.audio_media_path, m4a_audio_file_under))    
            self.convert_M4A_to_Wav(m4a_audio_file_under)  
            
        tuplas = _buscar_by_extension_in_dataset(self.audio_media_path, ".mp3")
        for tupla in tuplas:
            mp3_audio_file = tupla[0]   
            mp3_audio_subfolder = tupla[1]           
            mp3_audio_file_under = mp3_audio_file.replace(" ","_")
            os.rename(os.path.join(self.audio_media_path, mp3_audio_subfolder, mp3_audio_file), os.path.join(self.audio_media_path, mp3_audio_subfolder, mp3_audio_file_under))    
            self.convert_MP3_to_Wav(mp3_audio_file_under, mp3_audio_subfolder)            
        ## En caso de que los audios MP3 no vengan agrupados en carpetas de Datasets, sino en la misma carpeta                
        for mp3_audio_file in [mp3_audio for mp3_audio in os.listdir(self.audio_media_path) if mp3_audio.lower().endswith(".mp3")]:
            mp3_audio_file_under = mp3_audio_file.replace(" ","_")
            os.rename(os.path.join(self.audio_media_path, mp3_audio_file), os.path.join(self.audio_media_path, mp3_audio_file_under))    
            self.convert_MP3_to_Wav(mp3_audio_file_under)                           
                                                          
        tuplas = _buscar_by_extension_in_dataset(self.audio_media_path, ".wav")
        for tupla in tuplas:
            audio_file = tupla[0]   
            if self.audio_media_path != tupla[1]:
                audio_subfolder = tupla[1]                       
                audio_file_under = audio_file.replace(" ","_")
                os.rename(os.path.join(self.audio_media_path, audio_subfolder, audio_file), os.path.join(self.audio_media_path, audio_subfolder, audio_file_under))    
                if not os.path.exists(os.path.join(self.output_media_path, audio_subfolder)):
                    os.mkdir(os.path.join(self.output_media_path, audio_subfolder))
                    self.logger.warning(f"Creamos el path de audio de entrada: {str(os.path.join(self.output_media_path, audio_subfolder))}, para el dataset {audio_subfolder}")            
                shutil.copy2(os.path.join(self.audio_media_path, audio_subfolder, audio_file_under), os.path.join(self.output_media_path, audio_subfolder, audio_file_under))
                
                self.convert_stereo_to_mono(os.path.join(self.output_media_path, audio_subfolder, audio_file_under))                
                self.logger.debug(f"Copiado {audio_file_under} a {self.output_media_path}.")
        ## En caso de que los audios WAV no vengan agrupados en carpetas de Datasets, sino en la misma carpeta                    
        for audio_file in [audio_file for audio_file in os.listdir(self.audio_media_path) if audio_file.lower().endswith(".wav")]:
                # Move the audio files converted or not converted to the output path 
                audio_file_under = audio_file.replace(" ","_")
                os.rename(os.path.join(self.audio_media_path, audio_file), os.path.join(self.audio_media_path, audio_file_under))    
                shutil.copy2(os.path.join(self.audio_media_path, audio_file_under), os.path.join(self.output_media_path, audio_file_under))                   
                
                self.convert_stereo_to_mono(os.path.join(self.output_media_path, audio_file_under))
                self.logger.debug(f"Copiado {audio_file_under} a {self.output_media_path}.")
                
       except Exception as e:
            self.logger.error(f"Error: {e}")
            raise e    
       self.logger.debug(f"Conversiones finalizadas.")

    def convert_stereo_to_mono(self, path_wav_file):
        audio_file = AudioSegment.from_wav(path_wav_file)
        audio_file = audio_file.set_channels(1)    
        audio_file.export(path_wav_file, format="wav")
        
     # Convert MP4 video to WAV audio   
    def convert_video_to_audio(self, input_file, dataset_subfolder=None):
        output_file = input_file.replace('.mp4', '.wav')
        if dataset_subfolder is None:
            input_path = os.path.join(self.video_media_path, input_file)
            output_path = os.path.join(self.audio_media_path, output_file)
        else:
            input_path = os.path.join(self.video_media_path, dataset_subfolder, input_file)
            output_path = os.path.join(self.audio_media_path, dataset_subfolder, output_file)                
        # Load the MP4 audio file
        audio = AudioFileClip(input_path)
        # Convert and save the audio to WAV format
        audio.write_audiofile(output_path, codec='pcm_s16le', bitrate='16000')
        audio.close()        
        self.logger.debug(f"Convertido {input_file} a {output_file}.")

    def convert_M4A_to_Wav(self, m4a_audio_file, dataset_subfolder=None):
        if dataset_subfolder is None:            
            m4a_audio_filepath = os.path.join(self.audio_media_path, m4a_audio_file) 
        else:
            m4a_audio_filepath = os.path.join(self.audio_media_path, dataset_subfolder, m4a_audio_file) 
        m4a_wrapper = AudioSegment.from_file(m4a_audio_filepath, format='m4a')
        wav_audio_file = m4a_audio_file.replace('.m4a', '.wav').replace('.M4A', '.wav')
        if dataset_subfolder is None:
            m4a_wrapper.export(os.path.join(self.audio_media_path, wav_audio_file), format='wav', )
        else:    
            m4a_wrapper.export(os.path.join(self.audio_media_path, dataset_subfolder, wav_audio_file), format='wav')
        self.logger.debug(f"Convertido {m4a_audio_file} a {wav_audio_file}.")
            
    def convert_MP3_to_Wav(self, mp3_audio_file, dataset_subfolder=None):
        if dataset_subfolder is None:            
            mp3_audio_filepath = os.path.join(self.audio_media_path, mp3_audio_file) 
        else:        
            mp3_audio_filepath = os.path.join(self.audio_media_path, dataset_subfolder, mp3_audio_file) 
        mp3_wrapper = AudioSegment.from_mp3(mp3_audio_filepath, )
        wav_audio_file = mp3_audio_file.replace('.mp3', '.wav').replace('.MP3', '.wav')
        if dataset_subfolder is None:            
            mp3_wrapper.export(os.path.join(self.audio_media_path, wav_audio_file),  format='wav')
        else:
            mp3_wrapper.export(os.path.join(self.audio_media_path, dataset_subfolder, wav_audio_file),  format='wav')    
        self.logger.debug(f"Convertido {mp3_audio_file} a {wav_audio_file}.")            

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert MP4 video to WAV audio and other audio formats to WAV")
    parser.add_argument('-vmp', '--video_media_path', type=str, help='Carpeta de entrada con los archivos de video(.mp4)')
    parser.add_argument('-amp', '--audio_media_path', type=str, help='Carpeta de entrada con los archivos de audio(.wav, .mp3, .m4u)')
    parser.add_argument('-omp', '--output_media_path', type=str, help='Carpeta de salida con los archivos de audio(.wav) convertidos a Mono y muestreados 16Kbps.')

    args = parser.parse_args()
    converter = ConverterToAudio(args.video_media_path, args.audio_media_path,  args.output_media_path)
    converter.convert()