#!/usr/bin/env python3
"""
Check AgentMail inbox for messages

Usage:
    # List recent messages
    python check_inbox.py --inbox "myagent@agentmail.to"
    
    # Get specific message
    python check_inbox.py --inbox "myagent@agentmail.to" --message "msg_123abc"
    
    # List threads
    python check_inbox.py --inbox "myagent@agentmail.to" --threads
    
    # Monitor for new messages (poll every N seconds)
    python check_inbox.py --inbox "myagent@agentmail.to" --monitor 30

Environment:
    AGENTMAIL_API_KEY: Your AgentMail API key

Fallback:
    If the environment variable is missing, the script also checks
    skills/agentmail/.env for AGENTMAIL_API_KEY.
"""

import argparse
import os
import sys
import time
from datetime import datetime

from _agentmail_config import load_agentmail_api_key, resolve_inbox_or_agent

try:
    from agentmail import AgentMail
except ImportError:
    print("Error: agentmail package not found. Install with: pip install agentmail")
    sys.exit(1)

def format_timestamp(iso_string):
    """Format ISO timestamp for display"""
    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return iso_string

def as_dict(value):
    if hasattr(value, 'model_dump'):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return {}


def print_message_summary(message):
    """Print a summary of a message"""
    data = as_dict(message)
    from_field = data.get('from') or data.get('from_') or getattr(message, 'from_', None) or 'Unknown'
    from_text = ', '.join(from_field) if isinstance(from_field, list) else str(from_field)
    subject = data.get('subject', '(no subject)')
    timestamp = format_timestamp(str(data.get('timestamp', '')))
    preview = (data.get('preview') or data.get('text') or '')[:100]

    print(f"📧 {data.get('message_id', 'N/A')}")
    print(f"   From: {from_text or 'Unknown'}")
    print(f"   Subject: {subject}")
    print(f"   Time: {timestamp}")
    if preview:
        print(f"   Preview: {preview}{'...' if len(preview) == 100 else ''}")
    print()

def print_thread_summary(thread):
    """Print a summary of a thread"""
    data = as_dict(thread)
    subject = data.get('subject', '(no subject)')
    participants = ', '.join(data.get('participants', []))
    count = data.get('message_count', 0)
    timestamp = format_timestamp(str(data.get('last_message_at', '')))

    print(f"🧵 {data.get('thread_id', 'N/A')}")
    print(f"   Subject: {subject}")
    print(f"   Participants: {participants}")
    print(f"   Messages: {count}")
    print(f"   Last: {timestamp}")
    print()

def main():
    parser = argparse.ArgumentParser(description='Check AgentMail inbox')
    parser.add_argument('--inbox', help='Inbox email address')
    parser.add_argument('--agent', help='OpenClaw agent id to resolve inbox from config/config.json')
    parser.add_argument('--message', help='Get specific message by ID')
    parser.add_argument('--threads', action='store_true', help='List threads instead of messages')
    parser.add_argument('--monitor', type=int, metavar='SECONDS', help='Monitor for new messages (poll interval)')
    parser.add_argument('--limit', type=int, default=10, help='Number of items to fetch (default: 10)')
    
    args = parser.parse_args()
    
    inbox_id = resolve_inbox_or_agent(args.inbox, args.agent)
    if not inbox_id:
        print("Error: provide --inbox or use --agent with a matching inboxAgentMap entry in config/config.json")
        sys.exit(1)

    # Get API key
    api_key = load_agentmail_api_key()
    if not api_key:
        print("Error: AGENTMAIL_API_KEY not found in environment or skills/agentmail/.env")
        sys.exit(1)
    
    # Initialize client
    client = AgentMail(api_key=api_key)
    
    if args.monitor:
        print(f"🔍 Monitoring {inbox_id} (checking every {args.monitor} seconds)")
        print("Press Ctrl+C to stop\n")
        
        last_message_ids = set()
        
        try:
            while True:
                try:
                    messages = client.inboxes.messages.list(
                        inbox_id=inbox_id,
                        limit=args.limit
                    )
                    
                    new_messages = []
                    current_message_ids = set()
                    
                    for message in messages.messages:
                        msg_id = message.get('message_id')
                        current_message_ids.add(msg_id)
                        
                        if msg_id not in last_message_ids:
                            new_messages.append(message)
                    
                    if new_messages:
                        print(f"🆕 Found {len(new_messages)} new message(s):")
                        for message in new_messages:
                            print_message_summary(message)
                    
                    last_message_ids = current_message_ids
                    
                except Exception as e:
                    print(f"❌ Error checking inbox: {e}")
                
                time.sleep(args.monitor)
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
            return
    
    elif args.message:
        # Get specific message
        try:
            message = client.inboxes.messages.get(
                inbox_id=inbox_id,
                message_id=args.message
            )
            
            data = as_dict(message)
            print(f"📧 Message Details:")
            print(f"   ID: {data.get('message_id')}")
            print(f"   Thread: {data.get('thread_id')}")

            from_field = data.get('from') or data.get('from_') or getattr(message, 'from_', None) or 'Unknown'
            from_text = ', '.join(from_field) if isinstance(from_field, list) else str(from_field)
            print(f"   From: {from_text}")

            to_field = data.get('to') or []
            to_addrs = ', '.join(str(addr) for addr in to_field)
            print(f"   To: {to_addrs}")

            print(f"   Subject: {data.get('subject', '(no subject)')}")
            print(f"   Time: {format_timestamp(str(data.get('timestamp', '')))}")

            if data.get('labels'):
                print(f"   Labels: {', '.join(data.get('labels'))}")

            print("\n📝 Content:")
            if data.get('text'):
                print(data['text'])
            elif data.get('html'):
                print("(HTML content - use API to get full HTML)")
            elif data.get('preview'):
                print(data['preview'])
            else:
                print("(No text content)")

            if data.get('attachments'):
                print(f"\n📎 Attachments ({len(data['attachments'])}):")
                for att in data['attachments']:
                    if isinstance(att, dict):
                        print(f"   • {att.get('filename', 'unnamed')} ({att.get('content_type', 'unknown type')})")
                    else:
                        print(f"   • {att}")
            
        except Exception as e:
            print(f"❌ Error getting message: {e}")
            sys.exit(1)
    
    elif args.threads:
        # List threads
        try:
            threads = client.inboxes.threads.list(
                inbox_id=inbox_id,
                limit=args.limit
            )
            
            if not threads.threads:
                print(f"📭 No threads found in {args.inbox}")
                return
            
            print(f"🧵 Threads in {inbox_id} (showing {len(threads.threads)}):\n")
            for thread in threads.threads:
                print_thread_summary(thread)
                
        except Exception as e:
            print(f"❌ Error listing threads: {e}")
            sys.exit(1)
    
    else:
        # List recent messages
        try:
            messages = client.inboxes.messages.list(
                inbox_id=inbox_id,
                limit=args.limit
            )
            
            if not messages.messages:
                print(f"📭 No messages found in {inbox_id}")
                return
            
            print(f"📧 Messages in {inbox_id} (showing {len(messages.messages)}):\n")
            for message in messages.messages:
                print_message_summary(message)
                
        except Exception as e:
            print(f"❌ Error listing messages: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()