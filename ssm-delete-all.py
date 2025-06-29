import boto3
import sys

ssm = boto3.client("ssm", region_name="us-east-2")


def delete_all_parameters_by_path(path_prefix: str):
    sys.exit(1)  # uncomment to run

    next_token = None
    while True:
        # Step 1: List parameters
        list_args = {"Path": path_prefix, "Recursive": True, "MaxResults": 10}
        if next_token:
            list_args["NextToken"] = next_token

        response = ssm.get_parameters_by_path(**list_args)
        names = [param["Name"] for param in response["Parameters"]]

        # Step 2: Delete in batches of up to 10
        if names:
            print(f"Deleting {len(names)} parameters...")
            ssm.delete_parameters(Names=names)

        next_token = response.get("NextToken")
        if not next_token:
            break


# Example usage
delete_all_parameters_by_path("/dev/")
delete_all_parameters_by_path("/prd/")
