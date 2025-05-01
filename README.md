## Esto es un TFM sobre Subtítulos y Diarizazión. Cuida de cumplir la norma UNE 153010:2012  española.

Hervé Bredin es el autor de *Pyannote-audio* : https://github.com/hbredin

Construyendo las Docker Images
- Pyannote Pipeline:
1. Ve a la carpeta "TFM/docker"
2. Run `docker buildx build -f Dockerfile_pyannote_pipeline -t dasaenzd/pyannote_pipeline:latest ..`  Se constuye la imagen (Son casi HD 10 GB !)
3. Run `docker push dasaenzd/pyannote_pipeline:latest`   para enviarlo a Docker Hub, a mi espacio de nombres: dasaenzd