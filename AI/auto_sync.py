"""
Auto-Sync Manager - Monitor and sync new/updated files and folders
Watches cogs directory for changes and auto-loads new extensions
Supports hot-reload for updated files with minimal disruption
"""

import os
import asyncio
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, Set, Optional
import hashlib

class AutoSyncManager:
    """Manages automatic file/folder synchronization and hot-reloading"""
    
    def __init__(self, bot, watch_path: str = '.'):
        self.bot = bot
        self.watch_path = Path(watch_path)
        self.cogs_path = self.watch_path / 'cogs'
        self.is_watching = False
        
        # File tracking
        self.file_hashes: Dict[str, str] = {}
        self.loaded_cogs: Set[str] = set()
        self.watched_extensions = {'.py', '.json', '.yaml', '.yml'}
        
        # Directories to watch
        self.watch_dirs = [
            self.cogs_path,
            self.watch_path / 'data',
            self.watch_path / 'AI'
        ]
        
        # Ignore patterns
        self.ignore_patterns = {
            '__pycache__', '.git', '.venv', 'node_modules',
            '__init__.py', '.pyc', '.pyo', '.egg-info'
        }
        
        self.sync_log_file = 'data/autosync_log.json'
        self.initial_scan_complete = False
        
        print("[AutoSync] Manager initialized")
    
    def _should_ignore(self, path_str: str) -> bool:
        """Check if path should be ignored"""
        for pattern in self.ignore_patterns:
            if pattern in path_str:
                return True
        return False
    
    def _get_file_hash(self, filepath: Path) -> str:
        """Get hash of file content"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def _log_sync_event(self, event_type: str, file_path: str, status: str):
        """Log sync event"""
        os.makedirs('data', exist_ok=True)
        
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': event_type,
            'file': file_path,
            'status': status
        }
        
        try:
            if os.path.exists(self.sync_log_file):
                with open(self.sync_log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(event)
            logs = logs[-1000:]  # Keep last 1000
            
            with open(self.sync_log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            print(f"[AutoSync] Error logging event: {e}")
    
    async def _discover_cogs(self, directory: Path = None) -> Set[str]:
        """Discover all cog modules"""
        if directory is None:
            directory = self.cogs_path
        
        discovered = set()
        
        for root, dirs, files in os.walk(directory):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignore_patterns]
            
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    filepath = Path(root) / file
                    
                    if self._should_ignore(str(filepath)):
                        continue
                    
                    # Calculate module path
                    rel_path = filepath.relative_to(self.watch_path)
                    module_name = str(rel_path)[:-3].replace(os.sep, '.')
                    
                    if module_name.startswith('cogs.'):
                        discovered.add(module_name)
        
        return discovered
    
    async def _load_new_cogs(self) -> int:
        """Load newly discovered cogs"""
        discovered = await self._discover_cogs()
        new_cogs = discovered - self.loaded_cogs
        
        loaded_count = 0
        for cog in new_cogs:
            # Skip if already in bot's extensions (prevents duplicate load errors)
            if cog in self.bot.extensions:
                self.loaded_cogs.add(cog)
                continue
            
            try:
                await self.bot.load_extension(cog)
                self.loaded_cogs.add(cog)
                loaded_count += 1
                
                print(f"[AutoSync] ✅ Loaded new cog: {cog}")
                self._log_sync_event('COG_LOAD', cog, 'success')
                
            except Exception as e:
                print(f"[AutoSync] ❌ Failed to load {cog}: {str(e)[:60]}")
                self._log_sync_event('COG_LOAD', cog, f'failed: {str(e)[:50]}')
        
        return loaded_count
    
    async def _reload_updated_cogs(self) -> int:
        """Reload cogs that have been updated"""
        reloaded_count = 0
        
        for cog in list(self.loaded_cogs):
            cog_path = (self.watch_path / cog.replace('.', os.sep)).with_suffix('.py')
            
            if not cog_path.exists():
                continue
            
            if self._should_ignore(str(cog_path)):
                continue
            
            current_hash = self._get_file_hash(cog_path)
            previous_hash = self.file_hashes.get(cog, "")
            
            # File has been updated
            if current_hash and current_hash != previous_hash:
                try:
                    await self.bot.reload_extension(cog)
                    self.file_hashes[cog] = current_hash
                    reloaded_count += 1
                    
                    print(f"[AutoSync] 🔄 Reloaded cog: {cog}")
                    self._log_sync_event('COG_RELOAD', cog, 'success')
                    
                except Exception as e:
                    print(f"[AutoSync] ⚠️ Failed to reload {cog}: {str(e)[:60]}")
                    self._log_sync_event('COG_RELOAD', cog, f'failed: {str(e)[:50]}')
                    
                    # Attempt to recover by reloading again
                    try:
                        await self.bot.reload_extension(cog)
                    except:
                        pass
        
        return reloaded_count
    
    async def _check_new_folders(self) -> int:
        """Check for new folder structures and cogs"""
        discovered = await self._discover_cogs()
        new_folders = discovered - self.loaded_cogs
        
        if new_folders:
            print(f"[AutoSync] 🆕 Found {len(new_folders)} new cog module(s)")
            return len(new_folders)
        
        return 0
    
    async def _sync_data_files(self) -> int:
        """Check for new/updated data files"""
        data_dir = self.watch_path / 'data'
        if not data_dir.exists():
            return 0
        
        synced_count = 0
        for file in data_dir.glob('*.json'):
            if self._should_ignore(str(file)):
                continue
            
            current_hash = self._get_file_hash(file)
            file_key = f"data/{file.name}"
            previous_hash = self.file_hashes.get(file_key, "")
            
            if current_hash and current_hash != previous_hash:
                self.file_hashes[file_key] = current_hash
                synced_count += 1
                self._log_sync_event('DATA_SYNC', str(file.relative_to(self.watch_path)), 'updated')
        
        return synced_count
    
    async def _initial_scan(self):
        """Perform initial scan of all files"""
        print("[AutoSync] Running initial scan...")
        
        # Get all currently loaded extensions from bot
        discovered = await self._discover_cogs()
        for cog in discovered:
            # Mark as loaded if already in bot's extensions
            if cog in self.bot.extensions:
                self.loaded_cogs.add(cog)
        
        # Hash all existing cogs
        for cog in discovered:
            cog_path = (self.watch_path / cog.replace('.', os.sep)).with_suffix('.py')
            if cog_path.exists():
                self.file_hashes[cog] = self._get_file_hash(cog_path)
        
        # Hash data files
        data_dir = self.watch_path / 'data'
        if data_dir.exists():
            for file in data_dir.glob('*.json'):
                if not self._should_ignore(str(file)):
                    file_key = f"data/{file.name}"
                    self.file_hashes[file_key] = self._get_file_hash(file)
        
        print(f"[AutoSync] Initial scan complete. Tracking {len(self.file_hashes)} file(s)")
        self.initial_scan_complete = True
    
    def start_watching(self):
        """Start auto-sync watcher (background task)"""
        self.is_watching = True
        print("[AutoSync] 👁️  Watcher started")
        
        # Create background task using asyncio
        if self.bot:
            import asyncio
            try:
                asyncio.create_task(self._watch_loop())
            except RuntimeError:
                # If no event loop is running, it will be handled later
                pass
    
    def stop_watching(self):
        """Stop auto-sync watcher"""
        self.is_watching = False
        print("[AutoSync] 👁️  Watcher stopped")
    
    async def _watch_loop(self):
        """Main watch loop - runs periodically"""
        await self.bot.wait_until_ready()
        
        # Initial scan
        if not self.initial_scan_complete:
            await self._initial_scan()
        
        iteration = 0
        while self.is_watching:
            try:
                iteration += 1
                
                # Check for new cogs every 5 seconds
                if iteration % 5 == 0:
                    new_count = await self._load_new_cogs()
                    if new_count > 0:
                        print(f"[AutoSync] 🆕 Loaded {new_count} new cog(s)")
                
                # Check for updated cogs every 3 seconds
                if iteration % 3 == 0:
                    reload_count = await self._reload_updated_cogs()
                    if reload_count > 0:
                        print(f"[AutoSync] 🔄 Reloaded {reload_count} cog(s)")
                
                # Sync data files every 10 seconds
                if iteration % 10 == 0:
                    data_count = await self._sync_data_files()
                    if data_count > 0:
                        print(f"[AutoSync] 📊 Synced {data_count} data file(s)")
                
                # Reset iteration counter
                if iteration > 1000:
                    iteration = 0
                
                await asyncio.sleep(1)
            
            except Exception as e:
                print(f"[AutoSync] ❌ Error in watch loop: {e}")
                await asyncio.sleep(5)
    
    async def get_sync_stats(self) -> dict:
        """Get sync statistics"""
        stats = {
            'is_watching': self.is_watching,
            'tracked_files': len(self.file_hashes),
            'loaded_cogs': len(self.loaded_cogs),
            'watch_directories': [str(d.relative_to(self.watch_path)) for d in self.watch_dirs if d.exists()]
        }
        
        # Get recent sync events
        if os.path.exists(self.sync_log_file):
            try:
                with open(self.sync_log_file, 'r') as f:
                    logs = json.load(f)
                    stats['recent_events'] = logs[-10:]
                    stats['total_events_logged'] = len(logs)
            except:
                stats['recent_events'] = []
        
        return stats
    
    async def force_sync(self) -> dict:
        """Force immediate sync"""
        results = {
            'new_cogs': await self._load_new_cogs(),
            'reloaded_cogs': await self._reload_updated_cogs(),
            'synced_data': await self._sync_data_files(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return results
    
    async def watch_directory(self, directory: str):
        """Add additional directory to watch"""
        watch_dir = self.watch_path / directory
        if watch_dir.exists() and watch_dir not in self.watch_dirs:
            self.watch_dirs.append(watch_dir)
            print(f"[AutoSync] 📁 Added watch directory: {directory}")
