import csv
from models import ProtoAttribute
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template.context import RequestContext

def read_from_csv(csv_file):
    csv_reader = csv.DictReader(csv_file)
    attributes = {}

    for row in csv_reader:
        p = row.pop("Page").decode("utf-8")
        d = dict((k.decode("utf-8"), v.decode("utf-8")) for k,v in row.items())
        for k, v in d.items():
            if v != '':
                proto_attr = attributes.get(k, ProtoAttribute(k))
                attributes[k] = proto_attr
                proto_attr.add_value_for_page(p, v)
    return attributes


def start(request):
    return render_to_response('import_info/start.html',
                              context_instance=RequestContext(request))


def upload_csv(request):
    if request.method != 'POST' or 'csv_file' not in request.FILES:
        return HttpResponse('Upload a CSV file via POST method')

    csv = request.FILES['csv_file']
    attributes = read_from_csv(csv)
    c = { 'attributes': sorted([a for a in attributes.values()],
                               key=lambda a: a.count,
                               reverse=True)
         }

    return render_to_response('import_info/overview.html', c,
                              context_instance=RequestContext(request))


def tag_pages(request):
    if request.method != 'POST':
        return HttpResponse('Use POST method')

    pages = request.POST['pages']
    tag = request.POST['tag']
    count = 0

    return HttpResponse('Tagged %d pages with "%s"' % (count, tag))


def import_attribute(request):
    if request.method != 'POST':
        return HttpResponse('Use POST method')

    a = ProtoAttribute(request.POST['original_name'])
    pages = request.POST.getlist('page')
    values = request.POST.getlist('value')
    for p, v in zip(pages, values):
        a.add_value_for_page(p, v)
    c = { 'attribute': a
         }

    return render_to_response('import_info/import_attribute.html', c,
                              context_instance=RequestContext(request))