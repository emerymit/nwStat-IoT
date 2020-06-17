import speedtest
import psycopg2
import uuid
from datetime import datetime
import RPi.GPIO as GPIO
import time

LED_ON = True
LED_OFF = False

GPIO.setmode(GPIO.BCM)
GPIO.setup(15, GPIO.OUT)

#capture the current time
dt = datetime.now()
print("###EXECUTE###")
print("Op Time: " + str(dt))
print("Starting network test")
GPIO.output(15, LED_ON)
#conduct the network speed test
success = False
downFormatted = 0
upFormatted = 0
try: 
    servers = []
    threads = None
    s = speedtest.Speedtest()
    s.get_servers(servers)
    s.get_best_server()
    s.download(threads=threads)
    s.upload(threads=threads)
    s.results.share()
    #store the results
    results_dict = s.results.dict()
    #print(results_dict)
    #print("\n\n\n\n")
    print("Network test successfully run")
    success = True

    upFormatted = results_dict["upload"]/(1024*1024)
    downFormatted = results_dict["download"]/(1024*1024)

except Exception as e:
    print(e)
finally: 
    GPIO.output(15, LED_OFF)
#store the results
if success:
    print("Connecting to DB")
    try:
        connection = psycopg2.connect(user = "amigo",
                                  password = "burlington",
                                  host = "127.0.0.1",
                                  port = "5432",
                                  database = "5155_networkstats")
        cursor = connection.cursor()
        # Print PostgreSQL Connection properties
        print ("Connected to postgresdb")
        # Print PostgreSQL version
        cursor.execute("""INSERT INTO networkstats
                        (upload, serverLoc, ping, isp, id, hostname, download, time, publicIP)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);""", 
                        (results_dict["upload"], results_dict["server"]["name"],
                        results_dict["ping"], results_dict["client"]["isp"], str(uuid.uuid4()), 
                        results_dict["server"]["host"], results_dict["download"], dt,
                        results_dict["client"]["ip"],))
        #must commit transaction
        connection.commit()
        print("captured results in DB")
    except (Exception, psycopg2.Error) as error :
        print ("Error while connecting to PostgreSQL", error)
    finally:
        #closing database connection.
            if(connection):
                cursor.close()
                connection.close()
                print("PostgreSQL connection is closed")
                for x in range(1,4):
                    GPIO.output(15, LED_ON)
                    time.sleep(0.2)
                    GPIO.output(15, LED_OFF)
                    time.sleep(0.5)

print("### END ###\n\n\n\n")
