from typing import List
from ..exceptions.template import *
from botocore.exceptions import ClientError
import boto3


class Templates:

    def __init__(self, s3_client, bucket_name: str | None = None):

        self.client = s3_client
        self.region = self.client.meta.region_name
        self.templates = {}
        self.zips = {}

        self.bucket_name = bucket_name

    def get_template_url(self, template_path: str) -> str | None:

        template_url = self.templates.get(template_path, None)

        if template_url is None:
            raise TemplateNotFound(f"Not template with path {template_path}")

        return template_url

    def upload_templates(self, *template_paths: str):  # Make for lambda also here.
        if self.bucket_name is None:
            raise TemplateBucketNotFound("Set Template Bucket")
        for template in template_paths:
            try:
                print(f"Opening: {template}")
                with open(template) as template_file:
                    print(f"put_object: {template}")
                    self.client.put_object(
                        Bucket=self.bucket_name,
                        Body=template_file.read().encode("utf-8"),
                        Key=template
                    )

                self.templates[template] = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{template}"

            except ClientError as e:
                print(e)
                raise TemplateException(f"An error occurred during template upload operation")

    def set_template_bucket(self, bucket_name: str):
        self.bucket_name = bucket_name

    def upload_lambda_zips(self, *zips_paths):
        if self.bucket_name is None:
            raise TemplateBucketNotFound("Set Template Bucket")
        try:

            for path in zips_paths:
                with open(path, "rb") as f:
                    self.client.put_object(
                        Bucket=self.bucket_name,
                        Body=f,
                        Key=path
                    )

                    self.zips[path] = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{path}"

        except ClientError as e:
            print(e)
            raise TemplateException(f"An error occurred during template upload operation")

    def get_zip_url(self, zip_path: str) -> str | None:
        template_url = self.templates.get(zip_path, None)

        if template_url is None:
            raise ZipNotFound(f"Not template with path {zip_path}")

        return template_url

# if __name__ == "__main__":
#
#     s3_client = boto3.client("s3")
#
#     try:
#
#         test = Templates(s3_client=s3_client, bucket_name="cloudformation-ap-south-1-templates")
#
#     except TemplateBucketAlreadyExists as a:
#         print("success")
