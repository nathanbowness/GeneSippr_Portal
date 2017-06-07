#!/bin/sh
folderpath=$1
containernumber=$2
if [ "$(docker ps -q -f name=genesipprcontainer$containernumber)" ]
then
	#kill and delete old container
	echo "Stopping and removing current open container."
	docker kill genesipprcontainer$containernumber
	docker rm genesipprcontainer$containernumber
elif [ ! "$(docker ps -q -f name=genesipprcontainer$containernumber)" ] 
then
	if [ "$(docker ps -aq -f status=exited -f name=genesipprcontainer$containernumber)" ] 
	then
		echo "Removing the old container."
       		# cleanup
        	docker rm genesipprcontainer$containernumber
	fi
fi

wait

#must be run without the "-it" as this will give an error on execute with "-i" for an interactive display
docker run -i -v /home/bownessn/Documents/GeneSippr_Portal:/home/bownessn/Documents/GeneSippr_Portal --name genesipprcontainer$containernumber genesippr method.py /home/bownessn/Documents/GeneSippr_Portal/documents/$folderpath -s /home/bownessn/Documents/GeneSippr_Portal/documents/$folderpath/sequences -t /home/bownessn/Documents/GeneSippr_Portal/GeneSippr/targets

wait

echo " "
echo "Completed running geneseekr for the folder: $folderpath"
echo "Removing container now, since it has finished: genesipprcontainer$containernumber"
docker rm genesipprcontainer$containernumber
#Finished running geneseekr

