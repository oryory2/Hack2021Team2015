import time
from datetime import datetime

t0 = datetime.now()
while (datetime.now() - t0).seconds < 3:
    print("g")