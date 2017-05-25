#Unfinished install script for the GeneSippr_Portal to create a new work environment
#Tested on Ubuntu 16.4

#need to install docker 

#pull images needed and create containers used for the portal (there should be 3 new images and 2 new running containers)
docker pull rabbitmq:3
docker pull postgres
sudo docker build https://github.com/OLC-LOC-Bioinformatics/geneSipprV2.git#master:sipprverse

sudo docker run -d -p 0.0.0.0:5672:5672 --restart=always --hostname rabbit --name rabbit rabbitmq:3
sudo docker run --name postgres -e POSTGRES_PASSWORD=biohazard -e POSTGRES_USER=admin -e POSTGRES_DB=mydb -e PGDATA=/var/lib/postgresql/data/pgdata --restart=always -p 0.0.0.0:5432:5432 -d postgres

#now .........






