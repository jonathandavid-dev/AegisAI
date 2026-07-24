import asyncio
import threading
from typing import Coroutine, Any
from concurrent.futures import Future

def run_sync(coro: Coroutine) -> Any:
    """
    Executes an async coroutine synchronously from a synchronous context.
    Safely handles cases where an event loop is already running in the current thread.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop in the current thread, we can run it directly
        return asyncio.run(coro)

    # An event loop is already running, run the coroutine in a separate thread
    def target(fut: Future, c: Coroutine):
        try:
            res = asyncio.run(c)
            fut.set_result(res)
        except Exception as e:
            fut.set_exception(e)

    future = Future()
    t = threading.Thread(target=target, args=(future, coro))
    t.start()
    t.join()
    return future.result()
