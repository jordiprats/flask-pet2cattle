# flask-pet2cattle

Blogging platform with **Flask** using object storage (**S3**/**MinIO**) as backend running on **Kubernetes** (deployed using a [helm chart](https://github.com/jordiprats/helm-pet2cattle))

![pet2cattle diagram](diagrams/pet2cattle.png "pet2cattle diagram")

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
* suggest alternate terms to search (or at least true random posts)