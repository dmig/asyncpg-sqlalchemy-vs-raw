from random import randint
from time import time_ns
import asyncio
import asyncpg

from sqlalchemy import MetaData, Table, Column, Integer, String, ForeignKey, bindparam
from sqlalchemy.ext.asyncio import create_async_engine

ITERATIONS = 100000
NAME_TPL = 'table1%06d'

metadata = MetaData()

table1 = Table('table1', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(16), nullable=False)
)


async def prepare():
    engine = create_async_engine("postgresql+asyncpg:///test?host=/run/postgresql/")

    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)

        await conn.execute(table1.insert(), [
            {'name': NAME_TPL % (i, )} for i in range(1000)
        ])
    return engine

async def sa_main():
    times = []
    engine = await prepare()

    async with engine.connect() as conn:
        t0 = time_ns()
        for _ in range(ITERATIONS):
            # existing record
            await conn.execute(table1.select().where(table1.c.name==NAME_TPL % (randint(0, 1000), )))
            # nonexistent record
            await conn.execute(table1.select().where(table1.c.name==NAME_TPL % (randint(1000, 2000), )))
        times.append(time_ns() - t0)

    async with engine.connect() as conn:
        t0 = time_ns()
        stmt = table1.select().where(table1.c.name==bindparam('table1name'))
        for _ in range(ITERATIONS):
            # existing record
            await conn.execute(stmt, {'table1name': NAME_TPL % (randint(0, 1000), )})
            # nonexistent record
            await conn.execute(stmt, {'table1name': NAME_TPL % (randint(1000, 2000), )})
        times.append(time_ns() - t0)

    return times

async def raw_main():
    times = []
    conn: asyncpg.Connection = await asyncpg.connect("postgresql:///test?host=/run/postgresql/")

    t0 = time_ns()
    for _ in range(ITERATIONS):
        # existing record
        await conn.fetch('SELECT "table1".id, "table1".name FROM "table1" WHERE "table1".name = $1',
                         NAME_TPL % randint(0, 1000))
        # nonexistent record
        await conn.fetch('SELECT "table1".id, "table1".name FROM "table1" WHERE "table1".name = $1',
                         NAME_TPL % randint(1000, 2000))
    times.append(time_ns() - t0)

    t0 = time_ns()
    stmt = await conn.prepare('SELECT "table1".id, "table1".name FROM "table1" WHERE "table1".name = $1')
    for _ in range(ITERATIONS):
        # existing record
        await stmt.fetch(NAME_TPL % randint(0, 1000))
        # nonexistent record
        await stmt.fetch(NAME_TPL % randint(1000, 2000))
    times.append(time_ns() - t0)

    await conn.close()

    return times

print('Executing', ITERATIONS, 'iterations')

times = asyncio.run(sa_main())
print('sqlalchemy inline, prepared:', list(map(lambda tm: tm / 1000_000, times)))

times = asyncio.run(raw_main())
print('raw inline, prepared:', list(map(lambda tm: tm / 1000_000, times)))
