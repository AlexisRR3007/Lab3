# Lab 3 report

## Introduction

Amazon SQS is a message queuing service and aims to simplify the access to messaging resources with a classification between them. Amazon SQS supports two types of queues: standard types and FIFO (first in first out) types.

- Standard type: the messages aren’t handled at the same order as they were sent but the number of messages handled per second is nearly unlimited. The messages are sent at least one time, but it could happen that they’re sent a few more times.

- FIFO type: the messages are strictly handled at the same order as they were sent, but the number of messages per second is limited to 300 (can be increased with a supporting demand). All the messages are sent only one time.

Amazon SQS allows the developer to code with two types of object oriented interfaces to interact with S3: the resources and the users. The user class is the lower level of the two, which means all the designated targets must be explicitly specified. The resource class provides a higher-level abstraction than the raw, low-level calls made by service clients.

A Web-Queue-Worker architecture is a way of treating demands by going through a web-front end and a worker that performs resource-intensive tasks, long-running workflows, or batch jobs. It is often used with one or more databases. In our case, the web-front end is a web API.

This architecture is consider in the following case :

- Applications with a relatively simple domain.
- Applications with some long-running workflows or batch operations.
- When you want to use managed services, rather than infrastructure as a service (IaaS).

## Client application [Sender.py](https://github.com/AlexisRR3007/Lab3/blob/main/Code/Sender.py)

### Objective

The [sender.py](https://github.com/AlexisRR3007/Lab3/blob/main/Code/Sender.py) program simulates a client interacting with one or several AWS EC2 instances, S3 buckets and SQS. Therefore, the client is directly used by the end user. It needs to be user-friendly while efficiently communicating with AWS.

### Explanations of the code :

#### Functionalities

The client able the user to work with two types of data:

- a list of integers
- an image

#### Preamble

We implement two basic functions, to ease the interaction with the user.

- `secure_input` ensure the information inputted by the user corresponds to one of the suggested option
- `optionMessage` returns a string containing every option available

#### Integer list

- `requestType = 1` indicates that we are working with a list of integers
- `requestValue` is the list of integers the user wants to work on
- `requestTreatment` is one of these options
  > ["Sort", "Mean", "Sum", "Median", "Variance"]

#### Image

- `requestType = 2` indicates that we are working with an image
- `requestValue` corresponds to the paths to the image on the S3 bucket
- `requestTreatment` is one of these options
  > ["Reverse the image (Y axis)", "Reverse the image (X axis)", "Convert in grey level", "Sauvola"]

When working with an image, the client uploads it in the "Image" directory on the S3 bucket to make it easily reachable from the EC2 instance.
If the client can't find the image, an error is displayed to the user.

#### Communicate with EC2 instances

We use two SQS (Simple Queue Service) queues to communicate between the client and the instance.

- `requestQueue` in which the client writes the data to be treated, the queue is read and cleaned by the instance
- `responseQueue` in which the instance writes the computed response, the queue is read and cleaned by the client

The structure of the message sent to the `requestQueue` is the following:

```python3
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
```

#### Receive and display information

Once the request message is sent, the client waits for the response message to be written on the responseQueue by the instance.

- if the instance worked with a list of integers, the response value is directly sent in the response message
- if the instance worked with an image, the response value contains the path to the resulted image on the S3 bucket

Therefore, the client either displays the `responseValue` or downloads the response image from the S3 bucket.\
The `responseQueue` is also cleaned for future usages and the client is terminated

## Server application [Receiver.py](https://github.com/AlexisRR3007/Lab3/blob/main/Code/Receiver.py)

### Objective

This program is to be run on a EC2 instance. It gets the request from the client from the requestQueue, treats it and sends the result back by putting it in the `responseQueue`.

### Explanations of the code :

#### Name of the bucket (line [16](https://github.com/AlexisRR3007/Lab3/blob/main/Code/Receiver.py#16))

`nomBucket = "cloudcomputinglab3"`

After the request is treated, a log file will be created and saved on a bucket chosen by the client. This line enables the client to choose the bucket where this log will be saved.\
It is also used when the request is to treat an image, as this image will be stored inside this bucket.\
When using the code, this line has to be changed accordingly.

#### Parseur function (line [19](https://github.com/AlexisRR3007/Lab3/blob/main/Code/Receiver.py#19) to 43)

This function takes a string and returns a list of integers.

When the client’s request is a treatment on numbers, he sends a string in which there are the numbers he wants to be treated, and characters to separate them. For the treatment, there so is a need to convert this string to a list of integers, and this is the reason for this function.\
First, this function removes the last character of the message until it is a digit.\
Then, it creates the list of integers by treating each characters of the message, beginning by the penultimate and going backward: if it is a digit and not the last digit of the numbers, it is added at its right place (units, digits,... with `10**place`) on the number that is already stored at the end on the list, if it is the last digit of the number, it is added at the end of the list, if it is not a digit, it is not treated.

#### TreatmentValue function (line [46](https://github.com/AlexisRR3007/Lab3/blob/main/Code/Receiver.py#46) to 117)

This function takes the `requestType` (an integer : 1 for a treatment on numbers, 2 for a treatment on a image), `requestValue` (a string: containing the numbers the client wants to be treated or the path to the image) , `requestTreatment` (an integer: the treatment that is to be applied to the requestValue), `requestName` (a string with the name of the request) and `s3_client` (the link with aws to the s3 client) and return a string with the values treated.

If the request is on numbers, they are first transferred to a list of integers thanks to the function `parseur`, then the treatment asked is applied (1: the numbers are sorted; 2: returns the mean of those numbers; 3: sums up all the numbers; 4: return the median; 5: return the vairance). The library `statistics` is used to do the statistical treatments (mean, sum, median, variance). After the treatment, the result is converted to a string and stored in requestResponse.

If the request is a treatment on an image, the function gets it back from the s3 and stores it in `temp` with the `download_fileobject` function. The functions `imread` and `astype` from the library `imageio` are used to open the image stored in `temp` to `im` as a float. The extension of the image is also stored in a variable called ‘extension’ for when the image after treatment will have to be saved. Then the image is treated accordingly to what the client wanted:

1. the image is reversed by the Y axis using the `flip` function from the `numpy` library.
2. the image is reversed by the X axis using the `flip` function from the `numpy` library.
3. the image is converted in grey level by multiplicating the matrix containing the image to the [0.2989, 0.5870, 0.1140] vector using the function `dot` from the `numpy` library. An image is colored if it uses 3 channels to describe each pixel (red, green, blue). To convert it in grey level, it needs to calculate a grey value according to those 3 channels, instead of average the three, it is more accurate to ponder each channel by a value (0.2989 for the red, etc.) depending on how much information they convey. The values chosen here are the traditional values used when converting an image to grey.
4. it uses the Sauvola algorithm to apply a filter to the image by using the `sauvola` function. The Sauvola algorithm is a binarization algorithm: it converts a pixel image to a binary image (only black and white). Before calling the `sauvola` function, the image is converted to grey level. The Sauvola algorithm can, for example, be used on an image with text to put the text in black and the rest in white (the parameters are chosen so that this is what happens here)

Then the image after its treatment is saved in the `im.extension` file under the format of an array of integers with the `imwrite` function from the `imageio` library. In the bucket, the image after treatment will have the same name with an ‘\_treated’ before the .extension. This name is saved in the `requestReturn` variable. The image after treatment is saved on the bucket with the `upload_fileobject` function. Finally, the temporary files (‘temp’, ‘im’.extension) are deleted with the `remove`function from the `os` library.

#### Receive the request and send the result (line [120](https://github.com/AlexisRR3007/Lab3/blob/main/Code/Receiver.py#120) to 215)

The `requestQueue` and `responseQueue` are created in the _receiver.py_ script. For the _sender.py_ script to work, it so has to be executed after the _receiver.py_ script. We decided for this order as it seemed more natural for the client to only get queues as it will only be used when there is a need for a request, and to create those in the receiver (and to execute him first). For both queues, it was decided to not delay the delivery message in the queue, to not wait to take actions when a message is received and to put the visibility timeout to 10 seconds.\
Every 20 seconds, the script looks whether a message has been written on the requestQueue, if not it will display a message saying it is waiting for a request and the way to exit is ‘ctrl + c’ as it is the command to abort a script.

When there is a message on the `requestQueue`, its information (the name of the request, the type of the request, the values that are to be treated and the treatment wanted) are stored and the message is deleted from the queue so it will be treated only once. The treatment is then done with the function `treatmentValue`. The result is finally transmitted to the client by putting it on the `responseQueue` with the `sendmessage` function. As for the message in the `requestQueue`, the body of the message is the name of the request, the attributes added are the type which corresponds to the `Type` of the request (1 for integer, 2 for image), the `Value` where the result is stored and the `Treatment` which is the treatment wanted by the client.

#### Creating the log (line [217](https://github.com/AlexisRR3007/Lab3/blob/main/Code/Receiver.py#217) to 239)

After the request is done and the result is sent to the client by the `responseQueue`, a log is created which contains information about the request and its treatment. Each log contains the name of the request, the treatment that was needed, the values that were to be treated, the result of the treatment and the date of the request (using the `asctime()` function from the `time` library). Each log is called with the name of the request. They are stored in a file named ‘Logs’ on the bucket, to make them easier to find when needed.
