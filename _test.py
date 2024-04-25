import numpy as np

ext = { # Height and time extents
  "max_z": 0, # m.a.s.l
  "min_z": -115, # m.a.s.l
}

""" ext = { # Height and time extents
  "max_z": 115, # m.a.s.l
  "min_z": 0, # m.a.s.l
} """

res = { # Analysis resolution
  "x": 100, # meters
  "y": 100, # meters
  "z": 1, # meters
}

a = np.arange(
      ext['min_z'], 
      ext['max_z'] + res['z'], res['z']).tolist()

print(a)