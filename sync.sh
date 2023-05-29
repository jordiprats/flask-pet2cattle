#!/bin/sh

if [ ! -z "${DEBUG}" ];
then
    set -x
fi

if [ ! -f ${HOME-/root}/.ssh/config ];
then
    cat <<"EOF" >${HOME-/root}/.ssh/config
Host *
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
EOF
fi

if [ ! -f ${HOME-/root}/.config/rclone/rclone.conf ];
then
    mkdir -p ${HOME-/root}/.config/rclone/
    cat <<EOF > ${HOME-/root}/.config/rclone/rclone.conf
[remote]
type = s3
provider = ${S3_PROVIDER-Minio}
env_auth = ${S3_ENV_AUTH-false}
access_key_id = $(cat /etc/minio/accesskey)
secret_access_key = $(cat /etc/minio/secretkey)
region = ${S3_REGION-us-east-1}
endpoint = $MINIO_URL
location_constraint =
server_side_encryption =
EOF
fi

if [ ! -z "${DEBUG}" ];
then
    cat ${HOME-/root}/.config/rclone/rclone.conf
fi

# check bucket

rclone lsd remote: | grep "${MINIO_BUCKET}"
if [ "$?" -ne 0 ];
then
    rclone mkdir "remote:${MINIO_BUCKET}"
fi

PREV_HASH=""

mkdir -p reposync_tmp
cd reposync_tmp

while true;
do

    if [ ! -z "$MINIO_URL" ];
    then
        MINIO_HOST=$(echo $MINIO_URL | rev | cut -f1 -d/ | rev | cut -f1 -d:)
        MINIO_PORT=$(echo $MINIO_URL | rev | cut -f1 -d/ | rev | cut -f2 -d:)

        nc -zv -w 5 "$MINIO_HOST" "$MINIO_PORT"

        if [ $? -ne 0 ];
        then
            echo "unable to reach $MINIO_HOST using port $MINIO_PORT"
            sleep "$(echo "$(echo $RANDOM | grep -Eo "[0-9]$")+1" | bc -l)"
            exit 1
        fi
    fi

    echo "attempting to sync"

    rm -fr repo
    mkdir repo
    git clone "${POSTS_REPO}" repo

    cd repo
    CURRENT_HASH=$(git rev-parse HEAD)
    cd ..

    if [[ "${CURRENT_HASH}" != "${PREV_HASH}" ]];
    then
        echo "Updating S3..."
        rclone --no-update-modtime sync repo/favicon.ico "remote:${MINIO_BUCKET}"
        rclone --no-update-modtime sync repo/posts       "remote:${MINIO_BUCKET}/posts"
        rclone --no-update-modtime sync repo/pages       "remote:${MINIO_BUCKET}/pages"
        rclone --no-update-modtime sync repo/static      "remote:${MINIO_BUCKET}/static"
        rclone --no-update-modtime sync repo/redirects   "remote:${MINIO_BUCKET}/redirects"

        PREV_HASH="${CURRENT_HASH}"
    fi

    # random sleep between 30 an 39 minutes
    echo "sleeping"
    sleep "$(echo "$(echo $RANDOM | grep -Eo "[0-9]$")+30" | bc -l)"m
done
