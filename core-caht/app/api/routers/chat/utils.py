# app/api/routers/chat/utils.py
def serialize_blocks(blocks):
    if not blocks:
        return []
    out = []
    for block in blocks:
        try:
            if hasattr(block, 'model_dump'):
                out.append(block.model_dump())
            elif hasattr(block, 'dict'):
                out.append(block.dict())
            elif isinstance(block, dict):
                out.append(block)
            elif hasattr(block, '__dict__'):
                out.append(block.__dict__)
            else:
                out.append({"type": "unknown", "content": str(block)})
        except Exception as e:
            print(f"Error serializing block: {e}")
            out.append({"type": "error", "content": f"Failed to serialize block: {e}"})
    return out