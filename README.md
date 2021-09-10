# flask-pet2cattle

## development minio

```
docker run -d -p 9000:9000 \
  -e "MINIO_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE" \
  -e "MINIO_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" \
  minio/minio server /data
```

## flask run

```
MINIO_ACCESS_KEY="AKIAIOSFODNN7EXAMPLE" MINIO_SECRET_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" flask run -p 8000
```

## development

```
FORCE_PUBLISH=1 DEBUG=1 flask run -p 8000 -h 0.0.0.0
```

## TODO:

* fix search pagination