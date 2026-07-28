import threading

quad_last_status_data_lock = threading.Lock()
quad_last_status_data      = {}                 # shared last drone status (thread-safe via lock)
quad_isMissionInProgress   = threading.Event()
