import boto3
import datetime
import os
import psycopg2

# Set the AWS profile using the AWS_PROFILE environment variable
os.environ['AWS_PROFILE'] = 'tunas2w'

# Create the AWS Cost Explorer client
client = boto3.client('ce', region_name='ap-southeast-1')

# Define start and end dates
start_date = '2024-03-01'
end_date = '2024-04-09'

# List of tunas:cost-center values
cost_centers = ['ASP', 'DHT', 'TDM', 'IT']

# Connect to PostgreSQL database
conn = psycopg2.connect(
    dbname='finops',
    user='odoo',
    password='kepoajalu',
    host='localhost',
    port='5432'
)

# Create a cursor object using the cursor() method
cursor = conn.cursor()

# Check if the table exists, if not, create it
cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'cost')")
table_exists = cursor.fetchone()[0]

if not table_exists:
    # Define the SQL statement to create the table
    create_table_sql = """
    CREATE TABLE cost (
        id SERIAL PRIMARY KEY,
        service VARCHAR(255),
        cost DECIMAL(10, 2),
        date DATE,
        cost_center VARCHAR(255)
    )
    """
    
    # Execute the SQL command to create the table
    cursor.execute(create_table_sql)
    conn.commit()

# Loop over each cost center
for cost_center in cost_centers:
    # Make the API call to get the cost and usage data for the current cost center
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
                'Values': [cost_center]
            }
        }
    )

    # Insert data into the database
    for result in response['ResultsByTime']:
        for group in result['Groups']:
            service = group['Keys'][0]
            cost = group['Metrics']['UnblendedCost']['Amount']

            # SQL statement to check if the record already exists
            check_existence_sql = f"SELECT EXISTS (SELECT 1 FROM cost WHERE service = '{service}' AND date = '{result['TimePeriod']['Start']}' AND cost_center = '{cost_center}')"
            cursor.execute(check_existence_sql)
            record_exists = cursor.fetchone()[0]

            if not record_exists:
                # SQL statement to insert data into the table
                insert_data_sql = f"INSERT INTO cost (service, cost, date, cost_center) VALUES ('{service}', {cost}, '{result['TimePeriod']['Start']}', '{cost_center}')"

                # Execute the SQL command
                cursor.execute(insert_data_sql)

# Commit the transaction
conn.commit()

# Close the cursor and the connection
cursor.close()
conn.close()
