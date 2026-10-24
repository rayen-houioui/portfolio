try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:  # PyMySQL absent : SQLite utilisé en repli
    pass
