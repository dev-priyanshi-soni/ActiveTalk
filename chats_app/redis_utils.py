import redis
import json

redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

def mark_user_active_in_group(user_id, group_channel_name):
    """Mark a user as active in a group chat"""
    redis_client.sadd(group_channel_name, str(user_id))

def remove_user_from_group(user_id, group_channel_name):
    """Remove a user from the active group chat tracking"""
    redis_client.srem(group_channel_name, str(user_id))

def get_active_users_in_group(group_channel_name):
    """Get list of all active user IDs in a group chat"""
    return [int(uid) for uid in redis_client.smembers(group_channel_name)]

def mark_user_active_in_personal_chat(user_id, room_name):
    """Mark a user as active in a personal chat"""
    redis_client.sadd(room_name, str(user_id))

def remove_user_from_personal_chat(user_id, room_name):
    """Remove a user from active personal chat tracking"""
    redis_client.srem(room_name, str(user_id))

def is_user_active_in_personal_chat(user_id, room_name):
    """Check if a user is active in a personal chat"""
    return redis_client.sismember(room_name, str(user_id))
