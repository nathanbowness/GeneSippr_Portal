# Python Library
from __future__ import absolute_import
from subprocess import Popen
from celery import Celery
import shutil
import os
# Django Model Imports
from SilentD.models import Project, Data


# General Settings
app = Celery('tasks',
             backend='djcelery.backends.database.DatabaseBackend',
             broker='amqp://guest:guest@localhost:5672//')


def get_sequencedir(project_obj):
    """The directory for the sequences folder is created from the day of the job, followed by the name of the project"""
    description = project_obj.description.replace(' ', '')  # remove any spaces in the project name
    return 'documents/%s/%s/sequences' % (str(project_obj.date.date()), description)


def get_resultdir(project_obj, result_folder):
    """The directory for the reports folder is created from the day of the job, followed by the name of the project, 
    a reports folder and then the report name"""
    description = project_obj.description.replace(' ', '')  # remove any spaces in the project name
    return 'documents/%s/%s/reports/%s' % (str(project_obj.date.date()), description, result_folder)


def file_exists(end_path):
    """Check to see if the file already exists in the place specified"""
    if os.path.isfile(end_path):
        return True

    return False


def create_dir(working_dir):
    """Create the directory for the given path if it does not already exist."""
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)


def get_review_result(genus, matches):
    """Return a review of the results keyword based on the inputted genus and number of matches for that genus."""

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
            if total - matched <= 1:
                return success
            elif total - matched <= 5:
                return intermediate
            else:
                return not_success
        elif 'Listeria' in genus:  # Listeria has a total of 50 matches
            if total - matched <= 1:
                return success
            elif total - matched <= 5:
                return intermediate
            else:
                return not_success
        elif 'Salmonella' in genus:  # Salmonella has a total of 50 matches
            if total - matched <= 1:
                return success
            elif total - matched <= 5:
                return intermediate
            else:
                return not_success
    return "error"


def delete_file(file_id):
    """Delete the location of the temp file from the documcents folder. This will save space when files are 
    no longer needed by the user."""
    file_obj = Data.objects.get(id=file_id)
    print("Removing file: ", file_obj.name)
    print(file_obj.file.path)
    file_dir = file_obj.file.path
    os.remove(file_dir)
    print("Done.")


def delete_project(proj_id):
    """This method will delete fastq files from the project directory, which will save space.
    The reports and logs however are not deleted, permission issues make this difficult. 
    So the logs will remain, they are small and cause no errors. 
    Also useful to archive the information if that is needed later."""
    project_obj = Project.objects.get(id=proj_id)
    print('Deleting project the fastq files within the project: ', project_obj.description)

    description = project_obj.description.replace(' ', '')  # remove any space in the project name
    project_dir = 'documents/%s/%s' % (str(project_obj.date.date()), description)
    shutil.rmtree(project_dir, ignore_errors=True)
    print("Files deleted.")


def move_files(proj_id):
    """Move files from their temporary directory into the project directory."""
    project_obj = Project.objects.get(id=proj_id)
    data_files = project_obj.files.all()

    for data in data_files:
        working_dir = get_sequencedir(project_obj)
        create_dir(working_dir)
        path = data.file.name.split('/')[-1]
        end_path = os.path.join(working_dir, path)

        if file_exists(end_path):
            print("File: ", end_path, " already found. No need to copy.")
        else:
            try:
                print("Copying from %s to %s" % (data.file.name, end_path))
                shutil.copyfile(data.file.name, end_path)
            # if somehow the user deleted the database files, they are told to restart the database
            except FileNotFoundError:
                print("Protected database files have been deleted by the user. Restart the database to continue.")


@app.task(bind=True)
def genesippr_task(self, proj_id):
    """Run the docker genesippr task on the fastq files of the selected project. Output a message on success or 
    failure."""

    project_obj = Project.objects.get(id=proj_id)
    basepath = os.path.dirname(__file__).replace('/SilentD', '')

    description = project_obj.description.replace(' ', '')  # remove any spaces in the project name
    partialpath = os.path.join(str(project_obj.date.date()), description)
    execute_genesipper = 'GeneSippr/run_genesippr.sh'

    # run the GeneSippr docker container from an outside script
    p = Popen([execute_genesipper, basepath, partialpath, str(project_obj.id)])
    print("GeneSippr is creating reports for the project.")
    p.communicate()  # wait until the script completes before resuming the code

    # path for all reports created from the docker run, check to ensure they are all present
    results_16spath = get_resultdir(project_obj, result_folder_names.folder_16s)
    results_GDCSpath = get_resultdir(project_obj, result_folder_names.folder_GDCS)
    results_genesippr = get_resultdir(project_obj, result_folder_names.folder_genesippr)

    if file_exists(results_16spath) and file_exists(results_GDCSpath) and file_exists(results_genesippr):
        project_obj.genesippr_results = "Done"
        project_obj.save()
        print("The GeneSippr task was successful")
    else:
        project_obj.genesippr_results = "Error"
        project_obj.save()
        print("An error occurred when running the GeneSippr task.")


class result_folder_names(object):
    """Class containing the folder names of a genesippr run."""

    folder_16s = '16S.csv'
    folder_GDCS = 'GDCS.csv'
    folder_genesippr = 'genesippr.csv'
