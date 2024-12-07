import boto3
quicksight_client = boto3.client('quicksight', region_name='us-east-1')
aws_account_id = "522814694309"
dashboard_id = "8fb94a84-c221-403e-82db-9163af81e65c"

try:
    response = quicksight_client.get_dashboard_embed_url(
        AwsAccountId=aws_account_id,
        DashboardId=dashboard_id,
        IdentityType="QUICKSIGHT",
        SessionLifetimeInMinutes=600,
        UserArn="arn:aws:quicksight:us-east-1:522814694309:user/default/2bmayonaise"
    )
    embed_url = response['EmbedUrl']
    print("Embed URL:", embed_url)
except Exception as e:
    print("Error generating embed URL:", e)
