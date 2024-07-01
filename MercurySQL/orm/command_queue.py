"""
This file offers the `CommandQueue` class, which is used to queue and execute commands in the MercurySQL package.

This is useful when you are working with multiple threads and want to execute commands in a specific order.
"""

import queue
import threading

FETCHALL = -1


class CommandQueue:
    def __init__(self, driver, db_name: str, **conn_ops):
        self.driver = driver
        self.conn_info = (db_name, conn_ops)

        self.queue = queue.Queue()

        # start the loop, starts to process the project now
        self.isRunning = True
        self.loop()

    def stop(self):
        self.isRunning = False

    def __del__(self):
        self.stop()

    def put(self, command):
        """
        Put a command into the queue.

        :param command: The command to put into the queue.
        :type command: Any
        """
        self.queue.put(command)

    def loop(self):
        """
        Loop through the queue and execute each command (in an new thread).
        When the queue is empty, the loop will wait for new commands.
        """

        # start a new thread
        def loop_thread():
            # start a new conn
            db_aname, conn_ops = self.conn_info
            conn = self.driver.connect(db_aname, **conn_ops)
            cursor = conn.cursor()
            self.cursor = cursor

            while self.isRunning:
                data, size, callback = self.queue.get()
                query, param = data

                cursor.execute(query, param)
                result = None
                
                if size == FETCHALL:
                    result = cursor.fetchall()
                else:
                    result = cursor.fetchmany(size)

                callback(result)
                self.queue.task_done()

        threading.Thread(target=loop_thread).start()

    def get_cursor(self):
        """
        Return a fake cursor that will transfer the command to the real cursor in seperate thread.

        :return: The cursor.
        :rtype: Cursor
        """

        return CQFakeCursor(self)


class CQFakeCursor:
    def __init__(self, cq):
        self.cq = cq
        self.event = threading.Event()

    def execute(self, query: str, param: tuple):
        """
        Execute a query.
        The query will be executed when fetching results.

        :param query: The query to execute.
        :type query: str
        :param param: The parameters for the query.
        :type param: tuple
        """
        self.data = (query, param)
        self.result = None

    def fetchall(self):
        """
        Fetch all results.

        :return: The results.
        :rtype: list
        """

        def callback(result):
            self.result = result
            self.event.set()

        self.cq.put((self.data, FETCHALL, callback))
        self.event.wait()  # wait

        return self.result

    def fetchone(self):
        """
        Fetch one result.

        :return: The result.
        :rtype: Any
        """

        def callback(result):
            self.result = result
            self.event.set()

        self.cq.put((self.data, 1, callback))
        self.event.wait()

        return self.result

    def fetchmany(self, size: int):
        """
        Fetch a specific number of results.

        :param size: The number of results to fetch.
        :type size: int
        """

        def callback(result):
            self.result = result
            self.event.set()

        self.cq.put((self.data, size, callback))
        self.event.wait()

        return self.result
