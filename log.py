from datetime import datetime
import os

class Logging:
    def __init__(self, log_file_name):
        self.log_path = 'log/' + log_file_name
        self.log_enabled = False
    def start(self):
        self.log_enabled = True
        if not os.path.exists('log'):
            os.makedirs('log')
    def log(self, content):
        if self.log_enabled:
            with open(self.log_path, 'a+') as f:
                f.write(str(datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')) + '\t  ' + str(content) + '\n')
            f.close()
