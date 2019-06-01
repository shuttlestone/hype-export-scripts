#!/usr/bin/python

# 	CodePen.hype-export.py
#		Export Script to upload to CodePen
#		Based on instructions at:
#			https://blog.codepen.io/documentation/api/prefill/
#
#		Installation, usage, and additional info: 
#			https://tumult.com/hype/export-scripts/
#
#		MIT License
#		Copyright (c) 2019 Tumult Inc.
#

import argparse
import json
import sys
import distutils.util
import os

# update info
current_script_version = 1
version_info_url = "https://static.tumult.com/hype/export-scripts/CodePen/latest_script_version.txt" # only returns a version number
download_url = "https://tumult.com/hype/export-scripts/CodePen/" # gives a user info to download and install
minimum_update_check_duration_in_seconds = 60 * 60 * 24 # once a day
defaults_bundle_identifier = "com.tumult.Hype2.hype-export.CodePen"


class HypeURLType:
	Unknown = 0
	HypeJS = 1
	Resource = 2
	Link = 3
	ResourcesFolder = 4

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--hype_version')
	parser.add_argument('--hype_build')
	parser.add_argument('--export_uid')

	parser.add_argument('--get_options', action='store_true')

	parser.add_argument('--replace_url')
	parser.add_argument('--url_type')
	parser.add_argument('--is_reference', default="False")
	parser.add_argument('--should_preload')

	parser.add_argument('--modify_staging_path')
	parser.add_argument('--destination_path')
	parser.add_argument('--export_info_json_path')
	parser.add_argument('--is_preview', default="False")

	parser.add_argument('--check_for_updates', action='store_true')
	
	args, unknown = parser.parse_known_args()
	

	## --get_options
	##		return arguments to be presented in the Hype UI as a dictionary:
	##		'export_options' is a dictionary of key/value pairs that make modifications to Hype's export/preview system. Some useful ones:
	##			'exportShouldInlineHypeJS' : boolean
	##			'exportShouldInlineDocumentLoader' : boolean
	##			'exportShouldUseExternalRuntime' : boolean
	##			'exportExternalRuntimeURL' : string
	##			'exportShouldSaveHTMLFile' : boolean
	##			'indexTitle' : string
	##			'exportShouldBustBrowserCaching' : boolean
	##			'exportShouldIncludeTextContents' : boolean
	##			'exportShouldIncludePIE' : boolean
	##			'exportSupportInternetExplorer6789' : boolean
	##			'initialSceneIndex' : integer
	##		'save_options' is a dictionary of key/value pairs that for determining when/how to export. valid keys:
	##			'file_extension' : the final extension when exported (ex. "zip")
	##			'allows_export' : should show up in the File > Export as HTML5 menu and Advanced Export
	##			'allows_preview' : should show up in the Preview menu, if so --is_preview True is passed into the --modify_staging_path call
	##		'document_arguments' should be an array of keys, these will be passed to subsequent calls via --key value
	##		'extra_actions' should be an array of dictionaries
	##			'label': string that is the user presented name
	##			'function': javascript function to call if this action is triggered, just the name of it
	##			'arguments': array of dictionaries that represent arguments passed into the function
	##				'label': string that is presented to Hype UI
	##				'type': string that is either "String" (will be quoted and escaped) or "Expression" (passed directly to function argument as-is)
	if args.get_options:		
		def export_options():
			cdnPath = "https://cdn.jsdelivr.net/gh/tumult/hype-runtime"
			
			return {
				"exportShouldInlineHypeJS" : False,
				"exportShouldInlineDocumentLoader" : False,
				"exportShouldUseExternalRuntime" : True,
				"exportExternalRuntimeURL" : cdnPath,
				"exportShouldSaveHTMLFile" : True,
				"exportShouldNameAsIndexDotHTML" : True,
				#"indexTitle" : "",
				"exportShouldBustBrowserCaching" : False,
				"exportShouldIncludeTextContents" : False,
				"exportShouldIncludePIE" : False,
				"exportSupportInternetExplorer6789" : False,
				"exportShouldSaveRestorableDocument" : False,
			}

		def save_options():
			return {
				"file_extension" : "html",
				"allows_export" : True,
				"allows_preview" : False,
			}
		
		options = {
			"export_options" : export_options(),
			"save_options" : save_options(),
			"min_hype_build_version" : "574", # build number (ex "574") and *not* marketing version (ex "3.6.0")
			#"max_hype_build_version" : "10000", # build number (ex "574") and *not* marketing version (ex "3.6.0")
		}
	
		exit_with_result(options)


	## --replace_url [url] --url_type [HypeURLType] --is_reference [True|False] --should_preload [None|True|False] --is_preview [True|False] --export_uid [identifier]
	##		return a dictionary with "url", "is_reference", and optional "should_preload" keys
	##		if HypeURLType.ResourcesFolder, you can set the url to "." so there is no .hyperesources folder and everything
	##		is placed next to the .html file
	##		should_preload may be None type in cases where it won't be used
	elif args.replace_url != None:
		url_info = {}
		url_info['is_reference'] = bool(distutils.util.strtobool(args.is_reference))
		if args.should_preload != None:
			url_info['should_preload'] = bool(distutils.util.strtobool(args.should_preload))
		
		if int(args.url_type) == HypeURLType.ResourcesFolder:
			url_info['url'] = "."
		else:
			url_info['url'] = args.replace_url
				
		exit_with_result(url_info)


	## --modify_staging_path [filepath] --destination_path [filepath] --export_info_json_path [filepath] --is_preview [True|False] --export_uid [identifier]
	##		return True if you moved successfully to the destination_path, otherwise don't return anything and Hype will make the move
	##		make any changes you'd like before the save is complete
	##		for example, if you are a zip, you need to zip and write to the destination_path
	##		or you may want to inject items into the HTML file
	##		if it is a preview, you shouldn't do things like zip it up, as Hype needs to know where the index.html file is
	##		export_info_json_path is a json object holding keys:
	##			html_filename: string that is the filename for the html file which you may want to inject changes into
	##			main_container_width: number representing the width of the document in pixels
	##			main_container_height: number representing the height of the document in pixels
	##			document_arguments: dictionary of key/value pairs based on what was passed in from the earlier --get_options call
	##			extra_actions: array of dictionaries for all usages of the extra actions. There is no guarantee these all originated from this script or version.
	##				function: string of function name (as passed in from --get_options)
	##				arguments: array of strings
	elif args.modify_staging_path != None:
		import os
		import string
		import urllib
		import urllib2
		
		# read export_info.json file
		export_info_file = open(args.export_info_json_path)
		export_info = json.loads(export_info_file.read())
		export_info_file.close()

		# get contents of .html file
		index_path = os.path.join(args.modify_staging_path, export_info["html_filename"])
		index_contents = None
		with open(index_path, 'r') as target_file:
			index_contents = target_file.read()

		# find javascript file and get its contents
		js_contents = ""		
		# r=root, d=directories, f = files
		for r, d, f in os.walk(args.modify_staging_path):
			for file in f:
				if 'generated_script.js' in file:
					js_file = open(os.path.join(r, file))
					js_contents = js_file.read()
					js_file.close()		

		# page that we will load to automatically post the codepen
		codepenFileContents = """<!doctype html>
			<html>
			<head>
			<title>CodePen Loader</title>
			<script>
			window.onload = function () {
				var jsonData = ${jsonData};

				var formElement = document.createElement("form");
				formElement.setAttribute("action", "https://codepen.io/pen/define");
				formElement.setAttribute("method", "POST");
				formElement.setAttribute("name", "codepen_poster");
				document.body.appendChild(formElement);

				var hiddenInputElement = document.createElement("input");
				hiddenInputElement.setAttribute("type", "hidden");
				hiddenInputElement.setAttribute("name", "data");
				hiddenInputElement.setAttribute("value", jsonData);
				formElement.appendChild(hiddenInputElement);

				document.forms['codepen_poster'].submit();
			};

			</script>
			</head>
			<body></body>
			</html>
		"""		
		
		# dump twice to escape strings
		jsonDataAsString = json.dumps(json.dumps({ "title" : os.path.basename(args.destination_path), "editors" : "101", "html" : index_contents, "js" : js_contents }))
		
		# make sure script tag isn't terminated in string otherwise it will lead to issues
		jsonDataAsString = jsonDataAsString.replace("</script>", "</scr\"+\"ipt>")
				
		codepenFileContents = codepenFileContents.replace("${jsonData}", jsonDataAsString)

		import shutil
		shutil.rmtree(args.destination_path, ignore_errors=True)

		codepen_file_path = os.path.join(args.destination_path)
		codepen_file = open(codepen_file_path, "w+")
		codepen_file.write(codepenFileContents)
		codepen_file.close()
				
		import subprocess
		subprocess.Popen(['/usr/bin/open', codepen_file_path])

		exit_with_result(True)
		

	## --check_for_updates
	##		return a dictionary with "url", "from_version", and "to_version" keys if there is an update, otherwise don't return anything and exit
	##		it is your responsibility to decide how often to check
	elif args.check_for_updates:
		import subprocess
		import urllib2
		
		last_check_timestamp = None
		try:
			last_check_timestamp = subprocess.check_output(["defaults", "read", defaults_bundle_identifier, "last_check_timestamp"]).strip()
		except:
			pass

		try:
			timestamp_now = subprocess.check_output(["date", "+%s"]).strip()
			if (last_check_timestamp == None) or ((int(timestamp_now) - int(last_check_timestamp)) > minimum_update_check_duration_in_seconds):
				subprocess.check_output(["defaults", "write", defaults_bundle_identifier, "last_check_timestamp", timestamp_now])
				request = urllib2.Request(version_info_url, headers={'User-Agent' : "Magic Browser"})
				latest_script_version = int(urllib2.urlopen(request).read().strip())
				if latest_script_version > current_script_version:
					exit_with_result({"url" : download_url, "from_version" : str(current_script_version), "to_version" : str(latest_script_version)})
		except:
			pass


# UTILITIES

# communicate info back to Hype
# uses delimiter (20 equal signs) so any above printing doesn't interfere with json data
def exit_with_result(result):
	import sys
	print "===================="
	print json.dumps({"result" : result})
	sys.exit(0)

if __name__ == "__main__":
	main()
