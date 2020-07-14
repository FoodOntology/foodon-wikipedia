"""

Author: Anoosha Sehar
License: Creative Commons Zero v1.0 Universal.

This script uses Wikipedia Api to fetch definitions, images &
metadata of the Food Ontology terms for FoodON.

"""
import sys
# A Python library to parse data from Wikipedia.
import wikipedia
import requests
import json
import os
# Python's API to fetch a variety of information from the Wikipedia
# website
import wikipediaapi
import pandas as pd
import argparse
from time import process_time

parser = argparse.ArgumentParser()
required_name = parser.add_argument_group('required arguments')
required_name.add_argument("-i", "--input",
                           help="Tsv file as an input file. File must "
                                "contain a column of label, definition "
                                "status, definition, image url, "
                                "image status, image provider and "
                                "image license",
                           required=True)
required_name.add_argument("-o", "--output",
                           help="Output file in .tsv format",
                           required=True)

args = parser.parse_args()
if not args.input:
    print("No input file provided")
if not args.output:
    print("No output file provided")
if not (args.input or args.output):
    sys.exit(1)

file_input = args.input
file_output = args.output


def get_summary(term_label):
    try:
        # Function to fetch first two sentences of the summary.
        summary = wikipedia.summary(term_label, sentences=2,
                                    auto_suggest=True)
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
    wiki_request = \
        "http://en.wikipedia.org/w/api.php?action=query&" \
        "prop=pageimages&piprop=thumbnail&pithumbsize=640&" \
        "format=json&&titles= "
    try:
        resize_result = wikipedia.search(search_term, results=1)
        resize_wkpage = wikipedia.WikipediaPage(title=resize_result[0])
        resize_title = resize_wkpage.title
        resize_response = requests.get(wiki_request + resize_title)
        resize_json_data = json.loads(resize_response.text)
        resize_img_link = \
            list(resize_json_data['query']['pages'].values())[0][
                'thumbnail']['source']
        return resize_img_link
    except:
        return 0


def get_wiki_image_orignal(search_term_orignal):
    wiki_request_orignal = \
        "http://en.wikipedia.org/w/api.php?action=query&" \
        "prop=pageimages&format=json&piprop=original&titles="
    try:
        result = wikipedia.search(search_term_orignal, results=1)
        wkpage = wikipedia.WikipediaPage(title=result[0])
        title = wkpage.title
        response = requests.get(wiki_request_orignal + title)
        json_data = json.loads(response.text)
        img_link = list(json_data['query']['pages'].values())[0]['original'][
                'source']

        if img_link:
            img_license, img_provider = extract_image_license(
                image_name=os.path.basename(img_link))
            # Checking for resize image
            if get_wiki_image_resize(search_term=search_term_orignal):
                img_link_resize = get_wiki_image_resize(
                    search_term=search_term_orignal)
                if not img_link_resize == 0:
                    img_link = img_link_resize
        # A list of image data which have image link on index 0,
        # image license on 1st index and image provider on 2nd index.
        img_data = [img_link, img_license, img_provider]

        return img_data
    except:
        return []


def extract_image_license(image_name):
    try:
        start_of_end_point_str = \
            "https://commons.wikimedia.org/w/api.php?action=query&" \
            "titles=File:"
        end_of_end_point_str = \
            "&prop=imageinfo&iiprop=user|userid|canonicaltitle|url|" \
            "extmetadata&format=json"
        result = requests.get(
            start_of_end_point_str + image_name + end_of_end_point_str)
        result = result.json()
        page_id = next(iter(result['query']['pages']))
        image_info = result['query']['pages'][page_id]['imageinfo']
        return (image_info[0]['extmetadata']["UsageTerms"]['value']), (
            image_info[0]["user"])

    except:
        return 0


if __name__ == "__main__":
    lang = wikipediaapi.Wikipedia('en')
    print("\n\n Reading Input File" + str(file_input) + "\n\n")
    df = pd.read_csv(file_input, sep="\t", header=0, encoding='utf-8')
    print("Fetching definition(s) images and Metadata from Wikipedia "
          "\n\n")
    # label column in dataframe df
    for x in range(1, len(df['label'])):
        if pd.notna(df.loc[x, 'label']):
            # if definition status is zero OR definition status has nan
            # value
            if (df.loc[x, 'definition status'] == 0) or \
                    (pd.isna(df.loc[x, 'definition status'])):
                wiki_summary = get_summary(df.loc[x, 'label'])
                if not wiki_summary == 0:
                    df.loc[x, 'definition'] = wiki_summary
                    df.loc[x, 'definition status'] = 3
                    wiki_url = get_summary_url(df.loc[x, 'label'])
                    df.loc[x, 'definition source'] = wiki_url
                else:
                    df.loc[x, 'definition status'] = 1
            # Image status is zero or nan/empty
            if (df.loc[x, 'image status'] == 0) or \
                    (pd.isna(df.loc[x, 'image status'])):
                # store the value of function (returning list) in wiki
                # image, only when image status is 0 or nan.
                wiki_image = get_wiki_image_orignal(
                    search_term_orignal=df.loc[x, 'label'])
                if not len(wiki_image) == 0:
                    # Store image url in 'image url' column
                    df.loc[x, 'image url'] = wiki_image[0]
                    # Updating image status
                    df.loc[x, 'image status'] = 3
                    # Storing the value of img_license in
                    # 'license' Column
                    df.loc[x, 'license'] = wiki_image[1]
                    # Storing the value of image provider in
                    # 'image provider' Column
                    df.loc[x, 'image provider'] = wiki_image[2]
                else:
                    df.loc[x, 'image status'] = 1

    filename_tsv = file_output
    with open(filename_tsv, 'w', encoding="utf-8") as write_tsv:
        write_tsv.write(
            df.to_csv(sep='\t', line_terminator='\n', index=False))

    print("\n\n Output Written in " + str(file_output) + "\n\n")

# Get the current processor
# time in seconds
time_stop = process_time()

# print the current
# processor time
print("Elapsed time during the whole program in seconds:",
                                         time_stop)
print("Current processor time (in minutes):", (time_stop)/60)

