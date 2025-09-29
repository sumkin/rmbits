import yaml
import boto3 

with open("/home/ay49514/rmbits/config.yaml") as f:
    d = yaml.load(f)
    dynamodb = boto3.resource("dynamodb",
        aws_access_key_id = d["DYNAMODB_DATABASE"]["ACCESS_KEY_ID"],
        aws_secret_access_key = d["DYNAMODB_DATABASE"]["SECRET_ACCESS_KEY"],
        region_name = d["DYNAMODB_DATABASE"]["REGION_NAME"]    
    )

    table = dynamodb.Table("GROUP_OPT_SERIES_RESULTS")

    response = table.scan()
    data = response["Items"]

    while "LastEvaluateKey" in response:
        response = table.scan(ExclusiveStartKey = response["LastEvaluatedKey"])
        data.extend(response["Item"])

    for d in data:
        print(d)