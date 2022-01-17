FROM gcr.io/google.com/cloudsdktool/cloud-sdk:alpine

RUN apk --update add curl \
which \
bash \
jq \
unzip

RUN apk add --no-cache \
       python3 \
       py3-pip \
   && pip3 install --upgrade pip \
   && pip3 install \
       awscli \
   && rm -rf /var/cache/apk/*

RUN set -ex \
    && curl https://rclone.org/install.sh | bash

COPY googletransfer.sh /usr/bin/googletransfer.sh
COPY s3transfer.sh /usr/bin/s3transfer.sh
COPY rclone.conf /root/.config/rclone/rclone.conf
COPY sftptransfer.sh /usr/bin/sftptransfer.sh

RUN chmod +x /usr/bin/googletransfer.sh
RUN chmod +x /usr/bin/s3transfer.sh
RUN chmod +x /usr/bin/sftptransfer.sh