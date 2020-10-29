# Python Image modifier/List analyser Program

An ec2 server which treat lists of numbers and images along with the corresponding client

## Installation

- Clone the repository

- Create a credentials file and a config file on your computer and in the ec2 machine with the paths :

  /home/UserName/.aws/credentials  
   /home/UserName/.aws/config

- Write the following in credentials:

  ```
  [default]
  aws_access_key= THE_KEY
  aws_secret_access_key= THE_KEY
  aws_sessions_token= THE_SESSION_TOKEN
  ```

- Write the following in config:

  ```
  [default]
  region= REGION_OF_EC2
  output= json
  ```

- Create a bucket with the name you want

- Modify [line 5](https://github.com/AlexisRR3007/Lab3/blob/main/Code/Sender.py#L5) of Sender.py to match the name of the bucket to the one you created

- Modify [line 16](https://github.com/AlexisRR3007/Lab3/tree/main/Code/Receiver.py#L16) of Receiver.py to match the name of the bucket to the one you created

- Connect to the ec2 instance and write in the bash :

  - To install python3

  ```bash
  sudo yum install python3
  ```

  - To install the required libraries:

  ```bash
  sudo pip3 install boto3
  sudo pip3 install imageio
  sudo pip3 install numpy
  ```

- Put Receiver.py in the ec2 instance

## Usage

- Start Receiver.py in the ec2 instance

```bash
python3 Receiver.py
```

- Start Sender.py from your computer bash

```bash
python3 Sender.py
```

- Follow the instructions to start treating number lists and images
