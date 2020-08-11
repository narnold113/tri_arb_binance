import asyncio
import time

async def function1():
    while 1:
        now = time.time()
        await asyncio.sleep(0.001)
        print('Time diff =', time.time() - now)

async def function2():
    while 1:
        await asyncio.sleep(2)
        print('Hello from function 2!')


async def sub_main():
    # sub_coroutines = []
    # sub_coroutines.append(function1())
    # sub_coroutines.append(function2())
    await asyncio.wait([function1()])

async def main():
    coroutines = []
    # coroutines.append(function1())
    # coroutines.append(function2())
    coroutines.append(sub_main())
    await asyncio.wait(coroutines)



if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except:
        pass
    finally:
        loop.close()
