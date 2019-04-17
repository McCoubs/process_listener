import psutil
import subprocess
import ast
import os
import sys
import threading

PIDS = set()


class NotifyThread(threading.Thread):
    def __init__(self, process, title, subtitle, message):
        super(NotifyThread, self).__init__()
        self.process = process
        self.title = title
        self.subtitle = subtitle
        self.message = message
        PIDS.add(self.process.info['pid'])

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
                PIDS.remove(self.process.info['pid'])
            except psutil.NoSuchProcess as err:
                print('Error:', err.msg, '--- while trying to terminate')


# runner logic
if __name__ == '__main__':
    usage = 'Usage: sudo python process_listener.py <desired system cpu usage: limit >= 0> ' \
            '<desired single process cpu usage: limit >= 0>'
    # checking args
    if len(sys.argv) < 3:
        print(usage)
        exit(1)
    try:
        system_usage_limit, single_usage_limit = int(sys.argv[1]), int(sys.argv[2])
    except ValueError as e:
        print(usage)
        exit(1)
    if system_usage_limit < 0 or single_usage_limit < 0:
        print(usage)
        exit(1)

    # currently only checking cpu usage
    cpu_count = psutil.cpu_count(True)
    print('success: started listening to cpu usage...')
    while True:
        # get current usage
        cpu_usage = sum(psutil.cpu_percent(interval=1, percpu=True))
        ram_usage = psutil.virtual_memory().percent

        # if cpu usage is more than desired percent of system
        if cpu_usage >= (cpu_count * system_usage_limit):
            # check all currently running processes
            for proc in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent']):
                # if large process (defined by user), notify user, kill if responded
                if proc.info['pid'] not in PIDS and proc.info['cpu_percent'] >= single_usage_limit:
                    notify = NotifyThread(proc, 'Process Listener', '',
                                          proc.info['name'] + ' at CPU USAGE: ' + str(proc.info['cpu_percent']) + '%')
                    notify.start()
