# Simple MacOSX Process Moniter

This is a simple python script that monitors cpu usage, and displays desktop notifications of possible errant processes, allowing the user to kill or ignore processes from the prompt

## Setup 

- script requires python 3.4.x (psutil support)
- create a python virtual environment for script (or just use base python if you prefer)
  - `pip install virtualenv && virtualenv <target> && source <target>/bin/activate`
- `pip install -r requirements.txt` to install all requirements for script
- currently using [terminal-notifier](https://github.com/julienXX/terminal-notifier) v1.8.0 for MacOSX desktop notifications
  - note version 1.8.0 is necessary to support actions and timeout
  - future versions will hopefully use a python library for desktop notifications (or at least a more supportive notifier)
  
## Usage

`sudo python process_listener.py <desired system cpu usage: limit >= 0> <desired single process cpu usage: limit >= 0>`
  
