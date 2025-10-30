#!/usr/bin/env python3
"""
Script to help set up IAM Role for Redshift COPY operations
This script will guide you through creating the necessary IAM role
"""

import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

def get_aws_account_id():
    """Get the AWS account ID"""
    try:
        sts = boto3.client('sts',
                          aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                          aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                          region_name=os.getenv('AWS_REGION'))
        identity = sts.get_caller_identity()
        return identity['Account']
    except Exception as e:
        print(f"❌ Error getting AWS account ID: {e}")
        return None


def create_iam_role():
    """Create IAM role for Redshift with S3 access"""
    
    print("="*70)
    print("🔐 IAM Role Setup for Redshift COPY Operations")
    print("="*70)
    print()
    
    # Get AWS account ID
    print("📋 Getting AWS Account ID...")
    account_id = get_aws_account_id()
    
    if not account_id:
        print("\n⚠️  Could not retrieve AWS account ID.")
        print("Please check your AWS credentials in .env file")
        return None
    
    print(f"✅ AWS Account ID: {account_id}")
    print()
    
    # IAM role name
    role_name = "RedshiftS3CopyRole"
    
    # Trust policy for Redshift
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "redshift.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # S3 access policy
    s3_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{os.getenv('S3_BUCKET_NAME')}",
                    f"arn:aws:s3:::{os.getenv('S3_BUCKET_NAME')}/*"
                ]
            }
        ]
    }
    
    try:
        iam = boto3.client('iam',
                          aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                          aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                          region_name=os.getenv('AWS_REGION'))
        
        print(f"🔧 Creating IAM Role: {role_name}...")
        
        # Try to create the role
        try:
            role = iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Role for Redshift to access S3 for COPY operations'
            )
            print(f"✅ Role created successfully!")
            role_arn = role['Role']['Arn']
            
        except iam.exceptions.EntityAlreadyExistsException:
            print(f"ℹ️  Role already exists, retrieving ARN...")
            role = iam.get_role(RoleName=role_name)
            role_arn = role['Role']['Arn']
        
        # Attach S3 access policy
        policy_name = "RedshiftS3AccessPolicy"
        print(f"\n📎 Attaching S3 access policy: {policy_name}...")
        
        try:
            iam.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(s3_policy)
            )
            print(f"✅ Policy attached successfully!")
        except Exception as e:
            print(f"⚠️  Policy attachment: {e}")
        
        print("\n" + "="*70)
        print("✅ IAM Role Setup Complete!")
        print("="*70)
        print(f"\n📋 Your IAM Role ARN:")
        print(f"   {role_arn}")
        print(f"\n📝 Add this to your .env file:")
        print(f"   REDSHIFT_IAM_ROLE={role_arn}")
        print("\n" + "="*70)
        
        return role_arn
        
    except Exception as e:
        print(f"\n❌ Error creating IAM role: {e}")
        print("\n🔧 Manual Setup Instructions:")
        print_manual_instructions(account_id)
        return None


def print_manual_instructions(account_id):
    """Print manual setup instructions"""
    print("\n" + "="*70)
    print("📖 Manual IAM Role Setup Instructions")
    print("="*70)
    print("""
1. Go to AWS Console → IAM → Roles → Create Role

2. Select "AWS Service" → "Redshift" → "Redshift - Customizable"

3. Attach the following managed policy:
   ✓ AmazonS3ReadOnlyAccess
   
   OR create a custom policy with this JSON:
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "s3:GetObject",
                   "s3:GetObjectVersion",
                   "s3:ListBucket"
               ],
               "Resource": [
                   "arn:aws:s3:::YOUR_BUCKET_NAME",
                   "arn:aws:s3:::YOUR_BUCKET_NAME/*"
               ]
           }
       ]
   }

4. Name the role: RedshiftS3CopyRole

5. After creation, copy the Role ARN (format):
   arn:aws:iam::ACCOUNT_ID:role/RedshiftS3CopyRole

6. Attach the role to your Redshift cluster:
   - Go to Redshift Console
   - Select your cluster
   - Actions → Manage IAM roles
   - Add the role you created

7. Add to .env file:
   REDSHIFT_IAM_ROLE=arn:aws:iam::ACCOUNT_ID:role/RedshiftS3CopyRole
""")
    
    if account_id:
        print(f"\n💡 Your Account ID: {account_id}")
        print(f"   Your Role ARN will be: arn:aws:iam::{account_id}:role/RedshiftS3CopyRole")
    
    print("="*70)


def check_redshift_role_attachment():
    """Check if IAM role is attached to Redshift cluster"""
    print("\n🔍 Checking Redshift cluster configuration...")
    
    try:
        redshift = boto3.client('redshift',
                               aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                               aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                               region_name=os.getenv('AWS_REGION'))
        
        # Get cluster identifier from host
        host = os.getenv('REDSHIFT_HOST', '')
        cluster_id = host.split('.')[0] if '.' in host else None
        
        if not cluster_id:
            print("⚠️  Could not determine cluster ID from REDSHIFT_HOST")
            return
        
        print(f"📊 Cluster ID: {cluster_id}")
        
        # Get cluster info
        response = redshift.describe_clusters(ClusterIdentifier=cluster_id)
        cluster = response['Clusters'][0]
        
        iam_roles = cluster.get('IamRoles', [])
        
        if iam_roles:
            print(f"\n✅ IAM Roles attached to cluster:")
            for role in iam_roles:
                print(f"   - {role['IamRoleArn']} (Status: {role['ApplyStatus']})")
        else:
            print("\n⚠️  No IAM roles attached to Redshift cluster")
            print("   You need to attach the role manually:")
            print("   1. Go to Redshift Console")
            print("   2. Select your cluster")
            print("   3. Actions → Manage IAM roles")
            print("   4. Add the RedshiftS3CopyRole")
        
    except Exception as e:
        print(f"⚠️  Could not check cluster: {e}")


if __name__ == "__main__":
    # Validate environment
    required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION', 'S3_BUCKET_NAME']
    missing = [v for v in required_vars if not os.getenv(v)]
    
    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        print("Please check your .env file")
        exit(1)
    
    # Create IAM role
    role_arn = create_iam_role()
    
    if role_arn:
        # Check if role is attached to Redshift
        check_redshift_role_attachment()
        
        print("\n" + "="*70)
        print("🎯 Next Steps:")
        print("="*70)
        print(f"""
1. Add to your .env file:
   REDSHIFT_IAM_ROLE={role_arn}

2. Ensure the role is attached to your Redshift cluster:
   - AWS Console → Redshift → Your Cluster
   - Actions → Manage IAM roles → Attach the role

3. Run your pipeline:
   poetry run python my_pipeline.py
""")
        print("="*70)
