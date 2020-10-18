from evohomeasync2 import EvohomeClient
from asyncio import run, sleep, get_event_loop
from aiosqlite import connect
from sqlite3 import OperationalError
from time import time

def whitelist(text):
    return ''.join([(c if c.isalnum() or c == ' ' else '_') for c in text])

async def query():
    wakeup()
    db = await connect('records.sqlite')
    try:
        await db.execute('CREATE TABLE events (thermostat name, time real, temperature real, setpoint real)')
    except OperationalError as e:
        print('error from sqlite')
        if 'table events already exists' in repr(e):
            print('as expected')
        else:
            raise
    with open('credentials.txt', 'r') as o:
        username = o.readline().strip()
        password = o.readline().strip()
    client = EvohomeClient(username,  password)
    await client.login()
        
    print('hello')
    while True:
        temps = await client.temperatures()
        async for device in temps:
            print(device)
            name = whitelist(device['name'])
            temp = float(device['temp'])
            setpoint = float(device['setpoint']) if device.get('setpoint') else 0
            cmd = f'INSERT INTO events (thermostat, time, temperature, setpoint) values ("{name}", {time()}, {temp}, {setpoint})'
            print(cmd)
            await db.execute(cmd)
        await sleep(300)
    await client._session.close()
    await db.close()
    await whitelist()

# see https://stackoverflow.com/questions/27480967/why-does-the-asyncios-event-loop-suppress-the-keyboardinterrupt-on-windows
async def wakeup():
    while True:
        await sleep(1)

    
get_event_loop().run_until_complete(query())
