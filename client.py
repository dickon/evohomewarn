from evohomeasync2 import EvohomeClient
from asyncio import run, sleep, get_event_loop, create_task
from aiosqlite import connect
from sqlite3 import OperationalError
from time import time, gmtime
from aiohttp import web, ClientSession
from pygal import XY
from json import loads

def whitelist(text):
    return ''.join([(c if c.isalnum() or c == ' ' else '_') for c in text])



async def query():
    print('query running')
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
        weatherkey = o.readline().strip()
        city_name =  o.readline().strip()
    client = EvohomeClient(username,  password)
    await client.login()
        
    print('hello')
    while True:
        async with ClientSession() as session:
            url =f'http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={weatherkey}&units=metric'
            async with session.get(url) as response:
                json = await response.text()
            current = loads(json)
        temps = await client.temperatures()
        async for device in temps:
            print(device)
            name = whitelist(device['name'])
            temp = float(device['temp'])
            setpoint = float(device['setpoint']) if device.get('setpoint') else 0
            cmd = f'INSERT INTO events (thermostat, time, temperature, setpoint, outside) values ("{name}", {time()}, {temp}, {setpoint}, {current["main"]["temp"]})'
            print(cmd)
            await db.execute(cmd)
            # TODO: fold the existing events to work out if radiator is not producing heat on demand
        await db.commit()
        await sleep(300)
    await client._session.close()
    await db.close()
    await whitelist()

async def start_query(app):
    app['query'] = create_task(query())

async def stop_query(app):
    app['query'].cancel()
    await app['query']

# see https://stackoverflow.com/questions/27480967/why-does-the-asyncios-event-loop-suppress-the-keyboardinterrupt-on-windows
async def wakeup(app):
    while True:
        await sleep(1)

async def handle(request):
    name = whitelist(request.match_info.get('name', "Cave"))
    db = await connect('records.sqlite')
    cr = await db.execute(f'SELECT time, temperature, setpoint, outside FROM events WHERE thermostat="{name}" ORDER BY time')
    chart = XY(title=f'Recent temperature trend in {name}', x_title='Hours', y_title='degress celsius')
    setseries = []
    tempseries = []
    outsideseries = []
    now = time()
    for row in await cr.fetchall():
        dt = (row[0] - now)/3600
        tempseries.append((dt, row[1]))
        setseries.append((dt, row[2]))
        if row[3]:
            outsideseries.append((dt, row[3]))
    chart.add('temp', tempseries)
    chart.add('set', setseries)
    chart.add('outside', outsideseries)
    return web.Response(body=chart.render(), content_type='image/svg+xml')

app = web.Application()
app.router.add_get('/', handle)
app.router.add_get('/{name}', handle)
app.on_startup.append(start_query)
app.on_cleanup.append(stop_query)
web.run_app(app)
