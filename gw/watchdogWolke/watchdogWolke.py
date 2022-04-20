#!/usr/bin/python3

"""
  Service Communication Manager
  This Python Script Damon do the below stuff:
  Check the communication 3G
  Check and Control the Status modem
  Check the status application
  Check the status info and create a json file
  The Documentation of each class it's inside of them
"""
from __future__ import generators

import stat
from time import sleep
import abc
import os
import sys

if sys.platform == 'linux2' or sys.platform == 'linux':
    import gpiozero
from procname import ProcName
import logging
import json
import time
import atexit
import signal
import subprocess
import ctypes
import re
import psutil
import datetime

import pathlib

# Directory
path = dict()
path['config'] = '/home/pi/watchdogWolke/config.json'
path['appinfo'] = '/tmp/appinfo.json'
path['log'] = '/tmp/watchdogWolke.log'
path['pid'] = '/tmp/watchdogWolke.pid'
path['pwd'] = '/home/pi/watchdogWolke/watchdogWolke.py'

# create logger with 'spam_application'
logger = logging.getLogger(path['pwd'])
logger.setLevel(logging.DEBUG)
 

def loggerhandler(pathlogger):
    # create file handler which logs even debug messages
    fh = logging.FileHandler(pathlogger)
    ch = logging.StreamHandler()
    fh.setLevel(logging.INFO)
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(funcName)s:%(lineno)d - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

class Daemon:
    """A generic daemon class.

    Usage: subclass the daemon class and override the run() method."""

    def __init__(self, pidfile):
        self.pidfile = pidfile

    def daemonize(self):
        """Deamonize class. UNIX double fork mechanism."""

        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('fork #1 failed: {0}\n'.format(err))
            sys.exit(1)

        # decouple from parent environment
        os.chdir('/')
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('fork #2 failed: {0}\n'.format(err))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(os.devnull, 'r')
        so = open(os.devnull, 'a+')
        se = open(os.devnull, 'a+')

        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)

        pid = str(os.getpid())
        with open(self.pidfile, 'w+') as f:
            f.write(pid + '\n')

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """Start the daemon."""

        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile, 'r') as pf:

                pid = int(pf.read().strip())
        except (IOError, ValueError):
            pid = None

        if pid:
            check = self.check_pid(pid)
            if check:
                logger.error("pidfile %s already exist. Daemon already running?\n" % self.pidfile)
                sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """Stop the daemon."""

        # Get the pid from the pidfile
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
                logger.debug("pid: %d" % pid)
        except IOError:
            pid = None

        if not pid:
            logger.error("pidfile %s does not exist. Daemon not running?\n" % self.pidfile)
            return  # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            e = str(err.args)
            if e.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                logger.error(str(err.args))
                sys.exit(1)

    def restart(self):
        """Restart the daemon."""
        self.stop()
        self.start()

    def run(self):
        """You should override this method whit you subclass Daemon.

        It will be called after the process has been daemonized by
        start() or restart()."""

    @staticmethod
    def check_pid(pid):
        """ Check For the existence of a unix pid. """
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True


class MyDaemon(Daemon):
    """override method subclass Daemon."""

    def run(self):
        builder = ConcreteBuilder()
        logger.info("Building RTU")
        director = Director()
        logger.info("director")
        director.setBuilder(builder)
        logger.info("set builder")
        self.rtu = director.getProduct()
        logger.info("rtu")
        self.timeout = int(self.rtu.conf.data["ScanTime"])
        logger.info("Time Scan %s" % self.timeout)

        while True:
            try:
                self.ScanTask()
                self.PersistenceTask()
                logger.info("Timeout wait...{0}".format(self.timeout))
                time.sleep(int(self.timeout))
                
            except Exception as e:
                # THis will catch any exception!
                logger.error("Something terrible happened %s" % e)
                sys.exit(2)

    def ScanTask(self):
        i = 0
        while i < len(self.rtu.conf.data["Aplication"]):
            try:
                if self.rtu.conf.data["AppScan"] == "1":
                    logger.info("check if the app is running")
                    # the next stuff by do is check if the app still running
                    app = self.rtu.wd.getstatusapp(i)
                    print(json.dumps(self.rtu.conf.data))

                    # if the app is stop
                    if not app:
                        if self.rtu.wd.start_app_count > 10:
                            os.system("sudo reboot")
                        else:
                            logger.info("app is stop")
                            self.rtu.wd.startapp(i)
                else:
                    logger.info("app check disabled")

            except Exception as e:
                logger.error("Error in ScanTask %s" % e)
            i += 1
            
    def PersistenceTask(self):
        try:
            logger.info("veryfy json")
            if self.rtu.configmonitor.verify():
                self.timeout = self.rtu.conf.data["ScanTime"]
                logger.info("Time Scan %s" % self.timeout)
                logger.info(json.dumps(self.rtu.conf.data))
        except Exception as e:
            logger.error("Error in PersistenceTask %s" % e)

class Watchdogapp(object):
    """
    Brief: This class monitoring a app declared at config.json

    Usage:
        getstatusapp: this method check if the app is runing and return True if it's ok!
    """

    def __init__(self):
        self.conf = Config.getInstance()
        self.conf.load()
        logger.info("Create watch dog for app {0}".format(self.conf.data["Aplication"]))
        self.proc_name = self.conf.data["Aplication"]
        self.proc_path = self.conf.data["AppPath"]
        self.statusapp = ''
        self.data = dict()
        self.start_app_count = 0
        return

    def getstatusapp(self, i):
        # Ask by the process
        try:
            for proc in psutil.process_iter():
                pid = psutil.Process(proc.pid)  # Get the process info using PID
                pname = proc.name()  # Here is the process name

                if pname == self.proc_name[i]:
                    #logger.info("Process ok!")
                    self.statusapp = 'Proceso ' + pname + ' Ok'
                    logger.info(pid)
                    self.createjson(i)
                    self.writejson(i)
                    return True

            # if not appear the process
            logger.error("Process shut down")
            self.statusapp = 'Proceso suspendido'
            self.createjson(i)
            self.writejson(i)
        except Exception as e:
            # THis will catch any exception!
            self.statusapp = 'Problema monitor'
            self.createjson(i)
            self.writejson(i)
            logger.error("Something terrible happened %s" % e)
        return False

    def createjson(self, i):
        self.data["StatusApp-"+ self.proc_name[i]] = self.statusapp
        self.str = json.dumps(self.data)
        self.writejson(i)
        return

    def writejson(self, i):
        fjson = open(path['appinfo'], "w+")
        fjson.write(self.str)
        fjson.close()
        return

    def startapp(self, i):
        logger.info("Starting {0}".format(self.proc_name[i]))
        logger.info("Path {0}".format(self.proc_path[i]))
        os.chdir(self.proc_path[i])
        logger.info(pathlib.Path().resolve())
        os.system("%s &" % self.proc_name[i])
        self.statusapp = 'Iniciando proceso'
        self.createjson(i)
        self.writejson(i)
        self.start_app_count += 1
        return

class Config(object):
    """
    Brief:
        Singleton Class.
    Usage:
        for data persistence storaged at config.json
    """
    # Here will be the instance stored.
    __instance = None

    def load(self):
        self.data = PersistenceJson.load(path['config'])
        return self.data

    def save(self):
        PersistenceJson.save(path['config'], self.data)
        return

    @staticmethod
    def getInstance():
        """ Static access method. """
        if Config.__instance == None:
            logger.info("New instance Config()")
            Config()
            Config.__instance.load()
        return Config.__instance

    def __init__(self):
        logger.info("Creating singleton")
        """ Virtually private constructor. """
        self.data = dict()
        if Config.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            Config.__instance = self

class File(object):
    """
    Brief:

    Usage:

    """

    def __init__(self, file):
        logger.info("Create file object")
        self._cached_stamp = 0
        self.file = file

    def verify(self):
        stamp = os.stat(self.file).st_mtime
        if stamp != self._cached_stamp:
            self._cached_stamp = stamp
            logger.info("Has a file change")
            return True
        else:
            logger.info("No change file")
            return False

    @staticmethod
    def parsefilecmp(file, str1):
        logger.info("file: %s" % file)
        logger.info("strl: %s" % str1)
        try:
            with open(file, 'rt') as file1:
                read_data = file1.read()
                if str1 in read_data:
                    logger.debug("read_data: %s" % read_data)
                    return True
        except IOError:
            logger.error("Can't open file %s" % file)

        return False

    def rplcinfile(self, file, oldstr1, str):
        logger.info("file: %s" % file)
        logger.info("oldstr1: %s" % oldstr1)
        logger.info("strl: %s" % str)
        if not oldstr1:
            return False
        try:
            with open(file, 'r+') as file1:
                read_data = file1.read()
                logger.info("read_data: %s \n" % read_data)
                file1.close()
                lines = read_data.split('\n')
                logger.info("str %s" % str)
                logger.info("old str %s" % oldstr1)
                for line in lines:
                    logger.info("line %s" % line)
                    if line in oldstr1:
                        data = read_data.replace(oldstr1, str)
                        with open(file, "w") as f:
                            logger.info("data: %s\n" % data)
                            f.write(data)
                            f.close()
                        return True

        except IOError:
            logger.error("Can't open file %s" % file)
            sys.exit(2);
        return False

class LoadingBar(object):
    """
    Brief: This class create a load bar in command prompt

    Usage:
        just invoke start method and pass a integer with the seconds to wait
    """

    def __init__(self):
        return

    @staticmethod
    def start(seconds):
        for i in range(0, seconds):
            percent = float(i) / seconds
            hashes = '#' * int(round(percent * seconds))
            spaces = ' ' * (seconds - len(hashes))
            logger.info("\rStarting Daemon Percent: [{0}] {1}%".format(hashes + spaces, int(round(percent * 100))))
            time.sleep(1)

class Persistence(metaclass=abc.ABCMeta):

    def __init__(self):
        self.data = None
        return

    def factory(type):
        if type == "Json":
            return PersistenceJson()
        assert 0, "Bad shape creation: " + type

    factory = staticmethod(factory)

    @abc.abstractmethod
    def load(self, path):
        pass

    @abc.abstractmethod
    def save(self, path):
        pass

class PersistenceJson(Persistence):
    """
    Brief:

    Usage:

    """

    @staticmethod
    def load(path):
        try:
            with open(path) as f:
                data = json.load(f)
                f.close()
                return data
        except IOError as e:
            logger.error("I/O error({0}): {1}".format(e.errno, e.strerror))
        except ValueError:
            logger.error("Could not convert data to an integer.")
        except:
            logger.error("Unexpected error:", sys.exc_info()[0])
            raise
        return

    @staticmethod
    def save(path, data):
        try:
            fjson = open(path, "w")
            fjson.write(json.dumps(data, indent=4, sort_keys=True))
            fjson.close()
        except IOError as e:
            logger.error("I/O error({0}): {1}".format(e.errno, e.strerror))
        except ValueError:
            logger.error("Could not convert data to an integer.")
        except:
            logger.error("Unexpected error:", sys.exc_info()[0])
            raise
        return

class Director(object):
    """ Controls the construction process.
    Director has a builder associated with him. Director then
    delegates building of the smaller parts to the builder and
    assembles them together.
    """

    __builder = None

    def setBuilder(self, builder):
        self.__builder = builder

    # The algorithm for assembling a car
    def getProduct(self):
        rtu = RTU()

        conf = self.__builder.getConf()
        rtu.setConf(conf)

        wd = self.__builder.getWd()
        rtu.setWd(wd)

        monitor = self.__builder.getConfigMonitor()
        rtu.setConfigMonitor(monitor)

        return rtu

# The whole product
class RTU(object):
    """ The final product.
    """

    def __init__(self):
        self.conf = None
        self.wd = None
        self.configmonitor = None

    def setConf(self, conf):
        self.conf = conf

    def setWd(self, wd):
        self.wd = wd

    def setConfigMonitor(self, monitor):
        self.configmonitor = monitor

class Builder(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def getConf(self):
        pass

    @abc.abstractmethod
    def getWd(self):
        pass
    
    @abc.abstractmethod
    def getConfigMonitor(self):
        pass

class ConcreteBuilder(Builder):
    """ Concrete Builder implementation.
    """

    def getConf(self):
        cnf = Config.getInstance()
        cnf.load()
        return cnf

    def getWd(self):
        wd = Watchdogapp()
        return wd
    
    def getConfigMonitor(self):
        monitor = File(str(path['config']))
        return monitor

if __name__ == "__main__":

    loggerhandler(path['log'])
    logger.info("Iniciando watchdogWolke")

    # Change process name
    ProcName.set(b'watchdogWolke.py')
    try:
        with open(path['config']) as f:
            data = json.load(f)
    except IOError:
        logger.error("Can't open config.json")
        sys.exit(2)

    # load config data
    conf = Config.getInstance()
    conf.load()

    daemon = MyDaemon(path['pid'])
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            # wait 10 seconds before start daemon
            LoadingBar.start(10)
            logger.info(json.dumps(conf.data))
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print("Unknown command")
            print("usage: %s start|stop|restart" % sys.argv[0])
            sys.exit(2)
        sys.exit(0)
    elif len(sys.argv) == 1:
        # wait 10 seconds before start daemon
        LoadingBar.start(10)
        logger.info(json.dumps(conf.data))
        daemon.start()
    else:
        print("usage: %s start|stop|restart" % sys.argv[0])
    sys.exit(0)
    
