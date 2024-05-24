from .. import errors

import threading


class ConnPoolRef:
    def __init__(self, thread: threading.Thread, conn, cursor, callback):
        self.thread = thread
        self.conn = conn
        self.cursor = cursor

        # start monitoring the target thread
        threading.Thread(target=self.start_monitor, args=(callback,)).start()

    def start_monitor(self, callback: callable) -> None:
        """
        This function will monitor on the target thread, and call the 'callback' function when the thread is terminated.

        :param callback: The function to call when the thread is terminated.
        :type callback: callable
        """
        self.thread.join()
        callback()


class ConnPool:
    def __init__(self, driver, db_name: str, **conn_ops):
        self.driver = driver
        self.conn_info = (db_name, conn_ops)
        self.pool = {}

    def __del__(self):
        if len(self.pool) > 0:
            self.close()
            raise errors.ConnPoolNotClosedError(
                "The connection pool is not fully closed. Automatically closed all connections for you."
            )

    def _new_conn(self):
        """
        [Private] Create a new connection
        """
        db_aname, conn_ops = self.conn_info
        conn = self.driver.connect(db_aname, **conn_ops)
        return conn

    def _create_conn(self, thread: threading.Thread):
        """
        [Private] Create a new connection for the target thread, and add it to the pool

        :param thread: The target thread
        :type thread: threading.Thread

        .. warning::
            This method will not do cheks for the existence of the connection in the pool.
            Using this method improperly can cause the pool to overwrite the connection of the target thread.
        """
        # ensure the id is unique and predictable
        conn_id = id(thread)

        conn = self._new_conn()
        cursor = conn.cursor()

        self.pool[conn_id] = ConnPoolRef(
            thread, conn, cursor, lambda: self._remove_conn(conn_id)
        )

    def _remove_conn(self, conn_id):
        """
        [Private] Remove the connection from the pool
        """
        ref = self.pool.pop(conn_id)
        ref.conn.close()

    def get_ref(self) -> ConnPoolRef:
        """
        Get the ConnPoolRef object for the current thread

        :return: The ConnPoolRef object
        :rtype: ConnPoolRef
        """
        thread = threading.current_thread()
        conn_id = id(thread)

        if conn_id not in self.pool:
            self._create_conn(thread)

        return self.pool[conn_id]

    def get_conn(self):
        """
        Get the connection object for the current thread
        """
        return self.get_ref().conn

    def get_cursor(self):
        """
        Get the cursor object for the current thread
        """
        return self.get_ref().cursor

    def close(self):
        """
        Close all the connections in the pool
        """
        for conn_id in list(self.pool.keys()):
            self._remove_conn(conn_id)
