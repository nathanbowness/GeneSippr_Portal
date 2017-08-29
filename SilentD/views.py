import csv
import os
# Django Related Imports
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .forms import UserForm
# Database Models
from .models import Data, Project, Profile, Results
from collections import defaultdict, OrderedDict
# Celery Tasks
from .tasks import genesippr_task, result_folder_names
from .tasks import get_resultdir, get_review_result, delete_project, move_files, delete_file


# Create your views here.
def register(request):
    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        print(request.POST)
        user_form = UserForm(data=request.POST)

        if user_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()

            print(user)
            user_info = Profile(rank='Research')
            user_info.user = user
            user_info.save()

            print(user.profile)

            # Auto Log in the new user into system
            new_user = authenticate(username=request.POST['username'],
                                    password=request.POST['password'])
            login(request, new_user)

            # Redirect to main index page
            return HttpResponseRedirect('/bio/index/')
        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print(user_form.errors)

    # Something went wrong, redirect back to login page

    messages.add_message(request, messages.INFO, 'Form Errors or User Already Exists')
    return render(request, 'SilentD/login.html', {})


def user_login(request):
    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        # We use request.POST.get('<variable>') as opposed to request.POST['<variable>'],
        # because the request.POST.get('<variable>') returns None, if the value does not exist,
        # while the request.POST['<variable>'] will raise key error exception
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            print(user)
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/bio/index/')
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            error_message = "Invalid Login Details Provided"
            messages.add_message(request, messages.ERROR, error_message)

            print("Invalid login details: {0}, {1}".format(username, password))
            return render(request, "SilentD/login.html", {})

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render(request, 'SilentD/login.html', {})


# Use the login_required() decorator to ensure only those logged in can access the view.
@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)

    # Take the user back to the homepage.
    return HttpResponseRedirect('/')


# csrf_exempt decorator allowing easier Dropzone.js compatibility.
@csrf_exempt
@login_required
def file_upload(request):
    username = None
    if request.user.is_authenticated():
        username = request.user.username

    if request.method == 'POST':
        print("User %s uploading %s " % (username, request.FILES))
        file_name = str(request.FILES['file'])

        if 'fastq.gz' or 'fastq' in file_name:
            # creating a new Data element for the file to be saved in the database

            newdoc = Data(user=username, type='FastQ')
            newdoc.save()
            newdoc.file = request.FILES['file']
            newdoc.save()
            newdoc.name = newdoc.file.name.split('/')[-1]
            newdoc.save()

        return render(request, 'SilentD/file_upload.html', {})

    print('No Match Found')
    return render(request, 'SilentD/file_upload.html', {})


@login_required
def projects(request):

    # Project.objects.all().delete()        While in development env, use to delete all data in databases
    # Data.objects.all().delete()
    # Results.objects.all().delete()

    username = ''
    if request.user.is_authenticated():
        username = request.user.username

    if request.method == 'POST':
        print(request.POST)

        if "job" in request.POST:  # only executes if a job action is selected

            job = request.POST.get('job')
            proj_id = request.POST.get('project_id')
            pro_obj = Project.objects.get(id=proj_id)

            if job == 'genesippr_start':
                print("Started the GeneSippr job.")
                pro_obj.genesippr_results = "Running"
                pro_obj.save()
                genesippr_task.delay(pro_obj.id)  # run a genesippr job, by putting the task through celery with delay()

        elif "genesippr_results" in request.POST:
            # currently loads all projects from the user into view
            all_projects = Project.objects.filter(user=username)
            print(all_projects)
            print("print done")
            return render(request, 'SilentD/genesippr.html', {'projects': all_projects})

        elif "delete" in request.POST:
            proj_id = request.POST['id']
            delete_project(proj_id)
            pro_obj = Project.objects.get(id=proj_id)
            delete_project(proj_id)
            pro_obj.delete()

    # Retrieve all uploaded files relating to the user
    fastq_projects = Project.objects.filter(user=username, type='fastq')
    return render(request, 'SilentD/projects.html', {'fastq_projects': fastq_projects})


@login_required
def create_project(request):
    username = ''
    if request.user.is_authenticated():
        username = request.user.username

    project_creation_fail = False

    if request.method == 'POST':
        print(request.POST)
        if 'name' in request.POST:
            description = request.POST.get('name')
            if request.POST.get('id'):
                # FastQ
                data_file_list = request.POST.get('id')
            else:
                # incase no id is uploaded (not in database) ask the user to reupload the files
                error_message = "Error! Files uploaded did not exist in the database. " \
                                "Please try to reupload the files again, and delete the old ones."
                messages.add_message(request, messages.ERROR, error_message)

                fastq_projects = Project.objects.filter(user=username, type='fastq')
                return render(request, 'SilentD/projects.html', {'fastq_projects': fastq_projects})

            project_type = request.POST.get('type')

            if data_file_list and description and project_type:
                data_file_list2 = data_file_list.replace('id=', '')
                data_list = data_file_list2.split('&')

                data_obj_list = []
                filename_list = []
                failed_list = []
                for item in data_list:
                    data_obj = Data.objects.get(id=item)
                    data_obj_list.append(data_obj)
                    filename_list.append(str(data_obj.name))

                if project_type == 'fastq':
                    # Conditions below are tested in order for files to be added to a project
                    # File count is an even number
                    # Files have proper formatted _R1 or _R2 in file name
                    # Each file is paired with its other R value

                    if len(data_list) % 2 != 0:
                        # List has uneven number of files due retrieval error
                        project_creation_fail = True
                    else:
                        # Create a dictionary of strain names, and populate with found R values
                        file_dict = defaultdict(list)
                        for filename in filename_list:
                            name = filename.split("_")[0]
                            if '_R1' in filename:
                                rvalue = 'R1'
                                file_dict[name].append(rvalue)
                            elif '_R2' in filename:
                                rvalue = 'R2'
                                file_dict[name].append(rvalue)
                            else:
                                error_message = "Error! File %s does not have a correct RValue in the format _R1 or _R2" \
                                                % name
                                messages.add_message(request, messages.ERROR, error_message)

                        # Verify all files are paired and have a match of R1 and R2, not R1,R1, R2,R2 or only 1 R value

                        for key, value in file_dict.items():
                            if len(value) == 2:
                                if (value[0] == "R1" and value[1] == "R2") or (value[0] == "R2" and value[1] == "R1"):
                                    print("Match!")
                                else:
                                    project_creation_fail = True
                                    failed_list.append(key)
                                    error_message = "Error! %s has two R1 or two R2 values" % key
                                    messages.add_message(request, messages.ERROR, error_message)
                            else:
                                project_creation_fail = True
                                failed_list.append(key)
                                error_message = "Error! 2 Files must be associated with %s" % key
                                messages.add_message(request, messages.ERROR, error_message)

                if project_creation_fail:
                    error_message = "Error! No paired match found for the Following:  " + ", ".join(failed_list) + \
                                    ", Ensure each pair of files contains *_R1_001.fastq.gz and *_R2_001.fastq.gz"
                    messages.add_message(request, messages.ERROR, error_message)
                else:
                    # Create a Fastq Project
                    new_project = Project(user=username, description=description)
                    new_project.save()
                    for obj in data_list:
                        new_project.files.add(obj)
                    new_project.num_files = len(data_list)
                    new_project.type = request.POST.get('type')
                    new_project.save()

                    print("Moving files to the project directory./n")
                    move_files(new_project.id)
                    success_message = "The project, " + description + ", was created successfully."
                    messages.add_message(request, messages.SUCCESS, success_message)

            # Send user to the Projects main page
            fastq_projects = Project.objects.filter(user=username, type='fastq')
            return render(request, 'SilentD/projects.html', {'fastq_projects': fastq_projects})

        else:
            file_id = request.POST.get('id')
            delete_file(file_id)
            Data.objects.get(id=file_id).delete()

    # Retrieve all uploaded files relating to the user
    fastqs = Data.objects.filter(user=username, type='FastQ').exclude(file__isnull=True).exclude(file="")
    # Convert file size to megabytes
    for d in fastqs:
        if d.file:
            if os.path.isfile(d.file.name):
                file_size = d.file.size /1000 /1000
                d.size = round(file_size, 2)  # round the file size to 2 decimal digits, unless second digit is a 0
            else:
                # For some reason the file has been deleted, update the databases to remove this entry
                Data.objects.get(id=d.id).delete()
        else:
            d.size = 0
    return render(request, 'SilentD/create_project.html', {'fastqs': fastqs})


@login_required
def genesippr(request):
    username = ''
    if request.user.is_authenticated():
        username = request.user.username

    if request.POST:
        table_dict = OrderedDict()
        file_dict = OrderedDict()
        print(request.POST)
        # Send back the result file in a table, either ARG-ANNOT or ResFinder
        if 'id' in request.POST:
            proj_id = request.POST['id']
            proj_obj = Project.objects.get(id=proj_id)

            if 'result' in request.POST:  # only executes if the results button was selected

                results_GDCS = get_resultdir(proj_obj, result_folder_names.folder_GDCS)

                # get the path to the reports needed in the folders
                with open(results_GDCS) as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        # Check if entry exists in the database already, if not create new results for the strain
                        # The basic results are populated only from the GDCS file, if an entry is not in there
                        # it will not be displayed
                        strain = row['Strain']
                        if Results.objects.filter(description=proj_obj.description, strain=strain).exists():
                            print('The results for: %s exist in database, no need to create again.' % strain)
                        else:
                            print('Creating database entries for the results of strain: %s' % strain)
                            new_result = Results(user=username, description=proj_obj.description)
                            new_result.save()
                            new_result.strain = strain
                            new_result.genus = row['Genus']
                            new_result.matches = row['Matches']
                            new_result.runtype = get_review_result(new_result.genus, new_result.matches)
                            new_result.project_id = proj_id
                            new_result.save()

                all_projects = Project.objects.filter(user=username)
                results_dict = Results.objects.filter(user=username, description=proj_obj.description)
                return render(request, 'SilentD/genesippr.html',
                              {'projects': all_projects, 'current_project': proj_obj, 'results': results_dict})

            if 'Strain' in request.POST:  # only executes if the more details button is selected

                results_genesippr = get_resultdir(proj_obj, result_folder_names.folder_genesippr)
                strain = request.POST['Strain']
                genus = request.POST['Genus']

                with open(results_genesippr) as csvfile:
                    reader = csv.DictReader(csvfile)

                    # ensures to match the Strain and Genus in proper order from the table, then gets the genes after
                    for row in reader:
                        if strain in row['Strain']:
                            file_dict['Strain'] = strain
                            file_dict['Genus'] = genus

                            for key, value in row.items():
                                if value:
                                    if strain not in value and genus not in value:
                                        table_dict[key] = value

                if not table_dict:  # check to see if report was found, will display no further info if not found
                    print("No report was found for the following strain: ", strain, ".")

                all_projects = Project.objects.filter(user=username)
                results_dict = Results.objects.filter(user=username, description=proj_obj.description)
                return render(request, 'SilentD/genesippr.html', {'projects': all_projects, 'results': results_dict,
                                                                  'current_project': proj_obj,
                                                                  'genesippr': table_dict, 'info': file_dict})

    all_projects = Project.objects.filter(user=username)
    return render(request, 'SilentD/genesippr.html', {'projects': all_projects})
