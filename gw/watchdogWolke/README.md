# Requirements

* Python3 and psutil

```Shell
    sudo apt-get update
    sudo apt-get install python3 python3-setuptools python3-dev python3-gpiozero python3-psutil
```

* Symbolic link for Hermes and HermesWeb

```Shell
    sudo ln -s /home/pi/hermes/Hermes/usr/bin
    sudo ln -s /home/pi/web/HermesWeb/usr/bin
```

## File location

### Folder watchdogWolke

* Paste folder and content in /home/pi/

* Configuration file /home/pi/watchdogWolke/config.json:

```JSON
    {
        "Aplication": ["Hermes","HermesWeb"],
        "AppPath": ["/home/pi/hermes/","/home/pi/web/"],
        "AppScan": "1 to activate scanning : 0 to disable scanning - Default 1",
        "ScanTime": "scan intervals in sec - Default 10"
    }
```

## Test

* Run program:

```Python
    sudo python3 /home/pi/watchdogWolke/watchdogWolke.py start
```

* See process in real time (LOG)

```Shell
    tail -f /tmp/watchdogWolke.log
```

* Ejemplo de log en tiempo real

```Verilog
    2022-01-12 15:59:29,819 - ScanTask:223 - INFO - check if the app is running
    2022-01-12 15:59:29,898 - getstatusapp:287 - INFO - psutil.Process(pid=8447, name='Hermes', status='sleeping', started='15:02:38')
    2022-01-12 15:59:29,901 - ScanTask:223 - INFO - check if the app is running
    2022-01-12 15:59:29,936 - getstatusapp:287 - INFO - psutil.Process(pid=5781, name='HermesWeb', status='sleeping', started='11:13:50')
    2022-01-12 15:59:29,939 - check:387 - INFO - checked the system and put this info in the log
    2022-01-12 15:59:29,939 - getsysinfo:348 - INFO - getting sys info
    2022-01-12 15:59:29,940 - PersistenceTask:250 - INFO - veryfy json
    2022-01-12 15:59:29,941 - PersistenceTask:256 - ERROR - Error in PersistenceTask [Errno 2] No such file or directory: '/home/pi/testJCH/config.json'
    2022-01-12 15:59:29,941 - run:210 - INFO - Timeout wait...10
```

## For run on startup

* Edit file /etc/rc.local

```Shell
    sudo nano /etc/rc.local
```

* Add before "exit 0"

```Python
    sudo python3 /home/pi/watchdogWolke/watchdogWolke.py start
```
