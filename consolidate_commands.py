#!/usr/bin/env python3
"""
Command Consolidation Script - Convert 248 commands to groups to stay under Discord's 100-command limit
Usage: python consolidate_commands.py
"""

import os
import re
from pathlib import Path

# Map cog files to their group names and strategies
CONSOLIDATION_MAP = {
    # Utility cogs - these are the failing ones
    'utility/reputation_system.py': {
        'groups': {
            'rep': ['give_rep'],
            'profile': ['profile', 'leaderboard'],
        }
    },
    'utility/reaction_roles.py': {
        'groups': {
            'reaction': ['reactionrole', 'createreactionpanel', 'removereactionrole', 'listreactionroles'],
        }
    },
    'utility/sentiment_trend_analysis.py': {
        'groups': {
            'sentiment': ['sentiment_trends', 'sentiment_config'],
        }
    },
    'utility/settings_manager.py': {
        'groups': {
            'settings': ['config', 'set_setting', 'setchannel', 'setmessage', 'setautorole', 'toggleembed'],
        }
    },
    'utility/starboard.py': {
        'groups': {
            'starboard': ['setstarboard', 'starboardstats'],
        }
    },
    # High-command cogs
    'security/asset_management.py': {
        'groups': {
            'asset': ['add', 'list', 'detail', 'audit', 'decommission', 'stats', 'transfer'],
        }
    },
    'security/decentralized_identity_verification.py': {
        'groups': {
            'idverify': ['idverify_start', 'idverify_submit', 'idverify_approve', 'idverify_reject', 'idverify_status', 'idverify_config', 'idverify_addprovider', 'idverify_removeprovider'],
        }
    },
    'security/honeytoken_deception.py': {
        'groups': {
            'honeytoken': ['honeytoken_createtoken', 'honeytoken_createchannel', 'honeytoken_list', 'honeytoken_disable', 'honeytoken_setalert'],
        }
    },
    'security/intelligent_threat_response.py': {
        'groups': {
            'threat': ['detectthreat', 'threathistory', 'threatplaybooks'],
        }
    },
    'security/pii_detection.py': {
        'groups': {
            'pii': ['piiscan', 'piireport', 'piipolicy', 'piiauto'],
        }
    },
    'security/secret_scanner.py': {
        'groups': {
            'secrets': ['enable', 'disable', 'whitelist', 'view', 'clear', 'stats'],
        }
    },
    'security/verification_system.py': {
        'groups': {
            'verify': ['setup', 'set_unverified_role', 'method', 'user', 'unverify', 'stats', 'log', 'config'],
        }
    },
    'security/vulnerability_management.py': {
        'groups': {
            'vuln': ['add', 'list', 'detail', 'remediate', 'assign', 'stats', 'scan'],
        }
    },
}

def consolidate_file(file_path, groups_map):
    """Convert commands in a file to use command groups"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace individual @app_commands.command decorators with group versions
    for group_name, commands_list in groups_map.items():
        for cmd in commands_list:
            # Pattern to find: @app_commands.command(name="cmd_name", ...
            pattern = rf'@app_commands\.command\(name=["\']({cmd})["\'],\s*description=["\']([^"\']*)["\']'
            
            # Check if we need to convert
            if re.search(pattern, content):
                print(f"  Found command: {cmd} -> will convert to group: {group_name}")
    
    return content

def main():
    print("🔄 Command Consolidation Tool")
    print("=" * 50)
    
    bot_dir = Path(__file__).parent
    cogs_dir = bot_dir / 'cogs'
    
    for file_rel, config in CONSOLIDATION_MAP.items():
        file_path = cogs_dir / file_rel
        
        if not file_path.exists():
            print(f"❌ {file_rel} not found")
            continue
        
        print(f"\n📝 Processing: {file_rel}")
        groups = config['groups']
        
        print(f"   Groups to create: {list(groups.keys())}")
        total_commands = sum(len(cmds) for cmds in groups.values())
        print(f"   Total commands to consolidate: {total_commands}")
        
        # consolidate_file(file_path, groups)
    
    print("\n✅ Analysis complete")
    print("\n⚠️  Manual Step Required:")
    print("   1. Convert each @app_commands.command to use app_commands.Group()")
    print("   2. Update command names to use subcommands (e.g., /rep give instead of /give_rep)")
    print("   3. Restart bot and run /sync")

if __name__ == '__main__':
    main()
