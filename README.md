# smartPip

## Abstract

SmartPip can automatically resolve dependencies in Python projects, solve dependency conflicts, and avoid the waste of bandwidth and time caused by PIP's backtracking strategy. 

At the same time, SmartPip can also share third-party libraries in local repository to reduce the user's hard disk space.



## Installation 

```shell
cd smartpip/
python setup.py install # install smartpip
```



## Use

### Example

```shell
# requirements.txt
# 	idna>2.6
#		requests==2.22.0
cd example/
PySI -r requirements.txt
```



## Result

#### use smartPip to solver and install requirements.txt

```shell
PySI -r requirements.txt -g

install file has been successfully output
req.txt : requirements.txt

# install.txt
#		idna==2.8
# ......
#		requests==2.22.0
```



## Compare smartPip to pip

#### use pip to install requirements.txt

```shell
pip install -r requirements.txt

Collecting idna>2.6
  Downloading idna-3.3-py3-none-any.whl (61 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 61.2/61.2 KB 870.1 kB/s eta 0:00:00
Collecting requests==2.22.0
  Downloading requests-2.22.0-py2.py3-none-any.whl (57 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 58.0/58.0 KB 4.7 MB/s eta 0:00:00
Collecting idna>2.6
  Downloading idna-2.8-py2.py3-none-any.whl (58 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 58.6/58.6 KB 6.9 MB/s eta 0:00:00
......
Installing collected packages: chardet, urllib3, idna, certifi, requests
```

Installing version : *idna-2.8 requests-2.22.0*

package iterations : 2 times for *idna*



