from __future__ import annotations

import json
import os
import time
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key


TABLE = os.environ.get("REPOG_TABLE", "")
BUCKET = os.environ.get("REPOG_WORKSPACE_BUCKET", "")


def ddb_value(value: Any) -> Any:
    """Convert JSON numbers to DynamoDB's lossless Decimal representation."""
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, list):
        return [ddb_value(item) for item in value]
    if isinstance(value, dict):
        return {key: ddb_value(item) for key, item in value.items()}
    return value


def table():
    return boto3.resource("dynamodb").Table(TABLE)


def get_session(session_id: str) -> dict[str, Any]:
    item = table().get_item(Key={"pk": f"SESSION#{session_id}", "sk": "STATE"}, ConsistentRead=True).get("Item")
    if not item:
        raise KeyError("session_not_found")
    return item


def claim_nonce(nonce: str, ttl_seconds: int = 600) -> None:
    try:
        table().put_item(Item={"pk": f"NONCE#{nonce}", "sk": "USED", "expires_at": int(time.time()) + ttl_seconds}, ConditionExpression="attribute_not_exists(pk)")
    except table().meta.client.exceptions.ConditionalCheckFailedException as exc:
        raise RuntimeError("request_replayed") from exc


def create_session(item: dict[str, Any]) -> None:
    table().put_item(Item=ddb_value(item), ConditionExpression="attribute_not_exists(pk)")


def store_intent(session_id: str, turn_id: str, kind: str, operation_id: str, payload: dict[str, Any]) -> bool:
    key = {"pk": f"SESSION#{session_id}", "sk": f"TURN#{turn_id}#INTENT#{kind}"}
    try:
        table().put_item(Item=ddb_value({**key, "operation_id": operation_id, "payload": payload, "created_at": int(time.time())}), ConditionExpression="attribute_not_exists(pk)")
        return True
    except table().meta.client.exceptions.ConditionalCheckFailedException:
        current = table().get_item(Key=key, ConsistentRead=True).get("Item", {})
        if current.get("operation_id") != operation_id or current.get("payload") != payload:
            raise RuntimeError("operation_conflict")
        return False


def get_intents(session_id: str, turn_id: str) -> dict[str, dict[str, Any]]:
    result = table().query(KeyConditionExpression=Key("pk").eq(f"SESSION#{session_id}") & Key("sk").begins_with(f"TURN#{turn_id}#INTENT#"))
    return {str(item["sk"]).rsplit("#", 1)[-1].lower(): item["payload"] for item in result.get("Items", [])}


def mark_window_started(session_id: str, turn_id: str, execution_arn: str) -> bool:
    try:
        table().update_item(
            Key={"pk": f"SESSION#{session_id}", "sk": "STATE"},
            UpdateExpression="SET window_execution = :execution, runtime_status = :status, turn_deadline = :deadline",
            ConditionExpression="turn_id = :turn AND (attribute_not_exists(window_execution) OR window_execution = :empty)",
            ExpressionAttributeValues={":execution": execution_arn, ":status": "coordination_window", ":deadline": int(time.time()) + 15, ":turn": turn_id, ":empty": ""},
        )
        return True
    except table().meta.client.exceptions.ConditionalCheckFailedException:
        return False


def reserve(session_id: str, reservation: int, day_key: str) -> None:
    table().update_item(
        Key={"pk": f"SESSION#{session_id}", "sk": "STATE"},
        UpdateExpression="ADD spend_reserved :amount",
        ConditionExpression="spend_settled + spend_reserved + :amount <= :limit",
        ExpressionAttributeValues={":amount": reservation, ":limit": 1_000_000},
    )
    try:
        table().update_item(
            Key={"pk": f"BUDGET#{day_key}", "sk": "DAILY"},
            UpdateExpression="ADD spend_reserved :amount SET expires_at = :ttl",
            ConditionExpression="attribute_not_exists(spend_reserved) OR spend_reserved + :amount <= :limit",
            ExpressionAttributeValues={":amount": reservation, ":limit": 10_000_000, ":ttl": int(time.time()) + 172800},
        )
    except Exception:
        table().update_item(Key={"pk": f"SESSION#{session_id}", "sk": "STATE"}, UpdateExpression="ADD spend_reserved :rollback", ExpressionAttributeValues={":rollback": -reservation})
        raise


def settle(session_id: str, reservation: int, actual: int, day_key: str) -> None:
    for key in ({"pk": f"SESSION#{session_id}", "sk": "STATE"}, {"pk": f"BUDGET#{day_key}", "sk": "DAILY"}):
        table().update_item(Key=key, UpdateExpression="ADD spend_reserved :release, spend_settled :actual", ExpressionAttributeValues={":release": -reservation, ":actual": actual})


def load_golden_bootstrap() -> dict[str, Any]:
    response = boto3.client("s3").get_object(Bucket=BUCKET, Key="golden/bootstrap.json")
    return json.loads(response["Body"].read())


def put_event(session_id: str, sequence: int, event: dict[str, Any]) -> None:
    table().put_item(Item=ddb_value({"pk": f"SESSION#{session_id}", "sk": f"EVENT#{sequence:08d}", "payload": event, "created_at": int(time.time())}), ConditionExpression="attribute_not_exists(pk)")


def list_events(session_id: str, after: int = 0) -> list[dict[str, Any]]:
    result = table().query(KeyConditionExpression=Key("pk").eq(f"SESSION#{session_id}") & Key("sk").begins_with("EVENT#"), Limit=100)
    return [{"sequence": int(str(item["sk"]).split("#")[1]), **item["payload"]} for item in result.get("Items", []) if int(str(item["sk"]).split("#")[1]) > after]


def commit_resolution(session_id: str, expected_revision: int, resolution: dict[str, Any]) -> None:
    table().update_item(
        Key={"pk": f"SESSION#{session_id}", "sk": "STATE"},
        UpdateExpression="SET revision = :next, turn_number = turn_number + :one, turn_id = :turn, turn_brief = :brief, runtime_status = :ready, window_execution = :empty, updated_at = :now",
        ConditionExpression="revision = :expected AND runtime_status = :resolving",
        ExpressionAttributeValues=ddb_value({":next": expected_revision + 1, ":one": 1, ":turn": resolution["next_turn"]["session"]["turn_id"], ":brief": resolution["next_turn"], ":ready": "ready", ":empty": "", ":now": int(time.time()), ":expected": expected_revision, ":resolving": "resolving"}),
    )
