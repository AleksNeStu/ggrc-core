# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
 Benchmark load tests for stubs and collection

 The stubs for resources in benchmark such as Regulations are retrieved and it
 is followed by a collection get. The batch size for the collection get
 (batch_size) and number of test iterations (num_iterations) are configurable.
 The iterations of test allows to get consistent time for getting stubs and
 collection in GGRC

 The memcache mechanism be turned off in settings (default.py) and this script
 can be rerun to compare with/without cache

 Prerequisite: The following changes are required to run this script
   1. Cookie in localhost_headers, ggrcdev_headers, appspot_headers
   2. targethost - Points to localhost, appspot, ggrcdev
   3. headers - Points to localhost_headers, appspot_headers, ggrcdev_headers
   4. prefix - http for localhost, https for others

"""
import urllib2
import json
from datetime import datetime

localhost_headers = {
    'Accept': 'application/json',
    'x-requested-by': 'GGRC',
    'Cookie': 'Please enter cookie in headers'
}

ggrcdev_headers = {
    'Accept': 'application/json',
    'x-requested-by': 'GGRC',
    'Cookie': 'Please enter cookie in headers'
}

appspot_headers = {
    'Accept': 'application/json',
    'x-requested-by': 'GGRC',
    'Cookie': 'Please enter cookie in headers'
}

benchmark_resources = ["programs", "regulations", "controls", "people"]

localhost = "localhost:8080"
ggrcdev = "ggrc-dev.googleplex.com"
appspot = "grc-audit.appspot.com"
etag = 1000123


def get_stubs_url():
  ret = {}
  for entry in benchmark_resources:
    target_url = "/api/" + entry + "?__stubs_only=true"
    ret[entry] = target_url
  return ret


def run_benchmark_tests(prefix, targethost, num_iterations, headers,  # noqa
                        batchsize):
  resource_collection = {}
  print "Running benchmark tests for stubs"
  for resource, target_url in get_stubs_url().items():
    resource_collection[resource] = []
    print "Running benchmark tests for stubs, resource: {} url: {}".format(
        resource,
        target_url
    )
    result = invoke_url(prefix, targethost, target_url,
                        headers, etag, num_iterations)
    decoded_result = json.loads(result)
    if not isinstance(decoded_result, dict):
      print "ERROR: result from test: " + result
      break
    for key, data in decoded_result.items():
      for key, value in decoded_result[key].items():
        if key == resource:
          for item in value:
            id_ = item[u'id']
            resource_collection[resource].append(id_)

  print "Running benchmark load tests for collection"
  for resource, objids in resource_collection.items():
    objids_len = len(objids)
    target_url = "/api/" + resource + "?id__in="
    if objids_len > batchsize:
      objids_len = batchsize
    for cnt in range(objids_len):
      itemcnt = cnt + 1
      target_url = target_url + str(objids[cnt])
      if itemcnt < objids_len:
        target_url = target_url + "%2C"
    print ("Running benchmark tests for collection, resource: {} url: {}"
           "".format(resource, target_url))
    result = invoke_url(prefix, targethost, target_url,
                        headers, etag, num_iterations)
    decoded_result = json.loads(result)
    if not isinstance(decoded_result, dict):
      print "ERROR: result from test: " + result
      break


def invoke_url(prefix, host, url, headers, start_etag, count):
  for cnt in range(count):
    etag = start_etag + cnt
    testurl = prefix + "://" + host + url + "&_=" + str(etag)
    request = urllib2.Request(testurl, None, headers)
    starttime = datetime.now()
    response = urllib2.urlopen(request).read()
    endtime = datetime.now()
    print("Test Iteration #: " + str(cnt + 1) + " time: " +
          str(endtime - starttime) + "...")
    import time
    time.sleep(1)
  return response

print "Running benchmark load tests ..."
# REVISIT: read command line arguments from this script
# targethost=appspot
# headers=appspot_headers
# prefix="https"
targethost = localhost
headers = localhost_headers
prefix = "http"
batchsize = 20
num_iterations = 10
if __name__ == '__main__':
  print "Running benchmark load tests"
  run_benchmark_tests(prefix, targethost, num_iterations, headers, batchsize)
