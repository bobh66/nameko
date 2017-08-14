import os


class GenericEvent(object):
    def send(self, value, exc):
        pass

    def wait(self):
        pass

    def ready(self):
        pass

    def send_exception(self, exception):
        pass


class GenericPool(object):
    def waitall(self):
        pass

    def spawn(self, fcn, *args, **kwargs):
        pass


if os.environ.get('EVENTLOOP', 'eventlet') == 'eventlet':
    import eventlet
    import eventlet.event
    import eventlet.greenpool
    import eventlet.queue
    import eventlet.websocket
    import eventlet.wsgi
    from eventlet import backdoor

    Event = eventlet.event.Event
    getcurrent = eventlet.getcurrent
    GreenPool = eventlet.greenpool.GreenPool
    LightQueue = eventlet.queue.LightQueue
    listen = eventlet.listen
    monkey_patch = eventlet.monkey_patch
    spawn = eventlet.spawn
    spawn_n = eventlet.spawn_n
    Timeout = eventlet.Timeout
    WebSocketWSGI = eventlet.websocket.WebSocketWSGI
    wsgi = eventlet.wsgi

    def setup_backdoor(runner, port):
        def _bad_call():
            raise RuntimeError(
                'This would kill your service, not close the backdoor. '
                ' To exit, use ctrl-c.')
        socket = eventlet.listen(('localhost', port))
        gt = eventlet.spawn(
            backdoor.backdoor_server,
            socket,
            locals={
                'runner': runner,
                'quit': _bad_call,
                'exit': _bad_call,
            })
        return socket, gt

elif os.environ.get('EVENTLOOP') == 'gevent':
    import gevent
    from gevent import backdoor
    from gevent.monkey import patch_all
    from gevent.event import AsyncResult
    from gevent.pool import Pool
    import gevent.queue
    import gevent.pywsgi
    import gevent.socket
    import geventwebsocket

    class GEventPool(GenericPool):
        def __init__(self):
            self.pool = Pool()

        def waitall(self):
            self.pool.join()

        def spawn(self, fcn, *args, **kwargs):
            self.pool.spawn(fcn, *args, **kwargs)

    class GEvent(GenericEvent):
        def __init__(self):
            self.event = AsyncResult()

        def send(self, result, exc):
            return self.event.set(result)

        def ready(self):
            return self.event.ready()

        def wait(self):
            return self.event.wait()

        def send_exception(self, exc, *args):
            return self.event.set_exception(exc, *args)

    Event = GEvent
    getcurrent = gevent.getcurrent
    GreenPool = GEventPool
    LightQueue = gevent.queue.Queue
    # listen = gevent.socket.listen
    monkey_patch = patch_all
    spawn = gevent.spawn
    spawn_n = gevent.spawn_raw
    Timeout = gevent.Timeout
    WebSocketWSGI = geventwebsocket.WebSocketApplication
    wsgi = gevent.pywsgi

    def setup_backdoor(runner, port):
        def _bad_call():
            raise RuntimeError(
                'This would kill your service, not close the backdoor. '
                'To exit, use ctrl-c.')
        gevent.spawn(
            backdoor.BackdoorServer,
            ('localhost', port),
            locals={
                'runner': runner,
                'quit': _bad_call,
                'exit': _bad_call,
            })


class EventletPool(GenericPool):
    def __init__(self):
        self.pool = GreenPool()

    def waitall(self):
        self.pool.waitall()

    def spawn(self, fcn, *args, **kwargs):
        self.pool.spawn(fcn, *args, **kwargs)
