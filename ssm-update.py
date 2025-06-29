from dataclasses import dataclass
import os
import csv
import sys
import boto3


@dataclass
class Param:
    env: str
    business: str
    store: str
    addr: str


def main():
    # guard usage
    if not len(sys.argv) > 1:
        print("usage: python update-ssm.py <csv-path>")
        sys.exit(1)

    # guard csv
    csvpath = sys.argv[1]
    if not os.path.exists(csvpath):
        print(f"error: file not found {csvpath}")
        sys.exit(1)

    # data
    data = []
    with open(csvpath) as f:
        reader = csv.DictReader(f)

        for row in reader:
            print(row)
            data.append(
                Param(
                    env=row["env"],
                    business=row["business"],
                    store=row["store"],
                    addr=row["ip_address"],
                )
            )

    if len(data) == 0:
        print("error: datasource produced no data")
        sys.exit(1)

    # update ssm
    ssm = boto3.client("ssm")

    for x in data:
        path = f"/{x.env}/business/{x.business}/store/{x.store}/host"

        try:
            res = ssm.put_parameter(
                Name=path, Value=x.addr, Type="SecureString", Overwrite=True
            )

            # print(res)

            if res.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
                print(f"+ created param : {path}")
            else:
                print(f"! failed to create param : {path}")

        except Exception as e:
            print(f"! failed to create param {path} : {e}")


if __name__ == "__main__":
    main()
