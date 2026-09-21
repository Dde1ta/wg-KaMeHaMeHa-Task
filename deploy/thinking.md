## What is this doing

This script is making it so that the data flow task can be deployed
in any account from the start, and can make managing it easier.

## Things I am making

1. Template Buckets := 1 in us-west-2 and 1 in ap-south-1
2. Stacks := Some in us-west-2 and some in ap-south-1

### What are the things doing

#### Template Bucket
    
1. Check if the account has the bucket
   1. If not make it -> using a basic template.
   2. If it has load the properties.

2. Check the templates given
   1. maintain a dictionary of template -> url.
   2. upload the templates to S3.

3. Give the Template URL to the stacks
   1. Use the dictionary :D

#### Stacks

1. Check if the account has a stack with the same name
   1. if so use ` DescribeStacks ` to fill in parameters, outputs.
   2. if not wait.

2. detect drift.

3. make changes sets.

4. run stacks.

### Classes and Methods

#### Template Bucket

```python
class TemplateBucket:
    bucket_name=""
    templates={}
    bucket_template=""  # this will be sent in place to cfn in the make_bucket in create stack call
    
    def __init__(self, s3_client, bucket_name: str):
        ...
    
    def get_template_url(self, template_path: str) -> str:
        ...
    
    def upload_templates(self, **template_paths: list[str]) -> None:
        ...
    
    def make_bucket(self):
        ...
```

#### Stack

```python

class Stack:
    stack_name=""
    template_url=""
    parameters={}
    outputs={}
    
    
    def __init__(self, cfn_client, stack_name):
        ...
    
    def check_stack_exists(self) -> bool:
        ...
    
    def set_parameters(self, parameters: dict):
        ...
    
    def get_outputs(self) -> dict:
        ...
    
    def get_from_output(self, key_name) -> str:
        ...
    
    def start_stack_creation(self) -> str:
        ...
    
    def start_change_set(self) -> str:
        ...
    
    def execute_change_set(self, change_set_id: str) -> str:
        ...

    # def get_event_details(self, operation_id, next_token: None):
    #     ...
```

#### Utils.Screen

```python

class Screen:
    
    layers: {} # layer_name: layer_content
    layer_order = [] # layer_order
    
    def __init__(self):
        ...
    
    def add_layer(self, layer_name: str):
        ...
    
    def set_layer_content(self, layer_name: str, layer_content: str):
        ...
    
    def print_to_screen(self):
        ...
    
    def clear_screen(self):
        ...
    
    def change_layer_order(self, layers: list, *layer_order):
        ...
    
    def move_up(self, layer_name):
        ...
    
    def move_down(self, layer_name):
        ...
```

## Actions

### Bootstrap

1. Load / Create Template bucket
2. Upload Templates

### First - Deploy 
1. Check if already Deployed (For all the templates)
2. Start KMS in us-west-2
3. Start KMS Replica in ap-south-1
4. Make IAM Roles
5. Make us-west-2 resources
6. Make ap-south-1 resources
7. Add replication rule to us-west-2 bucket
8. Add initial object

### Update 
1. Check if already Deployed
2. If deployed start drift aware change sets
3. Start if needed

### Tear Down
1. Empty both buckets.
2. Check bucket and empty them again.
3. Start deletion.

## Core Flow

1. Bootstrap
2. Follow Flow 
   1. KMS
   2. IAM
   3. US-West-2
   4. AP-South-1
3. If stack not found run deploy
4. if stack found run Update
5. If global teardown -- Teardown.

## Errors

### Why

I will raise these error in the class's method. That will tell me what the situation is
I will handel them in the main script.

### What

1. ` StackDoesNotExist `
   - "Deploy" the stack.
   
2. ` StackCreationFailed `
   - Start the complete rollback.

3. ` StackNotChanged `
   - Skip The stack in the update chain.

4. ` StackUpdateFailed `
   - is difficult.

5. ` TemplateUploadFailed `
   - stop everything and exit.
   
6. ` TemplateBucketNotFound `
   - create bucket.

7. ` TemplateNotFound `
   - check local again, stop script if not found.
   - if found upload.
