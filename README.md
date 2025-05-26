## Esto es un TFM sobre Subtítulos y Diarización. Cuida de cumplir la norma UNE 153010:2012 española.

Hervé Bredin es el autor de *Pyannote-audio* : https://github.com/hbredin

Construyendo las Docker Images
- Pyannote Pipeline:
1. Ve a la carpeta "TFM/docker"
2. Run `docker buildx build -f Dockerfile_pyannote_pipeline -t dasaenzd/pyannote_pipeline:latest ..`  Se construye la imagen (Son 9.5 GB !!!)
3. Run `docker push dasaenzd/pyannote_pipeline:latest`   para enviarlo a Docker Hub, a mi espacio de nombres: dasaenzd

- ConverterSubtitles:
1. Ve a la carpeta "TFM/docker"
2. Run `docker buildx build -f Dockerfile_java_subtitles -t  dasaenzd/converter_subtitles:latest ..` Se construye una imagen de 115 Mb
3. Run `docker push dasaenzd/converter_subtitles:latest`   para enviarlo a Docker Hub, a mi espacio de nombres: dasaenzd
4. cd .. (ve a la carpeta TFM)
5. Run `docker run  --mount type=bind,source=.\\subtitles\\data,target=/data --name converter_java_subtitles -d  dasaenzd/converter_subtitles:latest`
    Ejecuta manualmente este contenedor, esto realiza la conversión de todos los archivos de subtitulos de referencia y los convierte a RTTM de referencia

Siguiente paso, obtención de métricas:
- En _subtitles/data/rttm_ref_ están los RTTMs de referencia y en _data/media/rttm/{pipeline HuggingFace utilizada}_ están los RTTMs hipótesis, con esto hay que utilizar pyannote.metrics
