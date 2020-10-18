from evohomeasync2 import EvohomeClient
from asyncio import run, sleep, get_event_loop

async def query():
    await sleep(0.1)
    with open('credentials.txt', 'r') as o:
        username = o.readline().strip()
        password = o.readline().strip()
    print(username, password)
    client = EvohomeClient(username,  password)
    await client.login()
    print('hello')
    for i in range(1):
        temps = await client.temperatures()
        print('temps',temps)
        async for device in temps:
            print(device)
        await sleep(5.0)
    await client._session.close()
print('start')
get_event_loop().run_until_complete(query())
