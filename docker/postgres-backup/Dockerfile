FROM postgres:17-alpine

RUN apk add --no-cache bash tzdata

COPY backup.sh /usr/local/bin/backup.sh

RUN mkdir -p /var/spool/cron/crontabs && \
    echo "0 3 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1" > /var/spool/cron/crontabs/root && \
    chmod +x /usr/local/bin/backup.sh && \
    chmod 0600 /var/spool/cron/crontabs/root

ENTRYPOINT ["crond", "-f", "-l", "2"]
