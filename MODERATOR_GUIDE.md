# 🛡️ Moderator Quick Reference

## Essential Commands (Use / or !)

### Basic Actions
```
/kick @user reason        - Kick member
/ban @user reason         - Ban member
/unban user_id reason     - Unban by ID
/timeout @user 10m reason - Mute for 10 minutes
/untimeout @user reason   - Remove timeout
/warn @user reason        - Issue warning
```

### Channel Management
```
/purge 50                - Delete last 50 messages
/purge 20 @user          - Delete 20 messages from user
/slowmode 10             - Set 10 second slowmode
/slowmode 0              - Disable slowmode
/lock                    - Lock current channel
/unlock                  - Unlock current channel
/lockdown                - Lock ALL channels (emergency)
/unlockdown              - Unlock all channels
```

### Advanced Actions
```
/massban 123 456 789     - Ban multiple users by ID
/masskick @role          - Kick all with role
/nickreset @user         - Reset nickname
/rolestrip @user         - Remove all roles
/raidmode on             - Enable raid protection
/raidmode off            - Disable raid protection
```

### Auto-Moderation
```
/filterconfig spam enable        - Enable spam filter
/filterconfig invites enable     - Block Discord invites
/filterconfig links enable       - Enable link filter
/filterconfig caps enable        - Block excessive caps
/linkwhitelist add youtube.com   - Allow YouTube links
/linkwhitelist list              - Show allowed domains
```

### History & Appeals
```
/modhistory @user        - View user's mod history
/listappeals pending     - Show pending appeals
/reviewappeal 5 approve note - Approve appeal #5
/reviewappeal 5 deny note    - Deny appeal #5
```

## Timeout Durations
- `10s` = 10 seconds
- `5m` = 5 minutes
- `1h` = 1 hour
- `1d` = 1 day
- Max: 28 days

## Filter Types
- **spam** - 5+ messages in 5 seconds (auto-timeout 60s)
- **mentions** - 5+ mentions in one message
- **invites** - Discord invite links
- **links** - Non-whitelisted URLs
- **caps** - 70%+ uppercase (min 10 chars)

## Raid Mode Features
When enabled:
- ✅ New member verification required
- ✅ All invite links blocked
- ✅ Enhanced spam detection
- ✅ Auto-kick suspicious accounts

## Appeal Process
1. User uses `/appeal reason:I apologize...`
2. Appeal appears in mod channel
3. Moderator reviews: `/reviewappeal <id> <approve/deny> <note>`
4. User receives DM with decision

## Permissions Required
- **kick** - Kick Members
- **ban** - Ban Members
- **timeout** - Moderate Members
- **warn** - Manage Messages
- **slowmode/lock** - Manage Channels
- **massban/lockdown** - Administrator
- **reviewappeal** - Manage Guild

## Tips
- Use slash commands for better UX (autocomplete)
- Always provide clear reasons for actions
- Check `/modhistory` before punishing
- Review `/listappeals` regularly
- Test filters in private channel first
- Use `/raidmode` only during actual raids
- Whitelist trusted domains before enabling link filter

