"""Backward-compatible alias — use NimService instead."""

from services.nim_service import NimService as GroqService

__all__ = ["GroqService"]
