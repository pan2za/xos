#!/usr/bin/env python
import os
import argparse
import sys

sys.path.append('/opt/xos')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xos.settings")
from xos.config import Config, DEFAULT_CONFIG_FN
from xos.logger import Logger, logging, logger
import time

from synchronizers.new_base.modelaccessor import *
from synchronizers.new_base.backend import Backend

config = Config()

logger = Logger(level=logging.INFO)

# after http://www.erlenstar.demon.co.uk/unix/faq_2.html
def daemon():
    """Daemonize the current process."""
    if os.fork() != 0: os._exit(0)
    os.setsid()
    if os.fork() != 0: os._exit(0)
    os.umask(0)
    devnull = os.open(os.devnull, os.O_RDWR)
    os.dup2(devnull, 0)
    # xxx fixme - this is just to make sure that nothing gets stupidly lost - should use devnull
    logdir=os.path.dirname(config.observer_logfile)
    # when installed in standalone we might not have httpd installed
    if not os.path.isdir(logdir): os.mkdir(logdir)
    crashlog = os.open('%s'%config.observer_logfile, os.O_RDWR | os.O_APPEND | os.O_CREAT, 0644)
    os.dup2(crashlog, 1)
    os.dup2(crashlog, 2)

    if hasattr(config, "observer_pidfile"):
        pidfile = config.get("observer_pidfile")
    else:
        pidfile = "/var/run/xosobserver.pid"
    try:
        file(pidfile,"w").write(str(os.getpid()))
    except:
        print "failed to create pidfile %s" % pidfile

def main():
    # Generate command line parser
    parser = argparse.ArgumentParser(usage='%(prog)s [options]')
    parser.add_argument('-d', '--daemon', dest='daemon', action='store_true', default=False,
                        help='Run as daemon.')
    # smbaker: util/config.py parses sys.argv[] directly to get config file name; include the option here to avoid
    #   throwing unrecognized argument exceptions
    parser.add_argument('-C', '--config', dest='config_file', action='store', default=DEFAULT_CONFIG_FN,
                        help='Name of config file.')
    args = parser.parse_args()

    if args.daemon: daemon()

    models_active = False
    wait = False
    while not models_active:
        try:
            _ = Instance.objects.first()
            _ = NetworkTemplate.objects.first()
            models_active = True
        except Exception,e:
            logger.info(str(e))
            logger.info('Waiting for data model to come up before starting...')
            time.sleep(10)
            wait = True

    if (wait):
        time.sleep(60) # Safety factor, seeing that we stumbled waiting for the data model to come up.
    backend = Backend()
    backend.run()

if __name__ == '__main__':

    main()
