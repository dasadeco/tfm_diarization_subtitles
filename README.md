## Esto es un TFM sobre Subtítulos y Diarización.

Hervé Bredin es el autor de *Pyannote-audio* : https://github.com/hbredin

Construyendo las Docker Images:
--------------------------------
- Pyannote Pipeline (Python): 
1. Ve a la carpeta "TFM/docker"
2. Ejecutar `docker buildx build -f Dockerfile_pyannote_pipeline -t dasaenzd/pyannote_pipeline:latest ..`  Se construye la imagen (Son 9.5 GB !!)
3. Ejecutar `docker push dasaenzd/pyannote_pipeline:latest`   para enviarlo a Docker Hub, a mi espacio de nombres: dasaenzd
4. Su ejecución puede ser orquestada por el módulo docker_diariz_manager, si se quiere ejecutar manualmente:
   - el comando para ejecutar el contenedor es: `docker run --mount type=bind,source=.\\data\\media,target=/media --name pyannote_pipeline dasaenzd/pyannote_pipeline:latest`

- NeMo Pipeline (Python): 
1. Ve a la carpeta "TFM/docker"
2. Ejecutar `docker buildx build -f Dockerfile_nemo_pipeline -t dasaenzd/nemo_pipeline:latest ..`  Se construye la imagen (Son  27.5 GB !!!)
docker buildx build -f Dockerfile_nemo -t  dasaenzd/nemo_pipeline:latest ..
3. Ejecutar `docker push dasaenzd/nemo_pipeline:latest`   para enviarlo a Docker Hub, a mi espacio de nombres: dasaenzd
4. Su ejecución puede ser orquestada por el módulo docker_diariz_manager, si se quiere ejecutar manualmente:
   - el comando para ejecutar el contenedor es: `docker run --mount type=bind,source=.\\data\\media,target=/media --name nemo_pipeline dasaenzd/nemo_pipeline:latest`

- ConverterSubtitles (Java):
1. Ve a la carpeta "TFM/docker"
2. Ejecutar `docker buildx build -f Dockerfile_java_subtitles -t  dasaenzd/converter_subtitles:latest ..` Se construye una imagen de 115 Mb
3. Ejecutar `docker push dasaenzd/converter_subtitles:latest`   para enviarlo a Docker Hub, a mi espacio de nombres: dasaenzd
4. cd .. (ve a la carpeta TFM)
5. Ejecutar `docker run --mount type=bind,source=.\\subtitles\\data,target=/data --name converter_java_subtitles dasaenzd/converter_subtitles:latest -d={PARAM DELTA EN MILLISECS.}`, ésto ejecuta manualmente este contenedor, esto realiza la conversión de todos los archivos de subtitulos de referencia y los convierte a RTTM de referencia, para ello le pasamos un (hiper)parámetro Delta para establecer cuando consideramos que termina un speech del mismo hablante. 

Siguiente paso, obtención de métricas:
- En _subtitles/data/rttm_ref_ están los RTTMs de referencia y en _data/media/rttm/{pipeline HuggingFace utilizada ó combinación de modelos de Nemo utilizados}_ están los RTTMs hipótesis, con esto hay que utilizar pyannote.metrics para calcularlas
