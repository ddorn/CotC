import sys

while True:
    print(input(), file=sys.stderr)
    nb = int(input())
    print(nb, file=sys.stderr)

    for i in range(nb):
        print(input(), file=sys.stderr)

    print("PORT")
    print("PORT")
    print("PORT")