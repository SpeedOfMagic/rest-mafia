from queue import SimpleQueue


class SubscriberQueue:
    subscriber_queue: dict[str, SimpleQueue]

    def __init__(self, subscribers: list[str]):
        self.subscriber_queue = {sub: SimpleQueue() for sub in subscribers}

    def get(self, subscriber: str):
        if subscriber not in self.subscriber_queue:
            return None
        return self.subscriber_queue[subscriber].get()

    def put(self, msg):
        for queue in self.subscriber_queue.values():
            queue.put(msg)
