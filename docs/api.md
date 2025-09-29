# Mistral API Integration

## Overview

The agent communicates with Mistral's language model using a structured JSON API. This document describes the request/response format, available tools, and error handling.

## Request Format

```json
{
  "model": "mistral-tiny",
  "messages": [
    {
      "role": "system",
      "content": "You are a Pokémon Blue playing AI..."
    },
    {
      "role": "user",
      "content": "Current state: Overworld at (10, 15)..."
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "press_button",
        "description": "Press a controller button",
        "parameters": {
          "type": "object",
          "properties": {
            "button": {
              "type": "string",
              "enum": ["A", "B", "START", "SELECT", "UP", "DOWN", "LEFT", "RIGHT"]
            },
            "duration": {
              "type": "integer",
              "description": "Frames to hold button"
            }
          }
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

## Response Format

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "mistral-tiny",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_123",
            "type": "function",
            "function": {
              "name": "press_button",
              "arguments": "{\"button\": \"A\", \"duration\": 1}"
            }
          }
        ]
      }
    }
  ]
}
```

## Available Tools

### press_button
Simulates controller button press.

**Parameters:**
- `button`: Which button to press
- `duration`: Frames to hold (default: 1)

**Example:**
```json
{"button": "A", "duration": 1}
```

### move_to
Navigates to specified coordinates.

**Parameters:**
- `x`: Target X coordinate
- `y`: Target Y coordinate
- `map`: Target map ID

**Example:**
```json
{"x": 15, "y": 20, "map": 1}
```

### use_item
Uses an item from inventory.

**Parameters:**
- `item`: Item name
- `target`: Pokémon index (if applicable)

**Example:**
```json
{"item": "Potion", "target": 0}
```

### battle_action
Performs battle action.

**Parameters:**
- `action`: "fight", "bag", "pokemon", or "run"
- `move": Move index (if fighting)
- "target": Target index (if applicable)

**Example:**
```json
{"action": "fight", "move": 1}
```

## Error Handling

### API Errors

| Error Code | Description | Retry Strategy |
|------------|-------------|----------------|
| 429 | Rate limit exceeded | Exponential backoff |
| 500 | Server error | Immediate retry (max 3) |
| 401 | Invalid API key | Fail fast |
| 400 | Bad request | Validate and correct |

### Response Validation

All responses are validated against JSON schema:

```python
class ToolCall(BaseModel):
    id: str
    type: str
    function: dict

class ChatCompletion(BaseModel):
    id: str
    choices: list[dict]
    # ... other fields
```

## Rate Limiting

- Maximum 60 requests per minute
- Burst limit of 10 requests
- Exponential backoff starting at 1 second

## Caching

Responses are cached for 60 seconds for identical prompts to reduce API calls.