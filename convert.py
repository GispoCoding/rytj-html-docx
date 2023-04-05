#!/usr/bin/env python

# Convert a bunch of HTML files into a DOCX
#

import copy
import gc
from multiprocessing import Process, Lock
import os
import psutil
from re import match

from bs4 import BeautifulSoup
from docx import Document
from htmldocx import HtmlToDocx

from list import directory_list, avoid_list

# Work around Python issue 35935
# https://bugs.python.org/issue35935
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

# Where to find the HTML
base_directory = "./ry-tietomallit/docs/_site/"

# Base URL online
base_url = "https://tietomallit.ymparisto.fi/"

# Output goes here
output_dir = "./output"

# Would like you threads ? that with (actually Processes)
use_threads = True

counters = {"main_content_wrap": 0, "page_body": 0, "body": 0, "html_files": 0}

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
    html_files = list(map(lambda n: os.path.join(dir, n), html_files))

    sub_dirs = list(filter(lambda n: os.path.isdir(
        os.path.join(root, dir, n)), files))

    for sub in sub_dirs:
        html_files.extend(dig_for_html(
            root, os.path.join(dir, sub), avoid_list, True))

    return html_files


def get_mem_usage():
    return psutil.Process(os.getpid()).memory_info().rss // 1024

# Handle one directory of stuff
def convert_dir(dir):
    global counters
    # Where it all will end up
    if dir == "":
        output_file = "rytj-sisalto.docx"
    else:
        output_file = dir.translate(str.maketrans({'/': '_'})) + ".docx"

    # Start things up
    docx = Document()
    converter = HtmlToDocx()

    html_files = dig_for_html(base_directory, dir, avoid_list, False)
    # print(dir + " ", len(html_files), " HTML files found")

    lock.acquire()  # Do we need locking if using processes?
    counters["html_files"] = counters["html_files"] + len(html_files)
    lock.release()

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
            title = "[EI OTSIKKOA]"

        link = "<a href='" + base_url + html + "'>" + html + "</a>"
        converter.add_html_to_document(
            "<h2>&gt;&gt; " + title + " ( " + link + " )</h2>", docx)

        # Some of our documents have a div with id="main_content_wrap",
        # use the contents of that if present
        if (bread_text := html_doc.find("div", id="main_content_wrap")) is not None:
            try:
                converter.add_html_to_document(str(bread_text), docx)
                lock.acquire()
                counters["main_content_wrap"] = counters["main_content_wrap"] + 1
                lock.release()
                print(html + ": main_content_wrap", len(str(bread_text)))
            except:
                print(html + ": EXCEPTION/main_content_wrap",
                      len(str(bread_text)))
            continue

        # The files with a <div class="PageBody"> seem to have
        # tables with colspan and rowspan, which tickle a bug in htmldocx.
        # (see https://github.com/pqzx/html2docx/search?q=indexerror&type=issues)

        elif (bread_text := html_doc.find("div", class_="PageBody")) is not None:
            try:
                # The converter object will be unusable if we encounter an exception
                backup = copy.deepcopy(converter)
                converter.add_html_to_document(str(bread_text), docx)
                lock.acquire()
                counters["page_body"] = counters["page_body"] + 1
                lock.release()
                print(html + ": pagebody", len(str(bread_text)))
            except:
                # Roll back possible failures
                converter = backup
                print(html + ": EXCEPTION/pagebody", len(str(bread_text)))
                
        # Last resort, use the body element
        elif (bread_text := html_doc.find("body")) is not None:
            try:
                backup = copy.deepcopy(converter)
                converter.add_html_to_document(str(bread_text), docx)
                lock.acquire()
                counters["body"] = counters["body"] + 1
                lock.release()
                print(html + ": body", len(str(bread_text)))
            except:
                converter = backup
                print(html + ": EXCEPTION/body", len(str(bread_text)))

        else:
            print(html + ": NO STRATEGY")

    docx.save(os.path.join(output_dir, output_file))
    mem = get_mem_usage()
    print(f"----- Memory usage at end of {dir} processing: {mem} KB")
    del docx
    del converter
    gc.collect()


# We want to avoid recursing into subdirectories that are in
# the avoid list, so we add them here.
avoid_list.extend(directory_list)
lock = Lock()

if use_threads:
    for dir in directory_list:
        threads = []
        threads.append(Process(target=convert_dir, args=(dir,)))
        threads[-1].start()

    for t in threads:
        t.join()
else:
    for dir in directory_list:
        convert_dir(dir)


print(counters)
