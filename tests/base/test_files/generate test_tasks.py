import csv
from operator import add, mul, sub
from random import randint, choice, choices

fp = "test.csv"

OPERATIONS = {"+": add,
              "-": sub,
              "*": mul}

with open(fp, mode="w", encoding="UTF-8", newline='') as csvfile:
    fieldnames = ["equation", "word"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()

    for row in range(3000):
        word = "".join(choices("qwertyuiopasdfghjklzxcvbnm", k=5))
        operation = choice(("-", "+", "*"))
        first = randint(-100, 100)
        second = randint(-100, 100)
        result = OPERATIONS[operation](first, second)
        equation = f"{first} {operation} {second} = {result}"
        
        
        writer.writerow({'equation': equation,
                         'word': word})
