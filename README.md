# Discord Bot for IC System

A Discord bot for handling in-character (IC) and supernatural (SPN) events in roleplay servers.

## Features

- Anonymous IC event posting
- Supernatural event posting  
- Image attachment support
- Role-based permissions
- Dice rolling system
- Thread messaging

## Commands

- `!ic-info <message> [image_url]` - Post anonymous IC event
- `!spn-info <message> [image_url]` - Post anonymous supernatural event
- `!send_to_thread <thread_id> <message>` - Send message to specific thread
- `!dice <sides> [count]` - Roll dice (1-10 sides, up to 20 dice)
- `!info` - Show bot information
- `!info-dice` - Show dice command help

## Deployment

1. Set environment variables in Railway dashboard
2. Deploy from this folder
3. Bot will automatically start

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

- `TOKEN` - Discord bot token
- `SPNINFO` - SPN events channel ID
- `SPNINFOADMIN` - SPN admin channel ID  
- `ICINFO` - IC events channel ID
- `ICINFOADMIN` - IC admin channel ID
- `TESTERROLE` - Tester role ID
- `PLAYERROLE` - Player role ID
- `MERCYMAINERROLE` - Mercy mainer role ID
- `QQUSERID` - Allowed user ID
