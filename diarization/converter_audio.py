from moviepy import AudioFileClip
from pydub import AudioSegment
import os, shutil
import argparse
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(filename=f'./data/converter_audio_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8', level=logging.DEBUG) 

class ConverterToAudio:
    def __init__(self, video_media_path, audio_media_path, ouput_media_path = './data/media'):
        self.video_media_path = video_media_path
        self.audio_media_path = audio_media_path
        self.ouput_media_path = ouput_media_path
        
    def convert(self):
       try:
        if self.audio_media_path is None:
            # Si no se proporciona una carpeta de audio destino, se crea una por defecto si no está ya creada
            audio_media_path = os.path.join(os.getcwd(), 'audio')
            if not os.path.exists(audio_media_path):
                os.mkdir(audio_media_path)
                logger.warning(f"Creamos un path de audio de entrada: {self.audio_media_path} puesto que no se ha suministrado ninguno.")
            self.audio_media_path = audio_media_path          
            logger.warning(f"El path de audio de entrada será: {self.audio_media_path}.")  

        if self.video_media_path is not None:
            # Existe un path de entrada de video ??            
            if os.path.exists(self.video_media_path):                
                video_files = [video for video in os.listdir(self.video_media_path) if video.endswith(".mp4")]
                # Convert the video to audio
                for video_file in video_files:          
                    video_file_under = video_file.replace(" ","_")
                    os.rename(os.path.join(self.video_media_path, video_file), os.path.join(self.video_media_path, video_file_under))    
                    self.convertVideoToAudio(video_file_under)
            else:
                logger.warning(f"Path de entrada: {self.video_media_path} con videos para convertir, no existe.")        
                
        for m4a_audio_file in [m4a_audio for m4a_audio in os.listdir(self.audio_media_path) if m4a_audio.endswith(".m4a")]:
            m4a_audio_file_under = m4a_audio_file.replace(" ","_")
            os.rename(os.path.join(self.audio_media_path, m4a_audio_file), os.path.join(self.audio_media_path, m4a_audio_file_under))    
            self.convertM4AToWav(m4a_audio_file_under)             
                             
        for audio_file in os.listdir(self.audio_media_path):
            if audio_file.endswith(".wav"):
                # Move the audio files converted or not converted to the output path 
                audio_file_under = audio_file.replace(" ","_")
                os.rename(os.path.join(self.audio_media_path, audio_file), os.path.join(self.audio_media_path, audio_file_under))    
                shutil.copy2(os.path.join(self.audio_media_path, audio_file_under), os.path.join(self.ouput_media_path, audio_file_under))                   
                logger.debug(f"Copiado {audio_file_under} a {self.ouput_media_path}.")
                #exit(1)
       except Exception as e:
            logger.error(f"Error: {e}")
            raise e
        
     # Convert MP4 video to WAV audio   
    def convertVideoToAudio(self, input_file):
        output_file = input_file.replace('.mp4', '.wav')
        input_path = os.path.join(self.video_media_path, input_file)
        output_path = os.path.join(self.audio_media_path, output_file)
        # Load the MP4 audio file
        audio = AudioFileClip(input_path)
        # Convert and save the audio to WAV format
        audio.write_audiofile(output_path, codec='pcm_s16le', bitrate='16000')
        audio.close()        
        logger.debug(f"Convertido {input_file} a {output_file}.")

    def convertM4AToWav(self, m4a_audio_file):
            m4a_audio_filepath = os.path.join(self.audio_media_path, m4a_audio_file) 
            m4a_wrapper = AudioSegment.from_file(m4a_audio_filepath, format='m4a')
            wav_audio_file = m4a_audio_file.replace('.m4a', '.wav')
            m4a_wrapper.export(os.path.join(self.audio_media_path, wav_audio_file), format='wav')
            logger.debug(f"Convertido {m4a_audio_file} a {wav_audio_file}.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert MP4 video to WAV audio")
    parser.add_argument('-vmp', '--video_media_path', type=str, default='../datasets', help='Path of the folder with the video(.mp4) files')
    parser.add_argument('-amp', '--audio_media_path', type=str,  help='Path of the folder with the audio(.wav) files')

    args = parser.parse_args()
    converter = ConverterToAudio(args.video_media_path, args.audio_media_path)
    converter.convert()
    logger.debug(f"Conversiones finalizadas.")
    exit(0)
    