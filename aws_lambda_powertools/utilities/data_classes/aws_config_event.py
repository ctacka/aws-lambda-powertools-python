import json
from typing import Union, Dict

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class AWSConfigConfigurationChangeEvent(DictWrapper):
    """AWS Config publishes an event when it detects a configuration change for a resource that
    is within a rule's scope. The following example event shows that the rule was triggered by a
    configuration change for an EC2 instance. """

    @property
    def event(self) -> dict:
        return self["configurationItem"]


class AWSConfigOversizedConfigurationChangeEvent(DictWrapper):
    """Some resource changes generate oversized configuration items. The following example event
    shows that the rule was triggered by an oversized configuration change for an EC2 instance. """

    @property
    def event(self) -> dict:
        return self["configurationItemSummary"]


class AWSConfigPeriodicInvokingEvent(DictWrapper):
    @property
    def event(self) -> dict:
        return dict(self)


class AWSConfigEvent(DictWrapper):
    @property
    def invoking_event(self) -> Union[
        AWSConfigConfigurationChangeEvent,
        AWSConfigOversizedConfigurationChangeEvent,
        AWSConfigPeriodicInvokingEvent
    ]:
        """The event that triggers the evaluation for a rule. If the event is published in
        response to a resource configuration change, the value for this attribute is a string
        that contains a JSON configurationItem or a configurationItemSummary (for oversized
        configuration items)"""
        invoking_event = json.loads(self["invokingEvent"])
        if "configurationItem" in invoking_event.keys():
            return AWSConfigConfigurationChangeEvent(invoking_event)
        elif "configurationItemSummary" in invoking_event.keys():
            return AWSConfigOversizedConfigurationChangeEvent(invoking_event)
        else:
            return AWSConfigPeriodicInvokingEvent(invoking_event)

    @property
    def rule_parameters(self) -> Dict[str, str]:
        """Key/value pairs that the function processes as part of its evaluation logic. You
        define parameters when you use the AWS Config console to create a Custom Lambda rule. You
        can also define parameters with the InputParameters attribute in the PutConfigRule AWS
        Config API request or the put-config-rule AWS CLI command. """
        return json.loads(self["ruleParameters"])

    @property
    def execution_role_arn(self) -> str:
        """The ARN of the IAM role that is assigned to AWS Config."""
        return self["executionRoleArn"]

    @property
    def config_rule_name(self) -> str:
        """The name that you assigned to the rule that caused AWS Config to publish the event and
        invoke the function. """
        return self["configRuleName"]

    @property
    def config_rule_id(self) -> str:
        """The ID that AWS Config assigned to the rule."""
        return self["configRuleId"]

    @property
    def config_rule_arn(self) -> str:
        """The ARN that AWS Config assigned to the rule."""
        return self["configRuleArn"]

    @property
    def account_id(self) -> str:
        """The ID that AWS Config assigned to the rule."""
        return self["accountId"]

    @property
    def version(self) -> str:
        """A version number assigned by AWS. The version will increment if AWS adds attributes to
        AWS Config events. If a function requires an attribute that is only in events that match
        or exceed a specific version, then that function can check the value of this attribute.
        The current version for AWS Config events is 1.0.
        """
        return self["version"]

    @property
    def event_left_scope(self) -> bool:
        """A Boolean value that indicates whether the AWS resource to be evaluated has been
        removed from the rule's scope. If the value is true, the function indicates that the
        evaluation can be ignored by passing NOT_APPLICABLE as the value for the ComplianceType
        attribute in the PutEvaluations call. """
        return self["eventLeftScope"]

    @property
    def result_token(self) -> str:
        """A token that the function must pass to AWS Config with the PutEvaluations call."""
        return self["resultToken"]
