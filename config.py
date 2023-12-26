from dotenv import get_key
import mysql.connector
from mysql.connector import pooling

conPool = pooling.MySQLConnectionPool(user= get_key(".env", "user"), password= get_key(".env", "password"), host='localhost', database='attractions', pool_name='attractionsConPool', pool_size=10,  auth_plugin='mysql_native_password')
