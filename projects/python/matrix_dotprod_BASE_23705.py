#! /usr/bin/python

import numpy as np
import json

json_string = "{\n    \"w00\": \"77\",\n    \"w01\": \"19\"\n}\n"
parsed_json = json.loads(json_string)
print(parsed_json['w00'])

w = np.array([[ 5, 1 ,3], 
              [ 1, 1 ,1], 
              [ 1, 2 ,1]])

x = np.array([1, 2, 3])


x = np.empty((1, 3), dtype=int)

x[0,0] = 1;
x[0,1] = 2;
x[0,2] = 3;

print x.dot(w)

