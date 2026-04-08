# === Changes needed in api/index.py ===

# 1. Update CreateChannelRequest to include default_model:
# class CreateChannelRequest(BaseModel):
#     name: str
#     slug: str
#     description: str = ""
#     system_prompt: str
#     greeting_prefix: str = ""
#     signature: str = ""
#     color: str = "#2563EB"
#     default_model: str = "gemini-2.5-flash"

# 2. In create_new_channel, pass default_model to create_channel (if supported)

# 3. In the generate route, use channel's default_model when user doesn't specify one:
# In the generate function, after getting the channel, if model is empty:
#     if not model and channel and channel.get("default_model"):
#         model = channel["default_model"]
