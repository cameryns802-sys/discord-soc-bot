"""Check all slash commands in new engagement systems"""
import re

systems = {
    'Reputation System': 'cogs/utility/reputation_system.py',
    'Giveaway System': 'cogs/utility/giveaway_system.py',
    'Currency System': 'cogs/utility/currency_system.py',
    'Marketplace System': 'cogs/utility/marketplace_system.py',
    'Achievement System': 'cogs/utility/achievement_system.py',
    'Reaction Roles': 'cogs/utility/reaction_roles.py',
    'Starboard': 'cogs/utility/starboard.py',
    'Daily Challenges': 'cogs/utility/daily_challenges.py'
}

print('=' * 70)
print('NEW ENGAGEMENT SYSTEMS - SLASH COMMAND INVENTORY')
print('=' * 70)

total = 0
for name, path in systems.items():
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find slash commands
        commands = re.findall(r'@app_commands\.command\(name="([^"]+)"', content)
        
        if commands:
            print(f'\n📦 {name}:')
            print(f'   Commands: {len(commands)}')
            for cmd in commands:
                print(f'   ✓ /{cmd}')
            total += len(commands)
    except Exception as e:
        print(f'\n❌ {name}: ERROR - {e}')

print('\n' + '=' * 70)
print(f'✅ TOTAL NEW SLASH COMMANDS: {total}/34')
print('=' * 70)
