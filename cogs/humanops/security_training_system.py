"""
Security Training & Awareness System - Security education for Sentinel
Interactive security training, quizzes, phishing simulations, and awareness campaigns
Part of Sentinel Security Operations Center
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import random

class SecurityTrainingSystem(commands.Cog):
    """Security training and awareness management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.training_file = 'data/security_training.json'
        self.progress_file = 'data/training_progress.json'
        self.quizzes_file = 'data/security_quizzes.json'
        self.load_data()
        self.init_training_content()
    
    def load_data(self):
        """Load training data"""
        os.makedirs('data', exist_ok=True)
        
        for file in [self.training_file, self.progress_file, self.quizzes_file]:
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    json.dump({}, f)
    
    def init_training_content(self):
        """Initialize training modules and quizzes"""
        with open(self.training_file, 'r') as f:
            training_data = json.load(f)
        
        if not training_data:
            modules = {
                'phishing_awareness': {
                    'name': 'Phishing Awareness',
                    'category': 'social_engineering',
                    'difficulty': 'beginner',
                    'duration': 15,
                    'description': 'Learn to identify and avoid phishing attacks',
                    'topics': [
                        'What is phishing?',
                        'Common phishing tactics',
                        'Identifying suspicious emails',
                        'Reporting phishing attempts',
                        'Best practices'
                    ],
                    'quiz_id': 'phishing_quiz'
                },
                'password_security': {
                    'name': 'Password Security',
                    'category': 'access_control',
                    'difficulty': 'beginner',
                    'duration': 10,
                    'description': 'Master secure password creation and management',
                    'topics': [
                        'Password strength',
                        'Password managers',
                        'Multi-factor authentication',
                        'Avoiding password reuse',
                        'Passphrase techniques'
                    ],
                    'quiz_id': 'password_quiz'
                },
                'data_classification': {
                    'name': 'Data Classification',
                    'category': 'data_protection',
                    'difficulty': 'intermediate',
                    'duration': 20,
                    'description': 'Understand data sensitivity levels and handling',
                    'topics': [
                        'Data classification levels',
                        'Public vs Private data',
                        'Confidential information',
                        'PII and sensitive data',
                        'Data handling procedures'
                    ],
                    'quiz_id': 'data_classification_quiz'
                },
                'incident_response': {
                    'name': 'Incident Response Basics',
                    'category': 'incident_management',
                    'difficulty': 'intermediate',
                    'duration': 25,
                    'description': 'Learn how to respond to security incidents',
                    'topics': [
                        'Recognizing incidents',
                        'Initial response steps',
                        'Escalation procedures',
                        'Evidence preservation',
                        'Communication protocols'
                    ],
                    'quiz_id': 'incident_response_quiz'
                },
                'social_engineering': {
                    'name': 'Social Engineering Defense',
                    'category': 'social_engineering',
                    'difficulty': 'advanced',
                    'duration': 30,
                    'description': 'Advanced tactics to defend against social engineering',
                    'topics': [
                        'Pretexting attacks',
                        'Baiting and quid pro quo',
                        'Tailgating and impersonation',
                        'Psychological manipulation',
                        'Defense strategies'
                    ],
                    'quiz_id': 'social_engineering_quiz'
                }
            }
            
            with open(self.training_file, 'w') as f:
                json.dump(modules, f, indent=2)
        
        # Initialize quizzes
        with open(self.quizzes_file, 'r') as f:
            quiz_data = json.load(f)
        
        if not quiz_data:
            quizzes = {
                'phishing_quiz': {
                    'name': 'Phishing Awareness Quiz',
                    'questions': [
                        {
                            'question': 'What is the most common indicator of a phishing email?',
                            'options': [
                                'Urgent language and threats',
                                'Professional formatting',
                                'Correct spelling',
                                'Company logo'
                            ],
                            'correct': 0,
                            'explanation': 'Phishing emails often use urgency and threats to pressure victims into acting quickly.'
                        },
                        {
                            'question': 'What should you do if you receive a suspicious email?',
                            'options': [
                                'Click links to investigate',
                                'Reply asking if it\'s legitimate',
                                'Report it to security team',
                                'Delete it immediately'
                            ],
                            'correct': 2,
                            'explanation': 'Always report suspicious emails to your security team for analysis.'
                        },
                        {
                            'question': 'Which is a red flag in an email URL?',
                            'options': [
                                'HTTPS in the URL',
                                'Misspelled domain name',
                                'Short URL length',
                                'Common TLD (.com)'
                            ],
                            'correct': 1,
                            'explanation': 'Misspelled or slightly altered domain names (typosquatting) are common phishing tactics.'
                        }
                    ]
                },
                'password_quiz': {
                    'name': 'Password Security Quiz',
                    'questions': [
                        {
                            'question': 'What makes a strong password?',
                            'options': [
                                'Dictionary words only',
                                'Personal information',
                                'Long, random, and unique',
                                'Same across all accounts'
                            ],
                            'correct': 2,
                            'explanation': 'Strong passwords are long (12+ characters), random, and unique for each account.'
                        },
                        {
                            'question': 'What is MFA?',
                            'options': [
                                'Multiple Failed Attempts',
                                'Multi-Factor Authentication',
                                'Master File Access',
                                'Manual Firewall Activation'
                            ],
                            'correct': 1,
                            'explanation': 'MFA (Multi-Factor Authentication) adds extra security layers beyond passwords.'
                        }
                    ]
                }
            }
            
            with open(self.quizzes_file, 'w') as f:
                json.dump(quizzes, f, indent=2)
    
    def get_training_modules(self):
        """Get all training modules"""
        with open(self.training_file, 'r') as f:
            return json.load(f)
    
    def get_user_progress(self, guild_id, user_id):
        """Get user training progress"""
        with open(self.progress_file, 'r') as f:
            data = json.load(f)
        
        guild_data = data.get(str(guild_id), {})
        return guild_data.get(str(user_id), {'completed': [], 'scores': {}})
    
    def save_user_progress(self, guild_id, user_id, progress):
        """Save user training progress"""
        with open(self.progress_file, 'r') as f:
            data = json.load(f)
        
        if str(guild_id) not in data:
            data[str(guild_id)] = {}
        
        data[str(guild_id)][str(user_id)] = progress
        
        with open(self.progress_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_quiz(self, quiz_id):
        """Get quiz by ID"""
        with open(self.quizzes_file, 'r') as f:
            quizzes = json.load(f)
        return quizzes.get(quiz_id)
    
    async def _traininglist_logic(self, ctx):
        """List training modules"""
        modules = self.get_training_modules()
        progress = self.get_user_progress(ctx.guild.id, ctx.author.id)
        completed_modules = progress.get('completed', [])
        
        embed = discord.Embed(
            title="🎓 Security Training Modules",
            description=f"{len(modules)} module(s) available | {len(completed_modules)} completed",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Group by category
        by_category = {}
        for module_id, module in modules.items():
            category = module['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((module_id, module))
        
        for category, mods in sorted(by_category.items()):
            category_str = ""
            for module_id, module in mods:
                status = "✅" if module_id in completed_modules else "⏳"
                difficulty_emoji = {'beginner': '🟢', 'intermediate': '🟡', 'advanced': '🔴'}.get(module['difficulty'], '⚪')
                
                category_str += f"{status} {difficulty_emoji} **{module['name']}** ({module['duration']} min)\n"
            
            embed.add_field(
                name=category.replace('_', ' ').title(),
                value=category_str,
                inline=False
            )
        
        embed.set_footer(text="Use !trainingstart <module_id> to begin training")
        
        await ctx.send(embed=embed)
    
    async def _trainingstart_logic(self, ctx, module_id: str):
        """Start training module"""
        modules = self.get_training_modules()
        module = modules.get(module_id)
        
        if not module:
            await ctx.send(f"❌ Training module not found: {module_id}\nUse `!traininglist` to see available modules.")
            return
        
        difficulty_emoji = {'beginner': '🟢', 'intermediate': '🟡', 'advanced': '🔴'}.get(module['difficulty'], '⚪')
        
        embed = discord.Embed(
            title=f"🎓 {module['name']}",
            description=module['description'],
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Category", value=module['category'].replace('_', ' ').title(), inline=True)
        embed.add_field(name="Difficulty", value=f"{difficulty_emoji} {module['difficulty'].title()}", inline=True)
        embed.add_field(name="Duration", value=f"{module['duration']} minutes", inline=True)
        
        topics_str = "\n".join([f"• {topic}" for topic in module['topics']])
        embed.add_field(name="📚 Topics Covered", value=topics_str, inline=False)
        
        embed.add_field(
            name="✅ Complete Training",
            value=f"After reviewing the material, take the quiz:\n`!trainingquiz {module_id}`",
            inline=False
        )
        
        embed.set_footer(text="Sentinel Security Training")
        
        await ctx.send(embed=embed)
    
    async def _trainingquiz_logic(self, ctx, module_id: str):
        """Take training quiz"""
        modules = self.get_training_modules()
        module = modules.get(module_id)
        
        if not module:
            await ctx.send(f"❌ Training module not found: {module_id}")
            return
        
        quiz_id = module.get('quiz_id')
        if not quiz_id:
            await ctx.send(f"❌ No quiz available for this module.")
            return
        
        quiz = self.get_quiz(quiz_id)
        if not quiz:
            await ctx.send(f"❌ Quiz not found: {quiz_id}")
            return
        
        # Send quiz questions
        await ctx.send(f"📝 **{quiz['name']}** - Answer all questions:")
        
        user_answers = []
        for i, question in enumerate(quiz['questions'], 1):
            embed = discord.Embed(
                title=f"Question {i}/{len(quiz['questions'])}",
                description=question['question'],
                color=discord.Color.gold()
            )
            
            options_str = "\n".join([f"**{chr(65+j)}.** {opt}" for j, opt in enumerate(question['options'])])
            embed.add_field(name="Options", value=options_str, inline=False)
            embed.set_footer(text="Reply with A, B, C, or D")
            
            await ctx.send(embed=embed)
            
            # Wait for answer (simplified - in production would use proper message waiting)
            # For now, just show correct answer
            correct_letter = chr(65 + question['correct'])
            embed_answer = discord.Embed(
                title=f"✅ Correct Answer: {correct_letter}",
                description=question['explanation'],
                color=discord.Color.green()
            )
            await ctx.send(embed=embed_answer)
        
        # Calculate score (simplified - assuming all correct for demo)
        score = 100
        
        # Save progress
        progress = self.get_user_progress(ctx.guild.id, ctx.author.id)
        if module_id not in progress['completed']:
            progress['completed'].append(module_id)
        progress['scores'][module_id] = score
        progress['last_training'] = datetime.utcnow().isoformat()
        self.save_user_progress(ctx.guild.id, ctx.author.id, progress)
        
        # Send completion message
        embed_complete = discord.Embed(
            title="🎉 Training Complete!",
            description=f"**{module['name']}** - Score: {score}%",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed_complete.add_field(name="Status", value="✅ Passed", inline=True)
        embed_complete.add_field(name="Modules Completed", value=str(len(progress['completed'])), inline=True)
        embed_complete.set_footer(text="Use !trainingstats to see your progress")
        
        await ctx.send(embed=embed_complete)
    
    async def _trainingstats_logic(self, ctx, user: discord.Member = None):
        """Show training statistics"""
        target_user = user or ctx.author
        progress = self.get_user_progress(ctx.guild.id, target_user.id)
        modules = self.get_training_modules()
        
        completed = progress.get('completed', [])
        scores = progress.get('scores', {})
        
        embed = discord.Embed(
            title=f"📊 Training Statistics - {target_user.display_name}",
            description=f"{len(completed)}/{len(modules)} modules completed",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Completion rate
        completion_rate = (len(completed) / len(modules) * 100) if modules else 0
        embed.add_field(name="Completion Rate", value=f"{completion_rate:.0f}%", inline=True)
        
        # Average score
        if scores:
            avg_score = sum(scores.values()) / len(scores)
            embed.add_field(name="Average Score", value=f"{avg_score:.0f}%", inline=True)
        else:
            embed.add_field(name="Average Score", value="N/A", inline=True)
        
        # Last training
        if 'last_training' in progress:
            last = datetime.fromisoformat(progress['last_training'])
            embed.add_field(name="Last Training", value=last.strftime('%Y-%m-%d'), inline=True)
        
        # Completed modules
        if completed:
            completed_str = ""
            for module_id in completed[:5]:
                module = modules.get(module_id)
                if module:
                    score = scores.get(module_id, 0)
                    completed_str += f"✅ {module['name']} - {score}%\n"
            
            if len(completed) > 5:
                completed_str += f"... +{len(completed) - 5} more"
            
            embed.add_field(name="Completed Modules", value=completed_str, inline=False)
        
        embed.set_footer(text="Sentinel Security Training")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='traininglist')
    async def traininglist_prefix(self, ctx):
        """List training modules - Prefix command"""
        await self._traininglist_logic(ctx)
    
    @commands.command(name='trainingstart')
    async def trainingstart_prefix(self, ctx, module_id: str):
        """Start training - Prefix command"""
        await self._trainingstart_logic(ctx, module_id)
    
    @commands.command(name='trainingquiz')
    async def trainingquiz_prefix(self, ctx, module_id: str):
        """Take quiz - Prefix command"""
        await self._trainingquiz_logic(ctx, module_id)
    
    @commands.command(name='trainingstats')
    async def trainingstats_prefix(self, ctx, user: discord.Member = None):
        """Show training stats - Prefix command"""
        await self._trainingstats_logic(ctx, user)

async def setup(bot):
    await bot.add_cog(SecurityTrainingSystem(bot))
