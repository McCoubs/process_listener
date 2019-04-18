import psutil
import subprocess
import ast
import os
import sys
from threading import Thread, Lock


class NotifyThreadHandler:
    def __init__(self):
        self.pids = set()
        self.mutex = Lock()

    def generate_thread(self, process, title, subtitle, message):
        pid = process.info['pid']
        # don't run if process is being handled by another thread
        if pid in self.pids:
            return

        # lock and add pid to blacklist
        self.mutex.acquire()
        self.pids.add(pid)
        self.mutex.release()

        # create notifier
        thread = NotifyThreadHandler.NotifyThread(process, title, subtitle, message, self.remove_pid, (pid,))
        thread.start()

    def remove_pid(self, pid):
        # acquire lock and remove pid from blacklist
        self.mutex.acquire()
        self.pids.remove(pid)
        self.mutex.release()

    class NotifyThread(Thread):
        def __init__(self, process, title, subtitle, message, callback, callback_args=None):
            super(NotifyThreadHandler.NotifyThread, self).__init__()
            self.process = process
            self.title = title
            self.subtitle = subtitle
            self.message = message
            self.callback = callback
            self.callback_args = callback_args

        def run(self):
            # generate the required flags
            m = '-message {!r}'.format(self.message)
            t = '-title {!r}'.format(self.title)
            st = '-subtitle {!r}'.format(self.subtitle)
            a = '-actions {!r}'.format('Kill')
            c = '-closeLabel {!r}'.format('Ignore')
            ext = '-timeout 10 -json'

            # generate notification and return the response object
            dir_path = os.path.dirname(os.path.realpath(__file__))
            raw_output = subprocess.check_output(
                '{}/terminal-notifier {}'.format(dir_path, ' '.join([m, t, st, a, c, ext])), shell=True)
            response_dict = ast.literal_eval(raw_output.decode('utf-8'))

            # process response and kill if necessary
            if response_dict.get('activationValue', '') == 'Kill':
                try:
                    self.process.terminate()
                except psutil.NoSuchProcess as err:
                    print('Error:', err.msg, '--- while trying to terminate')
            # callback function
            self.callback(*self.callback_args)


# runner logic
if __name__ == '__main__':
    usage = 'Usage: sudo python process_listener.py <desired cpu usage: limit >= 0> ' \
            '<desired memory usage: limit >= 0>'
    # checking args
    if len(sys.argv) < 3:
        print(usage)
        exit(1)
    try:
        cpu_usage_limit, mem_usage_limit = int(sys.argv[1]), int(sys.argv[2])
    except ValueError as e:
        print(usage)
        exit(1)
    if cpu_usage_limit < 0 or mem_usage_limit < 0:
        print(usage)
        exit(1)

    cpu_count = psutil.cpu_count(True)
    notifier_handler = NotifyThreadHandler()
    print('success: started listening to memory and CPU usage...')
    while True:
        # get current usage
        cpu_usage = sum(psutil.cpu_percent(interval=1, percpu=True)) / cpu_count
        mem_usage = psutil.virtual_memory().percent

        # if cpu usage is more than desired percent of system
        if cpu_usage >= cpu_usage_limit:
            # check all currently running processes
            for proc in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent']):
                cpu_percent = proc.info['cpu_percent']
                if cpu_percent is None:
                    continue

                # notify user of large process, kill if responded
                if cpu_percent >= 40:
                    notifier_handler.generate_thread(proc, 'Process Listener', f"Process name: {proc.info['name']}",
                                                     f'CPU usage at: {str(round(cpu_percent, 2))}%')

        # if memory usage is more than desired percent of system
        elif mem_usage >= mem_usage_limit:
            # check all currently running processes
            for proc in psutil.process_iter(attrs=['pid', 'name']):
                mem_percent = proc.memory_percent()
                if mem_percent is None:
                    continue

                # notify user of large process, kill if responded
                if mem_percent >= 20:
                    notifier_handler.generate_thread(proc, 'Process Listener', f"Process name: {proc.info['name']}",
                                                     f'RAM usage at: {str(round(mem_percent, 2))}%')
