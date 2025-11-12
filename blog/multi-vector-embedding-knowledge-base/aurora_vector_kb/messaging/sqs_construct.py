"""
SQS Queue Construct for Aurora Vector Knowledge Base

This construct creates the SQS infrastructure for document ingestion processing,
including the main queue, dead letter queue, and CloudWatch monitoring.
"""

from typing import Any
import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (
    Duration,
    aws_sqs as sqs,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    CfnOutput
)


class SqsConstruct(Construct):
    """
    SQS Queue Construct for document ingestion processing
    
    Creates:
    - Main ingestion queue with configured timeouts and retention
    - Dead letter queue for failed message handling
    - CloudWatch alarms for queue monitoring
    - SNS topic for alarm notifications
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create SNS topic for alarm notifications
        self.alarm_topic = sns.Topic(
            self,
            "IngestionQueueAlarmTopic",
            display_name="Aurora Vector KB - Ingestion Queue Alarms",
            topic_name="aurora-vector-kb-ingestion-alarms"
        )

        # Create dead letter queue first
        self.dead_letter_queue = sqs.Queue(
            self,
            "IngestionDeadLetterQueue",
            queue_name="aurora-vector-kb-ingestion-dlq",
            # Dead letter queue message retention: 14 days
            retention_period=Duration.days(14),
            # Enable server-side encryption
            encryption=sqs.QueueEncryption.SQS_MANAGED,
            # Remove queue when stack is deleted (for dev environments)
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        # Create main ingestion queue
        self.ingestion_queue = sqs.Queue(
            self,
            "IngestionQueue",
            queue_name="aurora-vector-kb-ingestion-queue",
            # Visibility timeout matches Lambda timeout (15 minutes)
            visibility_timeout=Duration.minutes(15),
            # Message retention: 14 days
            retention_period=Duration.days(14),
            # Dead letter queue configuration
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,  # 3 attempts before moving to DLQ
                queue=self.dead_letter_queue
            ),
            # Enable server-side encryption
            encryption=sqs.QueueEncryption.SQS_MANAGED,
            # Remove queue when stack is deleted (for dev environments)
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        # Create CloudWatch alarms for queue monitoring
        self._create_cloudwatch_alarms()

        # Add stack outputs
        CfnOutput(
            scope,
            "IngestionQueueUrl",
            value=self.ingestion_queue.queue_url,
            description="URL of the main ingestion SQS queue"
        )

        CfnOutput(
            scope,
            "IngestionQueueArn",
            value=self.ingestion_queue.queue_arn,
            description="ARN of the main ingestion SQS queue"
        )

        CfnOutput(
            scope,
            "DeadLetterQueueUrl",
            value=self.dead_letter_queue.queue_url,
            description="URL of the ingestion dead letter queue"
        )

        CfnOutput(
            scope,
            "DeadLetterQueueArn",
            value=self.dead_letter_queue.queue_arn,
            description="ARN of the ingestion dead letter queue"
        )

        CfnOutput(
            scope,
            "AlarmTopicArn",
            value=self.alarm_topic.topic_arn,
            description="SNS topic ARN for queue monitoring alarms"
        )

    def _create_cloudwatch_alarms(self) -> None:
        """
        Create CloudWatch alarms for SQS queue monitoring
        
        Monitors:
        - Messages in dead letter queue (critical)
        - Queue depth (high message count)
        - Message age (messages stuck in queue)
        - Queue processing rate
        """

        # Alarm for messages in dead letter queue (critical)
        dead_letter_alarm = cloudwatch.Alarm(
            self,
            "DeadLetterQueueMessagesAlarm",
            alarm_name="aurora-vector-kb-dlq-messages",
            alarm_description="Alert when messages appear in the dead letter queue",
            metric=self.dead_letter_queue.metric("ApproximateNumberOfVisibleMessages",
                period=Duration.minutes(5),
                statistic="Sum"
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )

        # Add SNS notification to dead letter alarm
        dead_letter_alarm.add_alarm_action(
            cw_actions.SnsAction(self.alarm_topic)
        )

        # Alarm for high queue depth (too many messages waiting)
        queue_depth_alarm = cloudwatch.Alarm(
            self,
            "IngestionQueueDepthAlarm",
            alarm_name="aurora-vector-kb-queue-depth",
            alarm_description="Alert when ingestion queue has too many pending messages",
            metric=self.ingestion_queue.metric("ApproximateNumberOfVisibleMessages",
                period=Duration.minutes(5),
                statistic="Average"
            ),
            threshold=100,  # Alert if more than 100 messages waiting
            evaluation_periods=2,  # Must be high for 10 minutes
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )

        # Add SNS notification to queue depth alarm
        queue_depth_alarm.add_alarm_action(
            cw_actions.SnsAction(self.alarm_topic)
        )

        # Alarm for old messages (messages stuck in queue)
        message_age_alarm = cloudwatch.Alarm(
            self,
            "IngestionQueueMessageAgeAlarm",
            alarm_name="aurora-vector-kb-message-age",
            alarm_description="Alert when messages are stuck in queue for too long",
            metric=self.ingestion_queue.metric("ApproximateAgeOfOldestMessage",
                period=Duration.minutes(5),
                statistic="Maximum"
            ),
            threshold=1800,  # Alert if oldest message is older than 30 minutes
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )

        # Add SNS notification to message age alarm
        message_age_alarm.add_alarm_action(
            cw_actions.SnsAction(self.alarm_topic)
        )

        # Alarm for no message processing (queue not being consumed)
        no_processing_alarm = cloudwatch.Alarm(
            self,
            "IngestionQueueNoProcessingAlarm",
            alarm_name="aurora-vector-kb-no-processing",
            alarm_description="Alert when no messages are being processed from the queue",
            metric=self.ingestion_queue.metric("NumberOfMessagesReceived",
                period=Duration.minutes(15),
                statistic="Sum"
            ),
            threshold=1,
            evaluation_periods=4,  # No messages received for 1 hour
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.BREACHING
        )

        # Add SNS notification to no processing alarm
        no_processing_alarm.add_alarm_action(
            cw_actions.SnsAction(self.alarm_topic)
        )

    def get_ingestion_queue(self) -> sqs.Queue:
        """
        Get the main ingestion SQS queue
        
        Returns:
            sqs.Queue: The main ingestion queue for document processing
        """
        return self.ingestion_queue

    def get_dead_letter_queue(self) -> sqs.Queue:
        """
        Get the dead letter queue
        
        Returns:
            sqs.Queue: The dead letter queue for failed messages
        """
        return self.dead_letter_queue

    def get_alarm_topic(self) -> sns.Topic:
        """
        Get the SNS topic for alarm notifications
        
        Returns:
            sns.Topic: SNS topic for CloudWatch alarm notifications
        """
        return self.alarm_topic

    def get_queue_url(self) -> str:
        """
        Get the ingestion queue URL
        
        Returns:
            str: The URL of the main ingestion queue
        """
        return self.ingestion_queue.queue_url

    def get_queue_arn(self) -> str:
        """
        Get the ingestion queue ARN
        
        Returns:
            str: The ARN of the main ingestion queue
        """
        return self.ingestion_queue.queue_arn