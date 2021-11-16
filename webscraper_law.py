import datetime
import socket
import urllib
import urllib.request as rq
from lxml import etree
import io
import json
import time
import os
import random
import sys


def get_results(query_url, parser):
    # delay request
    rand_delay = random.randint(0, 5)/1000
    time.sleep(0.005+rand_delay)
    with rq.urlopen(query_url) as response:
        s = response.read().decode('utf-8')
    tree = etree.parse(io.StringIO(s), parser)
    results = tree.xpath(
        ".//xmlns:span[contains(@class,'nativeDocumentLinkCell')]",
        namespaces={'xmlns': 'http://www.w3.org/1999/xhtml'})
    return results


def get_document(result, main_url, parser, extract_paragraphs=False):
    # result[0] = web site, result[1] = pdf, result[2] = rtf
    document_url = result[0].get('href')
    # delay request
    rand_delay = random.randint(0, 5)/1000
    time.sleep(0.005+rand_delay)
    doc = {
        'file': main_url + document_url,
        "time": datetime.datetime.now().isoformat()}

    try:
        with rq.urlopen(main_url+document_url, timeout=5) as response:
            d = response.read().decode('utf-8')
    except (socket.timeout, urllib.error.URLError) as err:
        doc['error'] = str(err)
        print(f'url error: {doc}')
        return doc

    tree = etree.parse(io.StringIO(d), parser)
    body_elements = tree.xpath(
        ".//xmlns:body", namespaces={'xmlns': 'http://www.w3.org/1999/xhtml'})
    assert len(body_elements) == 1

    try:
        text, entities, urls = get_text_from_html_body(body_elements[0])
        doc.update({'text': text, 'entities': entities, 'urls': urls})
    except ValueError as err:
        doc['error'] = str(err)
        print(f'parsing error: {doc}')

    return doc


def traverse(element, skip_tags=()):
    for e in element:
        yield e
        if e.tag not in skip_tags:
            yield from traverse(e, skip_tags=skip_tags)


def extract_element_text(element):
    text = ""
    if element.text is not None:
        text += element.text
    for child_element in element:
        text += extract_element_text(child_element)
    if element.tail is not None:
        text += element.tail
    return text


def get_text_from_html_body(body):
    entities = []
    urls = {}
    text = {"comments": []}
    curr_section = text["no_header"] = []
    curr_h1 = None
    curr_h2 = None
    skip_tags = ('{http://www.w3.org/1999/xhtml}table',)
    for e in traverse(body, skip_tags=skip_tags):
        if e.tag in skip_tags:
            curr_section.append("SKIPPED")
            continue
        if e.text is None:
            continue
        if e.tag.endswith('h1'):
            curr_h1 = e.text
            curr_h2 = None
            curr_h3 = None
            curr_section = text[curr_h1] = []
        elif e.tag.endswith('h2'):
            curr_h2 = e.text
            curr_h3 = None
            curr_section = text[f'{curr_h1}:{curr_h2}'] = []
        elif e.tag.endswith('h3'):
            curr_h3 = e.text
            curr_section = text[f'{curr_h1}:{curr_h2}:{curr_h3}'] = []
        elif e.tag.endswith('p'):
            curr_section.append(extract_element_text(e))
        elif e.tag.endswith('span'):
            entities.append(e.text)
        elif e.tag.endswith('a'):
            urls[e.text] = e.get('href')
        elif e.tag.endswith('s'):
            curr_section.append(extract_element_text(e))
            text['comments'].append('ignored <s>')
        else:
            t = e.text.strip()
            if t:
                raise ValueError(f'unexpected tag with text: {e.tag}: {t}')

    if len(text['no_header']) == 0:
        del text['no_header']

    return text, entities, urls


def doc2file(document_dict, file_path):
    """
    Writes one JSON file per line.
    """
    json_string = json.dumps(document_dict)
    with io.open(file_path, 'a', encoding='utf-8') as fp:
        fp.write(json_string+'\n')


def is_duplicate(results, old_results):
    return sum([1 for x, y in zip(results, old_results) if x == y]) != 0


def get_processed_count(out_file):
    with io.open(out_file, 'r', encoding='utf-8') as fp:
        return int(fp.readline())


def set_processed_count(out_file, count):
    fh = open(out_file, "r+b")
    fh.seek(0)
    count_string = "{:08d}".format(count)
    sb = bytes(count_string, encoding='utf-8')
    fh.write(sb)
    fh.close()


def main():
    parser = etree.XMLParser(recover=True)
    # out_file = "../CODE_OUT/ris.data"
    out_file = sys.argv[1]
    main_url = "https://www.ris.bka.gv.at"
    path_url = "/Ergebnis.wxe?Abfrage=Gesamtabfrage&ResultPageSize=100&Sort=2%7cAsc&Position="  # noqa
    has_new_results = True
    # old_results = None
    file_count = 0

    # allows the RIS crawler to continue if stopped
    if os.path.exists(out_file):
        position = get_processed_count(out_file)
    else:
        position = 1
        fp = io.open(out_file, 'w', encoding='utf-8')
        fp.write("{:08d}".format(position)+'\n')
        fp.close()

    start_time = time.time()
    while has_new_results:
        query_url = main_url + path_url + str(position)
        results = get_results(query_url, parser)
        # doc_count = len(results)
        for result in results:
            file_count += 1
            elapsed = time.time() - start_time
            print(
                'Page:', position, 'File:', file_count, 'F/s:',
                "{:.1f}".format(file_count/elapsed), len(result), end='\r')
            if len(result) != 3:
                continue

            document_dict = get_document(result, main_url, parser)
            doc2file(document_dict, out_file)
        # if doc_count < 100: #or is_duplicate(results, old_results):
        if position > 1716230:
            has_new_results = False
        # old_results = results
        position += 100
        set_processed_count(out_file, position)
        time.sleep(1+random.randint(0, 1000)/1000)
    print()
    print('Done')


if __name__ == "__main__":
    # execute only if run as a script
    main()
