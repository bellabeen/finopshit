import boto3
import datetime
import os
import psycopg2

# Set the AWS profile using the AWS_PROFILE environment variable
os.environ['AWS_PROFILE'] = 'tunas2w'

# Create the AWS Cost Explorer client
client = boto3.client('ce', region_name='ap-southeast-1')

# Define start and end dates
start_date = '2024-04-01'
end_date = '2024-04-02'

# List of tunas:cost-center values
cost_centers = ['ASP', 'DHT']

# Make the API call to get the cost and usage data
response = client.get_cost_and_usage(
    TimePeriod={
        'Start': start_date,
        'End': end_date
    },
    Granularity='DAILY',
    Metrics=['UnblendedCost'],
    GroupBy=[
        {
            'Type': 'DIMENSION',
            'Key': 'SERVICE'
        }
    ],
    Filter={
        'Tags': {
            'Key': 'tunas:cost-center',
            'Values': cost_centers
        }
    }
)

# Convert the response to a string
data_string = str(response)

# Print the data string
print(data_string)
