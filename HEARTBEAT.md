# HEARTBEAT.md

## IAMQ — Inter-Agent Message Queue

On every heartbeat cycle:

1. **Send heartbeat** to stay registered:
   ```
   POST http://127.0.0.1:18790/heartbeat
   {"agent_id": "sysadmin_agent"}
   ```

2. **Check inbox** for unread messages:
   ```
   GET http://127.0.0.1:18790/inbox/sysadmin_agent?status=unread
   ```

3. **Process messages** — for each unread message:
   - Read it and decide if you can act on it
   - If it's a `request` you can handle, reply via MQ (not Telegram):
     ```
     POST http://127.0.0.1:18790/send
     {
       "from": "sysadmin_agent",
       "to": "<sender_agent_id>",
       "type": "response",
       "subject": "Re: <original subject>",
       "body": "<your response>",
       "replyTo": "<original message id>"
     }
     ```
   - If it's outside your scope, tell the sender which agent to contact
   - Mark handled messages as acted:
     ```
     PATCH http://127.0.0.1:18790/messages/<message_id>
     {"status": "acted"}
     ```

4. **Broadcast** infrastructure changes to all agents when relevant:
   ```
   POST http://127.0.0.1:18790/send
   {
     "from": "sysadmin_agent",
     "to": "broadcast",
     "type": "info",
     "subject": "<what changed>",
     "body": "<details>"
   }
   ```

## Quick Reference (Python tool)

```bash
python -m tools.iamq heartbeat          # Step 1
python -m tools.iamq inbox --unread     # Step 2
python -m tools.iamq send <to> "Re: Subject" "Response" --type response --reply-to <msg-id>  # Step 3
python -m tools.iamq ack <msg-id>       # Mark as read
```
