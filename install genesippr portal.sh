#Untested install script for the GeneSippr_Portal to create a new development environment
#Tested on Ubuntu 16.4

#need to install docker

#pull/build images needed for the genesippr portal
docker pull rabbitmq:3
docker pull postgres
sudo docker build https://github.com/OLC-LOC-Bioinformatics/geneSipprV2.git#master:sipprverse

# create the containers needed for the database and the task manager
sudo docker run -d -p 0.0.0.0:5672:5672 --restart=always --hostname rabbit --name rabbit rabbitmq:3
# Can run the database without mounting the data to your local computer, it will all just 
# be encapsulated there. If you want to be able to see it in further detail add this to the 
# command when you run the container
# <Path to Folder 1>:/var/lib/postgresql/data/pgdata
sudo docker run --name postgres -e POSTGRES_PASSWORD=biohazard -e POSTGRES_USER=admin -e POSTGRES_DB=mydb -e PGDATA=/var/lib/postgresql/data/pgdata --restart=always -p 0.0.0.0:5432:5432 -d postgres

# Create a virtual environment
python3 -m venv genesipprportal
source ~/genesipprportal/bin/activate 

# Install all the requirements from the requirements.txt file
pip install requirements.txt

echo "Migrating Database If Needed"
cd /app/ && python manage.py makemigrations
cd /app/ && python manage.py migrate

echo "Setting Up Django"
echo "from django.contrib.auth.models import User; User.objects.filter(email='admin@example.com').delete(); User.objects.create_superuser('admin', 'admin@example.com', 'admin')" | python manage.py shell
cd /app/ && python manage.py runserver 0.0.0.0:8000 &

echo "Setting Up Celery"
# Starts Celery and workers given 24 hours max to complete a task and output logs
cd /app/ && python manage.py celery worker --time-limit=86400 --loglevel=info 
