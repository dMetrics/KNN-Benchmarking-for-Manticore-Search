from threading import BoundedSemaphore


class MaxQueuePool:
    """This Class wraps a concurrent.futures.Executor limiting the size of its
    task queue.

    If `max_queue_size` tasks are submitted, the next call to submit will block
    until a previously submitted one is completed.
    """

    def __init__(self, executor, max_queue_size, max_workers=None):
        self.pool = executor(max_workers=max_workers)
        self.pool_queue = BoundedSemaphore(max_queue_size)

    def submit(self, function, *args, **kwargs):
        """Submits a new task to the pool, blocks if Pool queue is full."""
        self.pool_queue.acquire()

        future = self.pool.submit(function, *args, **kwargs)
        future.add_done_callback(self.pool_queue_callback)

        return future

    def pool_queue_callback(self, _):
        """Called once task is done, releases one queue slot."""
        self.pool_queue.release()
