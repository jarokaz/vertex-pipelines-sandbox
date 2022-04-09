# vertex-pipelines-sandbox

```
IMAGE_URI=gcr.io/jk-mlops-dev/test-runner

docker build -t $IMAGE_URI .
docker push $IMAGE_URI
```

```
docker run -it --rm \
$IMAGE_URI \
--sleep_time 10
```

```
docker run -it --rm \
-v /home/jupyter/vertex-pipelines-sandbox:/source \
--entrypoint /bin/bash \
$IMAGE_URI
```

```
python3 launcher.py \
--project jk-mlops-dev \
--location us-central1 \
--gcp_resources /tmp/gcp_resources/file

```