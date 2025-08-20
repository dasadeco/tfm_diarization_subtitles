## Esto es un TFM sobre Subtítulos y Diarización.

Reconocimientos:
Hervé Bredin es el autor de *Pyannote-audio* : https://github.com/hbredin.  
También citar a la comunidad de diarizadores de la que se han tomado dos modulo para "modular Pyannote": https://github.com/huggingface/diarizers/blob/main/README.md

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

- Convertidor de subtítulos (Java):
1. Ve a la carpeta "TFM/docker"
2. Ejecutar `docker buildx build -f Dockerfile_java_subtitles -t  dasaenzd/manage_subtitles:latest ..` Se construye una imagen de 117 Mb
3. Ejecutar `docker push dasaenzd/manage_subtitles:latest`   para enviarlo a Docker Hub, a mi espacio de nombres: dasaenzd
4. cd .. (ve a la carpeta TFM)
5. Ejecutar `docker run --mount type=bind,source=.\\subtitles\\data,target=/data --name converter_subtitles dasaenzd/manage_subtitles:latest  generaAllRTTMRef  -d={PARAM DELTA EN MILLISECS.}`  : ejecuta manualmente este contenedor, ésto realiza la conversión de todos los archivos de subtitulos de referencia y los convierte a RTTM de referencia.
   - Le pasamos un primer parámetro obligatorio para indicar el modo de utilización que va a tener este contenedor, ya que tiene varios, el valor fijo es `generaAllRTTMRef`.
   - Le pasamos un segundo parámetro obligatorio llamado Delta para establecer cuando consideramos que termina un speech del mismo hablante. Normalmente será 0.

- Evaluador de Métricas UNE / Etiquetador de Subtítulos (Java)
Los pasos 1 a 4  del punto anterior 'Convertidor de subtítulos', sólo hay que hacerlos una vez, ya que la imagen utilizada es la misma. Lo que cambia es su utilización.
5.  Ejecutar `docker run --mount type=bind,source=.\\subtitles\\data,target=/data  --mount type=bind,source=.\\data\\media,target=/media --name une_evaluator dasaenzd/manage_subtitles:latest evalAllUne ` 
   - Aquí solo le pasamos un primer parámetro obligatorio `evalAllUne` que indica el uso que le damos a este contenedor, evaluación de los subtitulos diarizados según la norma UNE y concreteamente de algunos puntos elegidos que tienen algo que ver con la diarización.


Siguiente paso, obtención de métricas:
- En _subtitles/data/rttm_ref_ están los RTTMs de referencia y en _data/media/rttm/{modelos combinados utilizados de Pyannote o de Nemo}_ están los RTTMs de hipótesis, aquí hay que utilizar pyannote.metrics para calcularlas


