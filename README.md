# Site Infinity Log Parser
This component parse the log file of site-infinity and stores the records in the database server so that it can be picked up by the upstream SEIM solution.

# Build Container
```
$ docker build -t siteinifinitysync:2.0.0 .
```

# Run the container
```
$ docker run  \
 --env SI_DB_SERVER=<Server hostname> \
 --env SI_DB_DATABASE=<Database Name> \
 --env SI_DB_USERNAME=<Databsae User Name> \
 --env SI_DB_PASS=<Database Password> \
 --env SI_SOURCE_LOG_DIR=/opt/code/audit.logs \
 --env SI_DEST_DIR=/opt/code/audit.logs/archive \
 --mount type=bind,source="<LOCAL HOST DIRECTORY>",target=/opt/code/audit.logs \
 -d --name siteinifinitysync siteinifinitysync:2.0.0
```

# Take a shell in the container
```
docker exec -it  site-infinity-log-parser /bin/bas
```