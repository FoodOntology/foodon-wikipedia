"""

Author: Anoosha Sehar
License: Creative Commons Zero v1.0 Universal.

This script uses Wikipedia Api to fetch definitions, images & metadata\n of the Food Ontology terms for FoodON.

"""


import wikipedia					#A Python library to access and parse data from Wikipedia.
import requests
import json
import os
import numpy
import wikipediaapi					#Python's Wikipedia API to fetch a variety of information from the Wikipedia website
import urllib.request
import pandas as pd
import argparse

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
requiredName = parser.add_argument_group('required arguments')
requiredName.add_argument("-i", "--inputfile", help= "Tsv file as an input file. File must contain a column of 'label', 'definition status', 'definition', 'image url', 'image status', 'image provider', 'license'", required=True )
requiredName.add_argument("-o", "--outputfile", help= "Output file in .tsv format",required=True)

args = parser.parse_args()
if not args.inputfile: print("No input file provided")
if not args.outputfile: print("No output file provided")
if not (args.inputfile or args.outputfile): sys.exit(1)

outputfile = args.outputfile
inputfile = args.inputfile


def get_summary(term_label):
	try:
		summary = wikipedia.summary(term_label,sentences=2,auto_suggest=True) 		##Function from wikipedia wrapper to fetch first two sentences of the summary.
		summary = summary.replace("\n", " ")
		return summary
	except:
		return 0


def get_summary_url(term_url):
	try:
		summary_url = wikipedia.page(term_url)
		return summary_url.url
	except:
		return 0


def get_wiki_image_resize(search_term):
	wiki_request = 'http://en.wikipedia.org/w/api.php?action=query&prop=pageimages&piprop=thumbnail&pithumbsize=640&format=json&&titles='
	try:
		resize_result = wikipedia.search(search_term, results = 1)
		resize_wkpage = wikipedia.WikipediaPage(title = resize_result[0])
		resize_title = resize_wkpage.title
		resize_response  = requests.get(wiki_request+resize_title)
		resize_json_data = json.loads(resize_response.text)
		resize_img_link = list(resize_json_data['query']['pages'].values())[0]['thumbnail']['source']
		return resize_img_link
	except:
		return 0


def get_wiki_image_orignal(search_term_orignal):
	wiki_request_orignal = 'http://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=original&titles='
	try:
		result = wikipedia.search(search_term_orignal, results = 1)
		wkpage = wikipedia.WikipediaPage(title = result[0])
		title = wkpage.title
		response  = requests.get(wiki_request_orignal + title)
		json_data = json.loads(response.text)
		img_link = list(json_data['query']['pages'].values())[0]['original']['source']
		if img_link:
			img_license, img_provider= extract_image_license(image_name=os.path.basename(img_link))
														#Checking for resize image
			if get_wiki_image_resize(search_term=search_term_orignal):
				img_link_resize = get_wiki_image_resize(search_term = search_term_orignal)
				if not img_link_resize == 0:
					img_link = img_link_resize
		img_data=[]   											#A list of image data which have image link on index 0, image license on index 1 and image provider on index 2.
		img_data.append(img_link)
		img_data.append(img_license)
		img_data.append(img_provider)
		return img_data
	except:
		return []


def extract_image_license(image_name):
	try:
		start_of_end_point_str = 'https://commons.wikimedia.org/w/api.php?action=query&titles=File:'
		end_of_end_point_str = '&prop=imageinfo&iiprop=user|userid|canonicaltitle|url|extmetadata&format=json'
		result = requests.get(start_of_end_point_str + image_name + end_of_end_point_str)
		result = result.json()
		page_id = next(iter(result['query']['pages']))
		image_info = result['query']['pages'][page_id]['imageinfo']
		return (image_info[0]['extmetadata']["UsageTerms"]['value']),(image_info[0]["user"])
	except:
		return 0


if __name__ == "__main__":
	lang = wikipediaapi.Wikipedia('en')
	print("\n\n Reading Input File" + str(inputfile) + "\n\n")
	df = pd.read_csv(inputfile,sep="\t",header=0, encoding= 'utf-8')
	print("Fetching definition(s) iamges and Metadata from wikipedia \n\n")
	for x in range(1,len(df['label'])): 									#label column in dataframe df
		if pd.notna(df.loc[x,'label']):
			if (df.loc[x,'definition status'] == 0) or (pd.isna(df.loc[x,'definition status'])): 	#if definition status is zero OR definition status has nan value
				wiki_summary = get_summary(df.loc[x,'label'])
				if not wiki_summary == 0:
					df.loc[x,'definition'] = wiki_summary	 				#Assigning value of wiki_summary to definition column
					df.loc[x,'definition status'] = 1	 				#Update the definition status to 1 after fetching definition
					wiki_url = get_summary_url(df.loc[x,'label'])
					df.loc[x,'definition source'] = wiki_url

			if (df.loc[x,'image status']== 0) or (pd.isna(df.loc[x,'image status'])):  		#Image status is zero or nan/empty
				wiki_image = get_wiki_image_orignal(search_term_orignal = df.loc[x,'label']) 	#store the value of function (returning list) in wiki image, only when image status is 0 or nan.
				if not len(wiki_image) ==0:
					df.loc[x,'image url'] = wiki_image[0]   				#Store the image url in 'image url' column
					df.loc[x,'image status'] = 1  						#Update the image status to 1
					df.loc[x,'license'] = wiki_image[1] 					#Store the value of license in 'license' Column
					df.loc[x,'image provider'] = wiki_image[2] 				#Store the value of image provider in 'image provider' Column

	w_filenameTSV = (outputfile)
	with open(w_filenameTSV,'w',encoding="utf-8") as write_tsv:
		write_tsv.write(df.to_csv(sep='\t',line_terminator='\n',index=False))

	print("\n\n Output Written in " + str(outputfile) + "\n\n")
