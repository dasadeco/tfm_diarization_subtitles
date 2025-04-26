FROM python:3.11
LABEL AUTHOR="Daniel Saenz de Cosca"

#RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN apt-get update && apt-get install -y libsndfile1 ffmpeg
RUN pip3 install pyannote.audio    

WORKDIR /workdir
COPY  pyannote_pipeline.py /workdir/
RUN mkdir -p /data