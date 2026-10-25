from django.db import models
import boto3

# Create your models here.

class MasterProfile(models.Model):
    profile_name = models.CharField(max_length=50)
    access_key = models.CharField( max_length=50)
    secret_key = models.CharField(max_length=50)
    output = models.CharField(max_length=10, default='json')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Cost(models.Model):
    service_name = models.CharField(max_length=50)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    cost_center = models.CharField(max_length=10)
    # cost_center = models.ForeignKey('MasterCostCenter', on_delete=models.CASCADE)

class MasterRegion(models.Model):
    region_name = models.CharField(max_length=50)

class MasterCostCenter(models.Model):
    name = models.CharField(max_length=50)
    master_profile = models.ForeignKey(MasterProfile, on_delete=models.CASCADE)