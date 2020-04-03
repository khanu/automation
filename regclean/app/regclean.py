#!/usr/bin/python

import sys
import os.path
import subprocess
from subprocess import check_output
from flask import Flask, render_template, request, Response, stream_with_context
import time
from time import sleep
from datetime import datetime

app = Flask(__name__)

directory = '/app/registry/'

@app.route("/")
@app.route("/index")
def index():
    return 'Flask is running!'

@app.route('/garbage_collect', methods=['GET', 'POST'])
def garbage_collect():
	project = request.args.get("image_name")
	return render_template('index.html', project = project)

#@app.errorhandler(Exception)
#def all_exception_handler(error):
#	return 'Oops!\nNothing Found', 500

@app.route('/images', methods=['GET'])
def show_images():
	image_name = request.args.get("image_name")
	if os.path.isdir(os.path.join(directory, str(image_name))):
		cmd = "find '{0}'/'{1}'/_manifests/tags/ -type d -printf \"%P\n\" |cut -d'/' -f 1 | uniq | sort | sed '/^$/d'".format(str(directory), str(image_name))

		try:
			sp = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
			output = sp.communicate()[0]

		except Exception as ex:
			template = "An exception of type {0} occurred. Arguments:\n{1!r}"
			message = template.format(type(ex).__name__, ex.args)
			print(message)

		image_list = output.splitlines()
		return render_template('images.html', image_list = image_list, image_name = image_name)

@app.route('/remove', methods=['POST'])
def remove_images():
	image_name = request.form.get('image_name')
	oldest_to_keep = request.form.get('selected_version')
	if os.path.isdir(os.path.join(directory, str(image_name), '_manifests/tags/', str(oldest_to_keep))):
		cmd = "find '{0}'/'{1}'/_manifests/tags/ -type d ! -newer '{2}'/'{3}'/_manifests/tags/'{4}' -printf \"%P\n\" |grep -v ^latest|grep -v '{5}' |cut -d'/' -f 1 | uniq | sort | sed '/\^\$/d'" .format(str(directory), str(image_name), str(directory), str(image_name), str(oldest_to_keep), str(oldest_to_keep))

		try:
			sp = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
			output = sp.communicate()[0].decode('utf-8')

		except Exception as ex:
			template = "An exception of type {0} occurred. Arguments:\n{1!r}"
			message = template.format(type(ex).__name__, ex.args)
			print(message)
	images_for_removal = output.splitlines()
	return render_template('remove.html', image_name = image_name, images_for_removal = images_for_removal)

@app.route('/delete', methods=["POST"])
def delete_images():
	blob_list = []
	image_name = request.form.get('image_name')
	image = request.form.getlist('image')
	image = list(filter(None, image))
	for i in range(len(image)):
		cmd = "ls {0}{1}/_manifests/tags/{2}/index/sha256/".format(str(directory), str(image_name), (image[i]))
		if os.path.isdir(os.path.join(directory, str(image_name), '_manifests/tags/', (image[i]), '/index/sha256/')):
			digest_hash = check_output(cmd, shell=True).decode("utf8")

			delete_manifest = "rm -rf {0}{1}/_manifests/tags/{2}/index/sha256/{3}/".format(str(directory), str(image_name), (image[i]), str(digest_hash))
			if os.path.isdir(os.path.join(directory, str(image_name), '_manifests/tags/', (image[i]), '/index/sha256/', str(digest_hash))):
				p = subprocess.Popen(delete_manifest, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

			delete_revision = "rm -rf {0}{1}/_manifests/revisions/sha256/{2}".format(str(directory), str(image_name), str(digest_hash))
			if os.path.isdir(os.path.join(directory, str(image_name), '_manifests/revisions/sha256/', str(digest_hash))):
				p = subprocess.Popen(delete_revision, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		

	gc = 'ssh -o "StrictHostKeyChecking no" -l root drglcdcpvm001.nyumc.org "/bin/sh /home/devk01/garbage_collect.sh"'
	run_gc = subprocess.check_call(gc, shell=True)

	if run_gc == 0:
		return render_template('delete.html')


if __name__== '__main__':
    app.run(host= '0.0.0.0')
