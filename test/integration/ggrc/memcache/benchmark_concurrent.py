# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""
 Benchmark concurrent tests for checking consistency of cache on object changes

 CREATE
 GET
 PUT
 DELETE

The threads are started for simultaneous GET/PUT/DELETE operation

"""
import requests
import json
import time
from datetime import datetime
from copy import deepcopy
import threading

localhost_headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'x-requested-by': 'GGRC',
    'Cookie': 'Please enter cookie'
}

ggrcdev_headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'x-requested-by': 'GGRC',
    'Cookie': 'Please enter cookie'
}

appspot_headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'x-requested-by': 'GGRC',
    'Cookie': 'Please enter cookie'
}

create_resources = {
    'regulations': '{"regulation":{"kind":"Regulation","contact":{"id":1260,"t'
    'ype":"Person"},"title":"Benchmark Regulation","description":"Benchmark Re'
    'gulation","notes":"Benchmark Regulation CREATED","url":"","reference_url"'
    ':"","slug":"","start_date":"","end_date":"","status":null,"context":{"id"'
    ':null},"owners":[{"id":1260,"href":"/api/people/1260","type":"Person"}],"'
    'provisional_id":"provisional_6741102"}}'
}

update_resources = {
    'regulations': '{"regulation":{"kind":"Regulation","contact":{"id":1260,"h'
    'ref":"/api/people/1260","type":"Person"},"description":"Benchmark Regulat'
    'ion","object_people":[],"program_directives":[],"controls":[],"url":"","t'
    'ype":"Regulation","status":"Draft","owners":[{"id":1260,"href":"/api/peop'
    'le/1260","type":"Person"}],"scope":"","directive_controls":[],"sections":'
    '[],"selfLink":"/api/regulations/71","programs":[],"created_at":"2014-03-2'
    '0T22:09:24Z","updated_at":"2014-03-20T22:09:24Z","object_owners":[{"statu'
    's":"Draft","modified_by":{"href":"/api/people/1260","id":1260,"type":"Per'
    'son"},"id":1083,"selfLink":"/api/object_owners/1083","person":{"href":"/a'
    'pi/people/1260","id":1260,"type":"Person"},"context":null,"created_at":"2'
    '014-03-20T22:09:24","updated_at":"2014-03-20T22:09:24","type":"ObjectOwne'
    'r","ownable":{"href":"/api/regulations/71","id":71,"type":"Regulation"}}]'
    ',"reference_url":"","organization":"","documents":[],"title":"Benchmark R'
    'egulation","objectives":[],"modified_by":{"id":1260,"href":"/api/people/1'
    '260","type":"Person"},"people":[],"id":71,"notes":"Benchmark Regulation U'
    'PDATED 1","version":"","viewLink":"/regulations/71","object_documents":[]'
    ',"related_sources":[],"related_destinations":[], "slug": "REGULATION-101"'
    ', "start_date":"","end_date":"","context":{"id":null}}}'
}

update_resources2 = {
    'regulations': '{"regulation":{"kind":"Regulation","contact":{"id":1260,"h'
    'ref":"/api/people/1260","type":"Person"},"description":"Benchmark Regulat'
    'ion","object_people":[],"program_directives":[],"controls":[],"url":"","t'
    'ype":"Regulation","status":"Draft","owners":[{"id":1260,"href":"/api/peop'
    'le/1260","type":"Person"}],"scope":"","directive_controls":[],"sections":'
    '[],"selfLink":"/api/regulations/71","programs":[],"created_at":"2014-03-2'
    '0T22:09:24Z","updated_at":"2014-03-20T22:09:24Z","object_owners":[{"statu'
    's":"Draft","modified_by":{"href":"/api/people/1260","id":1260,"type":"Per'
    'son"},"id":1083,"selfLink":"/api/object_owners/1083","person":{"href":"/a'
    'pi/people/1260","id":1260,"type":"Person"},"context":null,"created_at":"2'
    '014-03-20T22:09:24","updated_at":"2014-03-20T22:09:24","type":"ObjectOwne'
    'r","ownable":{"href":"/api/regulations/71","id":71,"type":"Regulation"}}]'
    ',"reference_url":"","organization":"","documents":[],"title":"Benchmark R'
    'egulation","objectives":[],"modified_by":{"id":1260,"href":"/api/people/1'
    '260","type":"Person"},"people":[],"id":71,"notes":"Benchmark Regulation U'
    'PDATED 2","version":"","viewLink":"/regulations/71","object_documents":[]'
    ',"related_sources":[],"related_destinations":[],"slug": "REGULATION-101",'
    '"start_date":"","end_date":"","context":{"id":null}}}'
}

mapping_resource = {
    'regulations': 'regulation'
}


class TestGetThread(threading.Thread):

  def __init__(self, name, data, loop_cnt):
    super(TestGetThread, self).__init__()
    self.name = name
    self.data = data
    self.starttime = None
    self.endtime = None
    self.loop_cnt = loop_cnt

  def run(self):
    self.starttime = datetime.now()
    for cnt in range(self.loop_cnt):
      # print "Running GET Thread: " + self.name + " Iteration " + str(cnt+1)
      if not cnt % 100:
        print "GET Iteration " + str(cnt + 1) + " of " + str(self.loop_cnt)
      benchmark_get(self.data, 1, "Concurrency Test")
    self.endtime = datetime.now()


class TestPutThread(threading.Thread):

  def __init__(self, name, put_data, get_data, loop_cnt):
    super(TestPutThread, self).__init__()
    self.name = name
    self.get_data = get_data
    self.put_data = put_data
    self.starttime = None
    self.endtime = None
    self.loop_cnt = loop_cnt

  def run(self):
    self.starttime = datetime.now()
    for cnt in range(self.loop_cnt):
      # print "Running PUT/GET Thread: " + self.name + " Iteration " +
      # str(cnt+1)
      if not cnt % 100:
        print "PUT/GET Iteration " + str(cnt + 1) + " of " + str(self.loop_cnt)
      for resource, payload in self.put_data.items():
        json_payload = json.loads(payload)
        updated_notes = "Benchmark Regulation UPDATED#" + str(cnt + 1)
        json_payload[mapping_resource[resource]]['notes'] = updated_notes
        self.put_data[resource] = json.dumps(json_payload)
      benchmark_update(self.put_data, self.get_data, 1)
      benchmark_get(self.get_data, 1, "Concurrency GET Test", updated_notes)
    self.endtime = datetime.now()


def invoke_url(op, prefix, host, url, payload, headers, count):
  response = None
  for cnt in range(count):
    testurl = prefix + "://" + host + url
    if op == 'post':
      response = requests.post(testurl, data=payload, headers=headers)
    elif op == 'get':
      response = requests.get(testurl, headers=headers, params=payload)
    elif op == 'put':
      response = requests.put(testurl, data=payload, headers=headers)
    else:
      response = requests.delete(testurl, headers=headers)
    time.sleep(1)
  return response

localhost_url = "localhost:8080"
ggrcdev_url = "ggrc-dev.googleplex.com"
appspot_url = "grc-audit.appspot.com"

# headers=appspot_headers
# targethost=appspot_url
targethost = localhost_url
headers = localhost_headers
num_iterations = 1
etag = 10023
# prefix="https"
prefix = "http"


def benchmark_delete(resource_data, num_iterations):
  payload = None
  for resource, data in resource_data.items():
    # print "Test DELETE for resource: " + resource + " with ids " +
    # str(data['ids'])
    testurl = "/api/" + resource
    ids = data['ids']
    etags = data['etag']
    last_modified_items = data['last-modified']
    for cnt in range(len(ids)):
      id = ids[cnt]
      delete_headers = deepcopy(headers)
      delete_headers['If-Match'] = etags[cnt]
      delete_headers['If-Unmodified-Since'] = last_modified_items[cnt]
      response = invoke_url('delete', prefix, targethost, testurl +
                            "/" + str(id), payload, delete_headers,
                            num_iterations)
      if response.status_code != 200:
        print "DELETE Failed: " + str(response.status_code)


def benchmark_get(resource_data, num_iterations, name, verify_notes=None):
  for resource, data in resource_data.items():
    # print "Test GET for owner: " + name + " resource: " + resource + " with
    # ids " + str(data['ids'])
    testurl = "/api/" + resource
    ids = ""
    idslen = len(data['ids'])
    cnt = 0
    for id in data['ids']:
      cnt = cnt + 1
      if cnt == idslen:
        ids = ids + str(id)
      else:
        ids = ids + str(id) + ","
    payload = {'id__in': ids, '_': str(etag)}
    response = invoke_url('get', prefix, targethost,
                          testurl, payload, headers, num_iterations)
    if response.status_code != 200:
      print "GET Failed: " + str(response.status_code)
    else:
      json_response = json.loads(response.text)
      responses = json_response[resource + '_collection'][resource]
      for item in responses:
        if verify_notes is not None:
          # print "UPDATE Notes: " + verify_notes
          if item["notes"] != verify_notes:
            print "[WARN]: UPDATE Notes: " + verify_notes + "GET Notes: " + \
                item["notes"]


def benchmark_create(resource_data, resource_cnt, num_iterations):
  resource_dict = {}
  for resource, payload in resource_data.items():
    testurl = "/api/" + resource
    resource_dict[resource] = {}
    resource_dict[resource]['ids'] = []
    resource_dict[resource]['etag'] = []
    resource_dict[resource]['last-modified'] = []
    resource_dict[resource]['json-response'] = []
    for cnt in range(resource_cnt):
      response = invoke_url('post', prefix, targethost,
                            testurl, payload, headers, num_iterations)
      if response.status_code == 201:
        json_response = json.loads(response.text)
        for key, value in json_response.items():
          resource_dict[resource]['ids'].append(value['id'])
          resource_dict[resource]['etag'].append(response.headers['etag'])
          resource_dict[resource][
              'last-modified'].append(response.headers['last-modified'])
          # print "Test CREATE for resource: " + resource + " with id " +
          # str(value[u'id'])
      else:
        print "CREATE Failed: " + str(response.status_code)
        return None
  return resource_dict


def benchmark_update(resource_data, resource_dict, num_iterations):
  for resource, payload in resource_data.items():
    testurl = "/api/" + resource
    ids = resource_dict[resource]['ids']
    # print "Test UPDATE for resource: " + resource + " with ids " + str(ids)
    etags = resource_dict[resource]['etag']
    last_modified_items = resource_dict[resource]['last-modified']
    for cnt in range(len(ids)):
      # print etags
      # print last_modified_items
      id = ids[cnt]
      update_headers = deepcopy(headers)
      update_headers['If-Match'] = etags[cnt]
      update_headers['If-Unmodified-Since'] = str(last_modified_items[cnt])
      response = invoke_url('put', prefix, targethost, testurl +
                            '/' + str(id), payload, update_headers,
                            num_iterations)
      if response.status_code != 200:
        print "UPDATE Failed: " + str(response.status_code)
      else:
        resource_dict[resource]['etag'][cnt] = response.headers['etag']
        resource_dict[resource][
            'last-modified'][cnt] = response.headers['last-modified']
        # print response.headers['etag']
        # print response.headers['last-modified']


def run_singlethreaded_tests():
  print "Running single threaded benchmark tests create, GET, PUT, GET, DELETE"
  resource_dict = benchmark_create(create_resources, 1, 1)
  if resource_dict is not None:
    benchmark_get(resource_dict, 1, "Single Threaded GET Test")
    benchmark_update(update_resources, resource_dict, 1)
    benchmark_get(resource_dict, 1, "Single Threaded GET Test")
    benchmark_update(update_resources2, resource_dict, 1)
    benchmark_get(resource_dict, 1, "Single Threaded GET Test")
    benchmark_delete(resource_dict, 1)
  else:
    print "ERROR: Unable to run benchmark tests"


def run_concurrent_tests(loop_cnt):
  print "Running Benchmark Concurrent tests PUT/GET and GET..."
  resource_dict = benchmark_create(create_resources, 1, 1)
  if resource_dict is not None:
    get_threads = []
    put_threads = []
    for cnt in range(1):
      get_threads.append(TestGetThread(
          "GET Thread" + str(cnt + 1), resource_dict, loop_cnt + 20))
      put_threads.append(TestPutThread(
          "PUT Thread" + str(cnt + 1), update_resources, resource_dict,
          loop_cnt))
    for cnt in range(1):
      get_threads[cnt].start()
      put_threads[cnt].start()
    for cnt in range(1):
      get_threads[cnt].join()
      put_threads[cnt].join()
      benchmark_delete(resource_dict, 1)
    for cnt in range(1):
      print get_threads[cnt].name + " starttime: " + str(
          get_threads[cnt].starttime) + " endtime: " + str(
          get_threads[cnt].endtime)
      print put_threads[cnt].name + " starttime: " + str(
          put_threads[cnt].starttime) + " endtime: " + str(
          put_threads[cnt].endtime)

if __name__ == '__main__':
  run_singlethreaded_tests()
  run_concurrent_tests(1000)
