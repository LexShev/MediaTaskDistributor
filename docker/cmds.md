```bash
cd /home/a.shevchenko@tltv.local/SSHPycharmProjects/MediaTaskDistributor/docker/internal
```

```bash
docker-compose -p planner down -v --remove-orphans
```
```bash
docker-compose -p planner up -d --build
```

```bash
docker-compose -p media up -d --force-recreate mongodb
```