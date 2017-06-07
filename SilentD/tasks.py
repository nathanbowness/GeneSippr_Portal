# Python Library
from __future__ import absolute_import
from subprocess import Popen
from celery import Celery
import shutil
import os
# Django Model Imports
from SilentD.models import Project


# General Settings
app = Celery('tasks',
             backend='djcelery.backends.database.DatabaseBackend',
             broker='amqp://guest:guest@localhost:5672//')


def get_sequencedir(project_obj):
    return 'documents/%s/%s/sequences' % (str(project_obj.date.date()), project_obj.description)


def get_resultdir(project_obj, result_folder):
    return 'documents/%s/%s/reports/%s' % (str(project_obj.date.date()), project_obj.description, result_folder)


def fileexists(end_path):
    if os.path.isfile(end_path):
        return True

    return False


def create_dir(working_dir):
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)


def get_review_result(genus, matches):

    # Split the matches term, where the first term is the number of genes matched and the second term
    # is the total number of matches possible. Then assign a term for the review of results
    sequenced_num = matches.split('/')
    success = 'successful'
    intermediate = 'intermediate'
    not_success = 'unsuccessful'

    if len(sequenced_num) > 1 & len(sequenced_num) < 3:
        matched = int(sequenced_num[0])
        total = int(sequenced_num[1])

        if 'Escherichia' in genus:  # Escherichia has a total of 53 matches
            if total - matched <= 1:  # if 52 or more good match
                return success
            elif total - matched <= 5:  # if 48 or more okay match
                return intermediate
            else:
                return not_success
        elif 'Listeria' in genus:  # Listeria has a total of 50 matches
            if total - matched <= 1:  # if 49 or more good match
                return success
            elif total - matched <= 5:  # if 45 or more okay match
                return intermediate
            else:
                return not_success
        elif 'Salmonella' in genus:
            if total - matched <= 1:  # if __ or more good match
                return success
            elif total - matched <= 5:  # if __ or more okay match
                return intermediate
            else:
                return not_success
    return "error"


def delete_project(proj_id):
    '''This method will delete fastq files from the project directory, this will save space within the docker 
    containers. The reports and logs however were not deleted, permission issues make this difficult. 
    So the logs will remain, they are small and cause no errors. 
    Also useful to archive the information if that is needed later.'''
    project_obj = Project.objects.get(id=proj_id)
    print('Deleting project copies of the fastq files within the project: ', project_obj.description)
    print('The removal helps reduce storage.')

    project_dir = 'documents/%s/%s' % (str(project_obj.date.date()), project_obj.description)
    shutil.rmtree(project_dir, ignore_errors=True)
    print("Files deleted.")


@app.task(bind=True)
def genesippr_task(self, proj_id):
    project_obj = Project.objects.get(id=proj_id)
    data_files = project_obj.files.all()
    for data in data_files:
        # set the working directory to the day of the job, followed by the name of the project, then a sequences folder
        working_dir = get_sequencedir(project_obj)
        create_dir(working_dir)
        path = data.file.name.split('/')[-1]
        end_path = os.path.join(working_dir, path)
        # check to see if the file already exists for some reason in the folder before copying (should never happen)
        if fileexists(end_path):
            print("File: ", end_path, " already found. No need to copy.")
        else:
            try:
                print("Copying from %s to %s" % (data.file.name, end_path))
                shutil.copyfile(data.file.name, end_path)
            # if somehow the user deleted the database files, they are told to restart the database
            except FileNotFoundError:
                print("Protected database files have been deleted by the user. Restart the database to continue.")

    dockercontainertag = project_obj.id
    genesippr_dir = 'GeneSippr/'
    genesipprshell = 'run_genesippr.sh'
    partialpath = os.path.join(str(project_obj.date.date()), project_obj.description)
    execute_genesipper = os.path.join(genesippr_dir, genesipprshell)
    p = Popen([execute_genesipper, str(partialpath), str(dockercontainertag)])
    print("GeneSippr is creating reports for the project.")
    p.communicate()  # wait until completed before resuming the code

    # check that all files have been made by the docker container otherwise, update that it failed
    results_16spath = get_resultdir(project_obj, result_folder_names.folder_16s)
    results_GDCSpath = get_resultdir(project_obj, result_folder_names.folder_GDCS)
    results_genesippr = get_resultdir(project_obj, result_folder_names.folder_genesippr)

    if fileexists(results_16spath) and fileexists(results_GDCSpath) and fileexists(results_genesippr):
        project_obj.amr_results = "Done"
        project_obj.save()
        print("The GeneSippr task was successful")
    else:
        project_obj.amr_results = "Error"
        project_obj.save()
        print("An error occurred when running the GeneSippr task.")


class result_folder_names(object):
    folder_16s = '16S.csv'
    folder_GDCS = 'GDCS.csv'
    folder_genesippr = 'genesippr.csv'
