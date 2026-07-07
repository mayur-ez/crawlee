from pystalk import BeanstalkClient


class Queue:

    def __init__(self):

        self.client = BeanstalkClient(
            host="localhost",
            port=11300,
        )