# syntax=docker/dockerfile:1

FROM ghcr.io/lamusmaser/ffmpeg-python-image
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
ENTRYPOINT ["python3"]
CMD ["video_detector.py"]