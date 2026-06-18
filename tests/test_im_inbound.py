"""Tests for IM inbound payload parsers."""

from src.agent.im_inbound import (
    feishu_url_verification_challenge,
    parse_dingtalk_inbound,
    parse_feishu_inbound,
)


def test_feishu_url_verification():
    body = {"type": "url_verification", "challenge": "abc123"}
    assert feishu_url_verification_challenge(body) == "abc123"
    assert parse_feishu_inbound(body) is None


def test_feishu_text_message():
    body = {
        "schema": "2.0",
        "header": {"event_type": "im.message.receive_v1"},
        "event": {
            "message": {
                "message_type": "text",
                "content": '{"text":"你好"}',
                "chat_id": "oc_xxx",
            },
            "sender": {"sender_id": {"user_id": "ou_yyy"}},
        },
    }
    parsed = parse_feishu_inbound(body)
    assert parsed == ("你好", "ou_yyy", "oc_xxx")


def test_dingtalk_text_message():
    body = {
        "msgtype": "text",
        "text": {"content": "ping"},
        "senderId": "u1",
        "conversationId": "conv1",
    }
    assert parse_dingtalk_inbound(body) == ("ping", "u1", "conv1")
