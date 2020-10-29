# Module to install :
#   - boto3
import boto3

nomBucket = "cloudcomputinglab3"


def secure_input(message, min_input, max_input):
    """
        Return a response between min_input and max_input
    """
    response = min_input - 1
    list_response = []
    for i in range(min_input, max_input+1):
        list_response.append(str(i))
    while response not in list_response:
        response = input(message)
    return response


def optionMessage(listOption):
    """
        Return a message with a list of options
    """
    message = "Available options\n"
    for c, v in enumerate(listOption):
        message += "   " + str(c+1) + " - " + v + "\n"
    message += "What do you want to do : "
    return message


# Lists of treatments available for numbers and image
treatmentOptionNumber = ["Sort", "Mean", "Sum", "Median", "Variance"]
treatmentOptionImage = [
    "Reverse the image (Y axis)", "Reverse the image (X axis)", "Convert in grey level", "Sauvola"]

# All the messages that will be display
messageRequestName = "\nName of the request : "
messageTypeOfRequest = "What do you want to process\n   1 - Numbers\n   2 - Image\nChoice : "
messageRequestNumber = "Type the numbers to be scanned (separated by characters) : "
messageRequestImage = "Type the path of the image : "
messageTreatmentOptionNumber = optionMessage(treatmentOptionNumber)
messageTreatmentOptionImage = optionMessage(treatmentOptionImage)

# Start the link with aws for sqs and s3
sqs = boto3.resource('sqs')
s3_client = boto3.client('s3')

# Get bask the url of the queues using their names
requestQueue = sqs.get_queue_by_name(QueueName='requestQueue')
responseQueue = sqs.get_queue_by_name(QueueName='responseQueue')

# Interaction with the user
# Numbers :
#   - requestType : 1
#   - requestValue : the list of numbers
#   - requestTreatment : choice of the operation
# Image :
#   - requestType : 2
#   - requestValue : the key of the image in s3
#   - requestTreatment : choice of the operation
requestName = input(messageRequestName)
requestType = secure_input(messageTypeOfRequest, 1, 2)
if requestType == "1":
    requestValue = input(messageRequestNumber)
    requestTreatment = secure_input(
        messageTreatmentOptionNumber, 1, len(treatmentOptionNumber))
else:
    requestPath = input(messageRequestImage)
    # The image on s3 will be in the folder Images/requestName/
    # and the name of the image is find with the end of the path
    # if the image is in a different folder
    requestValue = 'Images/' + requestName + \
        '/' + requestPath.split(sep='/')[-1]
    requestTreatment = secure_input(
        messageTreatmentOptionImage, 1, len(treatmentOptionImage))

    try:
        # Open the file and upload it on s3
        with open(requestPath, 'rb') as data:
            s3_client.upload_fileobj(data, nomBucket, requestValue)
    except FileNotFoundError:
        print()
        print("File not found. Verify the path.")
        print()
        exit()
print()

# Send message to SQS queue
requestQueue.send_message(
    MessageBody=requestName,
    MessageAttributes={
        'Type': {
            'StringValue': requestType,
            'DataType': 'String'
        },
        'Value': {
            'StringValue': requestValue,
            'DataType': 'String'
        },
        'Treatment': {
            'StringValue': requestTreatment,
            'DataType': 'String'
        }
    }
)

# Wait for a response
response = []
while not response:
    response = responseQueue.receive_messages(
        MessageAttributeNames=[
            'Type',
            'Value',
            'Treatment'
        ],
        MaxNumberOfMessages=1,
        WaitTimeSeconds=20
    )
    if not response:
        print("No response for the moment")

# Get back the information of the response
message = response[0]
resultRequestName = message.body
resultValue = message.message_attributes.get('Value').get('StringValue')

# Delete received message from the response queue
message.delete()

# Prepare the final message
requestResultMessage = "Result of the request " + \
    resultRequestName + " : " + resultValue

if requestType == "2":
    # Download the traited image from s3
    path = '/'.join(requestPath.split(sep='/')[:-1])
    if path != "":
        path += "/"
    with open(path + resultValue.split(sep='/')[-1], 'wb') as data:
        s3_client.download_fileobj(nomBucket, resultValue, data)

print()
print(requestResultMessage)
print()
print()
