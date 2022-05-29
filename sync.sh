#!/bin/sh

if [ ! -z "${DEBUG}" ];
then
    set -x
fi

mkdir -p /root/.ssh
chmod 700 /root/.ssh

for key in /root/deploykeys/*;
do
    ln -s $key /root/.ssh >/dev/null 2>&1
done

if [ ! -f /root/.config/rclone/rclone.conf ];
then
    mkdir -p /root/.config/rclone/
    cat <<EOF > /root/.config/rclone/rclone.conf
[minio]
type = s3
provider = Minio
env_auth = false
access_key_id = $(cat /etc/minio/accesskey)
secret_access_key = $(cat /etc/minio/secretkey)
region = us-east-1
endpoint = $MINIO_URL
location_constraint =
server_side_encryption =
EOF
fi

# check bucket

rclone lsd minio: | grep "${MINIO_BUCKET}"
if [ "$?" -ne 0 ];
then
    rclone mkdir "minio:${MINIO_BUCKET}"
fi

PREV_HASH=""

while true;
do
    rm -fr repo
    mkdir repo
    git clone "${POSTS_REPO}" repo

    cd repo
    CURRENT_HASH=$(git rev-parse HEAD)
    cd ..

    if [ "${CURRENT_HASH}" != "${PREV_HASH}"];
    then
        rclone --no-update-modtime sync repo/favicon.ico "minio:${MINIO_BUCKET}"
        rclone --no-update-modtime sync repo/posts       "minio:${MINIO_BUCKET}/posts"
        rclone --no-update-modtime sync repo/pages       "minio:${MINIO_BUCKET}/pages"
        rclone --no-update-modtime sync repo/static      "minio:${MINIO_BUCKET}/static"
        rclone --no-update-modtime sync repo/redirects   "minio:${MINIO_BUCKET}/redirects"

        PREV_HASH="${CURRENT_HASH}"
    fi

    # random sleep between 30 an 39 minutes
    sleep "$(echo "$(echo $RANDOM | grep -Eo "[0-9]$")+30" | bc -l)"m
done
