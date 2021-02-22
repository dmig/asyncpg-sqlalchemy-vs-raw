# A simple performance comparision for SQLAlchemy + asyncpg

Creates a simple table, executes a series of simple queries and measures execution times.

## prerequisites
- Installed PostgreSQL
- peer authentication enabled (otherwise adjust DSNs accordingly)
- local socket path `/run/postgresql/`

## setup
```sh
$ pip3 install -r requirements.txt
$ sudo -u postgres createuser $USER
$ sudo -u postgres createdb test -O $USER
```
This will install `asyncpg` and `sqlalchemy`  1.4beta or newer (required to
utilize asynpg as a backend).

## run
```sh
$ python3 sa-vs-raw.py
```

## My results
```
$ python3 sa-vs-raw.py
Executing 100000 iterations
sqlalchemy inline, prepared: [53636.789534, 30416.472297]
raw inline, prepared: [19397.920068, 18982.737795]
```
The meaning:
- for SQLAlchemy
  - inline statement (`table1.select().where(table1.c.name==NAME_TPL % (randint(0, 1000), ))`)
    executed 100000 times took 53636.789534ms -> 0.536ms per query
  - prepared once and executed many times query took 30416.472297ms -> 0.304ms per query
- for raw SQL
  - inline statement (`'SELECT "table1".id, "table1".name FROM "table1" WHERE "table1".name = $1'`
    -- exactly same syntax as SQLAlchemy creates) executed 100000 times took 19397.920068ms -> 0.194ms per query
  - prepared once and executed many times query took 18982.737795ms -> 0.189ms per query
  such a little difference is caused by `asyncpg` query caching using prepare/execute
