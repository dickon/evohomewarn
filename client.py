from evohomeasync2 import EvohomeClient
from asyncio import run, sleep, get_event_loop

async def query():
    with open('credentials.txt', 'r') as o:
        username = o.readline().strip()
        password = o.readline().strip()
    client = EvohomeClient(username,  password)
    await client.login()
    print('hello')
    for i in range(1):
        if i > 0:         
            await sleep(5.0)
        temps = await client.temperatures()
        async for device in temps:
            print(device)
    await client._session.close()
print('start')
get_event_loop().run_until_complete(query())
