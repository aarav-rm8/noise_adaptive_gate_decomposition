from catalogue import CATALOGUE

for item in CATALOGUE:

    print("="*60)
    print(item["name"])
    print("="*60)

    qc = item["builder"]()

    print(qc.draw("text"))