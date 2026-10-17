"""Job control for PyShell: background processes, jobs table, fg/bg/kill."""
import threading
import time


class Job:
    _next_id = 1

    def __init__(self, command, thread, stop_event):
        self.id = Job._next_id
        Job._next_id += 1
        self.command = command
        self.thread = thread
        self.stop_event = stop_event
        self.state = "Running"

    def __repr__(self):
        return "[" + str(self.id) + "] " + self.state + " " + self.command


class JobManager:
    def __init__(self, shell):
        self.shell = shell
        self.jobs = {}

    def add(self, command, fn):
        stop_event = threading.Event()

        def runner():
            try:
                fn()
            except Exception as e:
                self.shell.err("[job " + str(command) + "] " + str(e))
            finally:
                # remove this job when done
                for jid, job in list(self.jobs.items()):
                    if job.thread is threading.current_thread():
                        job.state = "Done"
                        # give the user a moment to see it, then remove
                        time.sleep(0.5)
                        self.jobs.pop(jid, None)
                        break

        t = threading.Thread(target=runner, daemon=True)
        job = Job(command, t, stop_event)
        self.jobs[job.id] = job
        t.start()
        return job

    def list(self):
        return list(self.jobs.values())

    def get(self, jid):
        return self.jobs.get(jid)

    def remove(self, jid):
        self.jobs.pop(jid, None)
