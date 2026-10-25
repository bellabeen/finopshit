from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from django.db.utils import OperationalError
from .models import MasterProfile, MasterRegion, MasterCostCenter, Cost
import boto3, datetime, os


# Create your views here.
from django.http import HttpResponse

# Example usage of the fetch_aws_cost_data function
def index(request):
    cost_data = fetch_aws_cost_data()
    return JsonResponse({'cost_data': cost_data})

def fetch_aws_cost_data():
    try:
        # Search for the MasterCostCenter instance with the desired name
        cost_center_name = 'IT'  # Replace 'YourCostCenterName' with the actual name
        cost_center = MasterCostCenter.objects.get(name=cost_center_name)

        # Retrieve the AWS profile associated with the cost center
        aws_profile = cost_center.master_profile

        # Set the AWS credentials using the profile retrieved from the database
        aws_access_key_id = aws_profile.access_key
        aws_secret_access_key = aws_profile.secret_key

        # Create the AWS Cost Explorer client
        client = boto3.client('ce', region_name='ap-southeast-1', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

        # Define start and end dates
        start_date = '2024-03-01'
        end_date = '2024-04-09'

        # Fetch AWS Cost Explorer data
        try:
            # Make the AWS Cost Explorer API call
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
                        'Values': [cost_center_name]
                    }
                }
            )

            # Process the response and insert data into the database
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    date = result['TimePeriod']['Start']

                    # Insert data into the database
                    # For example, you can create a new model instance or use create method
                    # Here, I'm assuming you have a model named 'Cost' to insert the data
                    Cost.objects.create(service=service,
                     cost=cost, 
                     date=date, 
                     cost_center=cost_center)

            return {'message': 'Data inserted successfully'}
        except Exception as e:
            # Handle any errors gracefully
            error_message = f"Error fetching data for cost center '{cost_center_name}': {str(e)}"
            return {'error': error_message}

    except MasterCostCenter.DoesNotExist:
        return {'error': f"Cost center with name '{cost_center_name}' does not exist"}
    except MasterProfile.DoesNotExist:
        return {'error': f"No associated profile found for cost center '{cost_center_name}'"}
    except Exception as e:
        # Handle any exceptions and return an error message
        error_message = f"An error occurred: {str(e)}"
        return {'error': error_message}