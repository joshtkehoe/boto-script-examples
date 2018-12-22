import boto3
import argparse
import base64
import uuid
import os
import json

#
# This utility can be used in the following ways.
# 1. Generate random messages on a SQS queue.
# 2. Pull a specified amount of messages (or all messages) from a queue and save off the message body and attributes
#    in a text file.
# 3. Restore messages from the text files back as new SQS messages onto the same queue, or a different queue.
# Usage:
# To run locally, you can run from the IDE or by running python from the command line or bash window. It is assumed
# that you have valid AWS API credentials in your .aws directory and your user/role has list/retrieve/delete SQS
# access.
#
# The parameters to pass in are as follows:
#    1. The SQS queue name to process from or to. The queue must exist in your AWS account.
#    2. The number of random SQS messages to generate. This parameter is not considered if the mode parameter is not
#       'G'.
#    3. The number of messages to process (save or restore). This parameter is only used if mode is 'S' or 'R'. To
#       process all messages, put in 'ALL'.
#    4. The path to your input or output directory. This parameter is only used if mode is 'S' or 'R'. Make sure
#       to take consideration which OS you are running this on. For best results, use a directory that already exists.
#       The script will attempt to create the directory if it does not exist, but it will not work if the directory is
#       nested.
#
#


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("sqs_queue_name")
    parser.add_argument("gen_random_msgs", help="Generate random sqs messages. 0 for none.")
    parser.add_argument("num_msgs", help="Number of messages to save or restore (depending on mode). Use 'ALL' for all.")
    parser.add_argument("mode", help="S = Poll and save messages to disk. "
                                     "R = Restore from disk to SQS. "
                                     "G = Generate random messages.")
    parser.add_argument("path", help="OS Specific input or output path")
    parser.add_argument("--region", help="The AWS region to use", default="us-east-1")
    parser.add_argument("--verbosity", help="increase output verbosity")
    args = parser.parse_args()
    verbose = False
    if args.verbosity:
        print "Verbosity turned on"
        verbose = True
    return args.sqs_queue_name, args.gen_random_msgs, args.num_msgs, args.mode, args.path, args.region, verbose


def _put_random_msgs_on_queue(queue_name, msgs_to_generate, aws_region):
    sqs = boto3.resource('sqs', region_name=aws_region)
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    for x in range(int(msgs_to_generate)):
        rnd_uuid = uuid.uuid4()
        response = queue.send_message(MessageBody=base64.encodestring('Hello World {}'.format(str(rnd_uuid))))
        print("Added {}".format(response.get('MessageId')))


def _put_messages_back_on_sqs(queue_name, num_msgs_to_restore, input_dir, aws_region):
    sqs = boto3.resource('sqs', region_name=aws_region)
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    dir_files = os.listdir(input_dir)
    dir_files.sort()
    counter = 0
    for filename in dir_files:
        with open(os.path.join(input_dir, filename)) as f:
            try:
                msg = json.load(f)
                queue.send_message(MessageBody=msg['body'])
                print("Sent message: {}".format(filename))
            except:
                print("Something bad happened. Exiting.")
                exit(1)
        os.remove(os.path.join(input_dir, filename))
        counter = counter + 1
        if counter >= int(num_msgs_to_restore):
            print ("Number of messages met. Exiting.")
            break


def _poll_sqs_and_save_msgs(queue_name, num_msgs_to_save, output_dir, aws_region):
    sqs = boto3.resource('sqs', region_name=aws_region)
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    counter = 0
    while True:
        if counter >= int(num_msgs_to_save):
            print ("Number of messages met. Exiting.")
            break

        messages = queue.receive_messages(MaxNumberOfMessages=10, AttributeNames=['All'])
        if len(messages) == 0:
            break

        for message in messages:
            filename = os.path.join(output_dir, str(counter).rjust(7, '0') + "_" + message.message_id)
            counter = counter + 1
            obj = {'id': message.message_id, 'attributes': message.message_attributes, 'body': message.body}
            print("Writing file to disk {}".format(message.message_id))
            with open(filename, 'w') as f:
                json.dump(obj, f, indent=2)
            message.delete()
            if counter >= int(num_msgs_to_save):
                break


if __name__ == '__main__':
    sqs_queue, random_msgs_to_generate, num_msgs, mode, path, region, verbosity = _parse_args()

    if num_msgs == "ALL":
        num_msgs = 1000000

    if (mode == "S" or mode == "R") and not os.path.isdir(path):
        print "Message directory does not exist. Creating."
        try:
            os.mkdir(path)
        except OSError:
            print("Creation of the output directory failed")
        else:
            print("Successfully created the output directory")

    if int(random_msgs_to_generate) > 0 and mode == "G":
        print "Put random messages on queue: {}".format(sqs_queue)
        _put_random_msgs_on_queue(sqs_queue, random_msgs_to_generate, region)

    if int(num_msgs > 0) and mode == "S":
        print "Polling SQS queue and saving to disk: {}".format(sqs_queue)
        _poll_sqs_and_save_msgs(sqs_queue, num_msgs, path, region)

    if int(num_msgs > 0) and mode == "R":
        print "Restoring messages from disk to queue: {}".format(sqs_queue)
        _put_messages_back_on_sqs(sqs_queue, num_msgs, path, region)

    print "Done!"
    exit(0)
