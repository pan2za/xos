#! /usr/bin/env python

import os
import site
from distutils.core import setup

CHAMELEON_DIR='xosapi/chameleon'

if not os.path.exists(CHAMELEON_DIR):
    raise Exception("%s does not exist!" % CHAMELEON_DIR)

if not os.path.exists(os.path.join(CHAMELEON_DIR, "protos/schema_pb2.py")):
    raise Exception("Please make the chameleon protos")

setup(name='xosapi',
      description='XOS api client',
      package_dir= {'xosapi.chameleon': CHAMELEON_DIR},
      packages=['xosapi.chameleon.grpc_client',
                'xosapi.chameleon.protos',
                'xosapi.chameleon.protos.third_party',
                'xosapi.chameleon.protos.third_party.google',
                'xosapi.chameleon.protos.third_party.google.api',
                'xosapi.chameleon.utils',
                'xosapi.chameleon.protoc_plugins',
                'xosapi',
                'xosapi.convenience'],
      py_modules= ['xosapi.chameleon.__init__'],
      include_package_data=True,
      package_data = {'xosapi.chameleon.protos.third_party.google.api': ['*.proto'],
                      'xosapi.chameleon.protos': ['*.proto'],
                      'xosapi.chameleon.protoc_plugins': ['*.desc']},
      scripts = ['xossh'],
     )

# Chameleon needs the following files set as executable
for dir in site.getsitepackages():
   fn = os.path.join(dir, "xosapi/chameleon/protoc_plugins/gw_gen.py")
   if os.path.exists(fn):
       os.chmod(fn, 0777)
   fn = os.path.join(dir, "xosapi/chameleon/protoc_plugins/swagger_gen.py")
   if os.path.exists(fn):
       os.chmod(fn, 0777)


"""
from twisted.internet import reactor
from xosapi.xos_grpc_client import InsecureClient
client = InsecureClient(endpoint="xos-core.cord.lab:50055")
client.start()
reactor.run()
"""


