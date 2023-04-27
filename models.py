from flask_login import UserMixin
from datetime import datetime
import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import uuid

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

class User(UserMixin):
    def __init__(self, username, password, tokens=200, id=None, created_at=None):
        self.id = str(uuid.uuid4()) if id is None else id
        self.username = username
        self.password = password
        self.tokens = tokens
        self.created_at = created_at

    @staticmethod
    def get(id):
        table = dynamodb.Table('Users')
        try:
            response = table.get_item(Key={'id': id})
        except ClientError as e:
            print(e.response['Error']['Message'])
            return None
        else:
            return User(**response['Item']) if 'Item' in response else None

    @staticmethod
    def get_by_username(username):
        table = dynamodb.Table('Users')
        try:
            response = table.query(
                IndexName='username-index',
                KeyConditionExpression=Key('username').eq(username)
            )
            print("Response:", response)  # Add this print statement
        except ClientError as e:
            print(e.response['Error']['Message'])
            return None
        else:
            return User(**response['Items'][0]) if response['Items'] else None

    def save(self):
        table = dynamodb.Table('Users')
        item = self.__dict__
        item['created_at'] = item['created_at'].strftime('%Y-%m-%dT%H:%M:%S.%f')
        table.put_item(Item=item)


    def update(self, new_attributes):
        table = dynamodb.Table('Users')
        table.update_item(
            Key={'id': self.id},
            UpdateExpression='SET tokens = :t',
            ExpressionAttributeValues={':t': new_attributes['tokens']}
        )
        self.tokens = new_attributes['tokens']


class VisualNovel:
    def __init__(self, title, dialogues, created_dt, user_id, cover_image_bucket=None, cover_image_key=None, private=False, location="Unknown", ip_address=None, user_agent=None, id=None, **kwargs):
        self.id = str(uuid.uuid4()) if id is None else id
        self.title = title
        self.private = private
        self.dialogues = dialogues
        self.user_id = user_id
        self.created_dt = created_dt
        self.user_agent = user_agent
        self.ip_address = ip_address
        self.location = location
        self.cover_image_bucket = cover_image_bucket
        self.cover_image_key = cover_image_key

    @staticmethod
    def get(id):
        table = dynamodb.Table('VisualNovels')
        try:
            response = table.get_item(Key={'id': id})
        except ClientError as e:
            print(e.response['Error']['Message'])
            return None
        else:
            return VisualNovel(**response['Item']) if 'Item' in response else None

    @staticmethod
    def get_all_by_user_id(user_id):
        table = dynamodb.Table('VisualNovels')
        try:
            response = table.query(
                IndexName='user_id-index',
                KeyConditionExpression=Key('user_id').eq(user_id)
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
            return None
        else:
            print("response['Items']:", response['Items'])  # Add this print statement
            return [VisualNovel(**item) for item in response['Items']]

    def save(self):
        table = dynamodb.Table('VisualNovels')
        item = self.__dict__
        item['created_dt'] = item['created_dt'].strftime('%Y-%m-%dT%H:%M:%S.%f')
        table.put_item(Item=item)


    def update(self, new_attributes):
        table = dynamodb.Table('VisualNovels')
        expression = ', '.join([f"#{key} = :{key}" for key in new_attributes])
        attribute_names = {f"#{key}": key for key in new_attributes}
        attribute_values = {f":{key}": value for key, value in new_attributes.items()}
        table.update_item(
            Key={'id': self.id},
            UpdateExpression=f"SET {expression}",
            ExpressionAttributeNames=attribute_names,
            ExpressionAttributeValues=attribute_values
        )
        for key, value in new_attributes.items():
            setattr(self, key, value)


    @staticmethod
    def get_all_public():
        table = dynamodb.Table('VisualNovels')
        try:
            response = table.scan(
                FilterExpression=Attr('private').eq(False)
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
            return None
        else:
            return [VisualNovel(**item) for item in response['Items']] if response['Items'] else []


