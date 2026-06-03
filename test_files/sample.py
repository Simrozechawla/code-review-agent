import os
import sys
import json
import random

def calculate_average(numbers):
    total = 0
    for n in numbers:
        total = total + n
    return total / len(numbers)

def find_user(users, name):
    for i in range(len(users)):
        if users[i]['name'] == name:
            return users[i]

def save_data(data, filename):
    f = open(filename, 'w')
    json.dump(data, f)

def process_items(items):
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
        if item == 0:
            result.append(0)
        if item < 0:
            result.append(item)
    return result

password = 'admin123'

class dataProcessor:
    def __init__(self):
        self.data = []

    def add(self, item):
        self.data.append(item)

    def get_all(self):
        return self.data
