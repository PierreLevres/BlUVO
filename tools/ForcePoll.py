#sets a semaphore read my debug.py
import pickle
manualForcePoll = True
with open('../semaphore.pkl', 'wb') as f:
    pickle.dump(manualForcePoll, f)