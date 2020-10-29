# Modules to install :
#   - boto3
#   - numpy
#   - imageio

import Sauvola as sv
import numpy as np
import imageio
import statistics as st
import time
import os
from botocore.exceptions import ClientError
import logging
import boto3

nomBucket = "cloudcomputinglab3"


def parseur(messageStr):
    """
        Parseur which return a list of int from a string with numbers
    """
    numberStr = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    lenMessage = len(messageStr)

    # Remove spaces at the beginning and end of the message
    while (messageStr[-1] not in numberStr):
        messageStr = messageStr[0:lenMessage-1]
        lenMessage -= 1

    # Create the list of int
    listOfNumber, place = [int(messageStr[lenMessage-1])], 0
    for i in range(lenMessage-2, -1, -1):
        if messageStr[i] in numberStr:
            if messageStr[i+1] in numberStr:
                place += 1
                listOfNumber[-1] += (10**place) * int(messageStr[i])
            else:
                listOfNumber.append(int(messageStr[i]))
        else:
            place = 0

    return listOfNumber


def treatmentValue(requestType, requestValue, requestTreatment, requestName, s3_client):
    """
        Treat the value
    """
    requestReturn = ""

    if requestType == "1":
        # Transform the string into int list
        requestValue = parseur(requestValue)

        # Treatments
        if requestTreatment == "1":
            requestValue.sort()
        elif requestTreatment == "2":
            requestValue = [st.mean(requestValue)]
        elif requestTreatment == "3":
            requestValue = [st._sum(requestValue)[1]]
        elif requestTreatment == "4":
            requestValue = [st.median(requestValue)]
        elif requestTreatment == "5":
            requestValue = [st.variance(requestValue)]

        # Create a new string with the new list
        for i in requestValue:
            requestReturn = requestReturn + str(i) + " "
    else:
        # Get back the image from s3 and stock it in temp
        with open('temp', 'wb') as data:
            s3_client.download_fileobj(nomBucket, requestValue, data)

        # Open the image
        im = imageio.imread('temp').astype(float)

        # Get back the extension of the image
        extension = requestValue.split(sep='.')[-1]

        # Treatments
        if requestTreatment == "1":
            im = np.flip(im, axis=1)
        elif requestTreatment == "2":
            im = np.flip(im, axis=0)
        elif requestTreatment == "3":
            if len(im.shape) == 3:
                im = np.dot(im[..., :3], [0.2989, 0.5870, 0.1140])
        elif requestTreatment == "4":
            if len(im.shape) == 3:
                im = np.dot(im[..., :3], [0.2989, 0.5870, 0.1140])
            taille_filtre = 15         # Taille du filtre lors de l'algo de Sauvola
            R = 128                    # Paramètre R de l'algo de Sauvola
            k = 0.2                    # Paramètre k de l'algo de Sauvola
            n = 3                      # Distance entre deux pixels où on apllique Sauvola
            # Type d'interpolation si n!=1 (1 : moyennes simples, 2 : moyennes pondérées)
            type_inter = 2
            im = sv.sauvola(im, k, R, n, taille_filtre, type_inter)

        # Write the new image
        imageio.imwrite('im.' + extension, im.astype(np.uint8))

        # Create the key of the traited image for s3
        requestReturn = requestValue.split(sep='.')
        requestReturn.insert(-1, '_traited.')
        requestReturn = ''.join(requestReturn)

        # Upload the traited image in s3
        with open('im.' + extension, 'rb') as data:
            s3_client.upload_fileobj(data, nomBucket, requestReturn)

        # Delete local files
        os.remove('temp')
        os.remove('im.' + extension)

    return requestReturn


# Clean the window before starting
os.system('clear')

# Start the link with aws for sqs and s3
sqs = boto3.resource('sqs')
s3_client = boto3.client('s3')

# Create the two queues use by the programs
requestQueue = sqs.create_queue(
    QueueName='requestQueue',
    Attributes={
        # Time, in seconds, for which the delivery of all messages in the queue is delayed
        'DelaySeconds': '0',
        # Time, in seconds, for which a `` ReceiveMessage `` action waits for a message to arrive
        'ReceiveMessageWaitTimeSeconds': '0',
        # The visibility timeout for the queue, in seconds.
        'VisibilityTimeout': '10'
    }
)
responseQueue = sqs.create_queue(
    QueueName='responseQueue',
    Attributes={
        'DelaySeconds': '0',
        'ReceiveMessageWaitTimeSeconds': '0',
        'VisibilityTimeout': '10'
    }
)

print()
print("---Serveur operationel---")

# The server will always wait for messages
while True:
    response = []
    while not response:
        response = requestQueue.receive_messages(
            MessageAttributeNames=[
                'Type',
                'Value',
                'Treatment'
            ],
            MaxNumberOfMessages=1,
            # The duration (in seconds) for which the call waits for a message to arrive in the queue before returning.
            WaitTimeSeconds=20
        )
        if not response:
            print("Wait for a message to treat (Leave : ctrl+c)")

    # Get back the information of the response
    # Numbers :
    #   - requestType : 1
    #   - requestValue : the list of numbers
    #   - requestTreatment : choice of the operation
    # Image :
    #   - requestType : 2
    #   - requestValue : the key of the image in s3
    #   - requestTreatment : choice of the operation
    message = response[0]
    requestName = message.body
    requestType = message.message_attributes.get(
        'Type').get('StringValue')
    requestValue = message.message_attributes.get(
        'Value').get('StringValue')
    requestTreatment = message.message_attributes.get(
        'Treatment').get('StringValue')

    # Delete received message from the request queue
    message.delete()

    print("Working on the request",
          requestName, "|", end=" ", flush=True)

    # Treat the data
    requestResult = treatmentValue(
        requestType, requestValue, requestTreatment, requestName, s3_client)

    # Send request result to SQS response queue
    response = responseQueue.send_message(
        MessageBody=requestName,
        MessageAttributes={
            'Type': {
                'StringValue': requestType,
                'DataType': 'String'
            },
            'Value': {
                'StringValue': requestResult,
                'DataType': 'String'
            },
            'Treatment': {
                'StringValue': requestTreatment,
                'DataType': 'String'
            }
        }
    )

    print("Request done")

    # Create the content of the log file
    messageFile = "Name of the request : " + requestName + \
        "\nType of treatment : " + requestType + \
        "\nValues to treat : " + requestValue + \
        "\nValues treated : " + requestResult + \
        "\nDate of the treatment : " + time.asctime()

    # Create the name of the log file
    nameFichier = "Log_" + requestName + ".txt"

    # Create the log file
    with open(nameFichier, "w") as fichier:
        fichier.write(messageFile)

    # Put the log file on s3
    try:
        s3_client.upload_file(
            nameFichier, nomBucket, "Logs/"+nameFichier)
    except ClientError as e:
        logging.error(e)

    # Delete the log file from the server
    os.remove(nameFichier)
