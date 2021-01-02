#sets a semaphore read my bluvo.py
import pickle
manualForcePoll = False
with open('semaphore.pkl', 'wb') as f:
    pickle.dump([manualForcePoll], f)