#!/usr/bin/env python

# Convert a bunch of HTML files into a DOCX
# 

from bs4 import BeautifulSoup
from docx import Document
from htmldocx import HtmlToDocx
from re import match
import copy
import os

# Contains the directory_list
from list import directory_list, avoid_list

# Where to find the HTML
base_directory = "../ry-tietomallit/docs/_site/"
# Base URL online
base_url = "https://tietomallit.ymparisto.fi/"

counters = {"main_content_wrap":0, "page_body":0, "body": 0, "html_files":0}

# Recurse from root down, avoid paths in avoidlist
# Return list of all HTML files found, width first search
# root: ...of the HTML tree
# dir:  relative to the root
# avoid_list: directories not to recurse into
# avoid: is the avoid_list in use
def dig_for_html(root, dir, avoid_list, avoid):    
    if avoid and dir in avoid_list:
        return []
    files = os.listdir(os.path.join(root, dir))

    html_files = list(filter(lambda n: match(".*\.html$", n), files))
    html_files = list(map(lambda n: os.path.join(dir,n), html_files))
    
    sub_dirs = list(filter(lambda n: os.path.isdir(os.path.join(root, dir, n)), files))

    for sub in sub_dirs:
        html_files.extend(dig_for_html(root, os.path.join(dir,sub), avoid_list, True))
    
    
    return html_files



# Build list of HTML files we want to include in the DocXs.
# We want to avoid recursing into subdirectories that are in
# the avoid list, but the first level can't use the avoid list
# as all the directories are in it.
avoid_list.extend(directory_list)
for dir in directory_list:
    # Where it all will end up
    if dir == "":
        output_file = "rytj-sisalto.docx"
    else:
        output_file = dir.translate(str.maketrans( {'/': '_'})) + ".docx"

    # Start things up
    docx = Document()
    converter = HtmlToDocx()

    html_files = dig_for_html(base_directory, dir, avoid_list, False)
    # print(dir + " ", len(html_files), " HTML files found")
    counters["html_files"] = counters["html_files"] + len(html_files)
    
    # do stuff to documents
    for html in html_files:
        f = open(os.path.join(base_directory, html))
        text = f.read()
        #print(html + ":", len(text), " bytes")
        html_doc = BeautifulSoup(text, "html.parser")

        # Oh nice, some of the files have multiple <title> elements...
        titles = html_doc.find_all("title", limit=1)
        # But then, it looks like we can get a collection of Tag (or str?),
        # and of course it can be empty if there is no <title>
        if len(titles):
            title = titles[0].contents[0] if len(titles[0].contents) else ""
        else:
            title = "EI OTSIKKOA"

        link = "<a href='" + base_url + html + "'>" + html + "</a>"
        converter.add_html_to_document("<h2>&gt;&gt; " + title + " ( " + link + " )</h2>", docx)

           
        # Some of our documents have a div with id="main_content_wrap",
        # use the contents of that if present
        bread_text = html_doc.find("div",id="main_content_wrap")
        if bread_text is not None:
            try:
                converter.add_html_to_document(str(bread_text), docx)
                counters["main_content_wrap"] = counters["main_content_wrap"] + 1
                print(html + ": main_content_wrap", len(str(bread_text)) )
            except:
                print(html + ": EXCEPTION/main_content_wrap", len(str(bread_text)) )
            continue

        # The files with a <div class="PageBody"> seem to have
        # tables with colspan and rowspan, which tickle a bug in htmldocx.
        # (see https://github.com/pqzx/html2docx/search?q=indexerror&type=issues)
        bread_text = html_doc.find("div",class_="PageBody")
        if bread_text is not None:
            try:
                # The converter object will be unusable if we encounter an exception
                backup = copy.deepcopy(converter)
                converter.add_html_to_document(str(bread_text), docx)
                counters["page_body"] = counters["page_body"] + 1
                print(html + ": pagebody", len(str(bread_text)) )
            except:
                # Roll back possible fuckups?
                converter = backup
                print(html + ": EXCEPTION/pagebody", len(str(bread_text)) )
            continue

        # Last resort, use the body element
        bread_text = html_doc.find("body")
        if bread_text is not None:
            try:
                backup = copy.deepcopy(converter)
                converter.add_html_to_document(str(bread_text), docx)
                counters["body"] = counters["body"] + 1
                print(html + ": body", len(str(bread_text)) )
            except:
                converter = backup
                print(html + ": EXCEPTION/body", len(str(bread_text)) )
            continue
            

    docx.save(output_file)
print(counters)
