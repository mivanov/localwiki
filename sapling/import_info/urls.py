from django.conf.urls.defaults import *

from views import *

urlpatterns = patterns('',
    url(r'^$', start, name='start'),
    url(r'^csv/$', upload_csv, name='upload-csv'),
    url(r'^import/$', import_attribute, name='import_attribute'),
    url(r'^tagpages/$', tag_pages, name='tag_pages'),
)
