# Auto-Learning System: AI recommendations and continuous improvement
import discord
from discord.ext import commands
from datetime import datetime
import json
import os
from cogs.core.pst_timezone import get_now_pst

class AutoLearningSystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.learning_models = {}
        self.recommendations = {}
        self.training_data = {}
        self.model_counter = 0
        self.recommendation_counter = 0
        self.data_file = "data/learning.json"
        self.load_learning()

    def load_learning(self):
        """Load learning system data from JSON file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.learning_models = data.get('models', {})
                    self.recommendations = data.get('recommendations', {})
                    self.training_data = data.get('training_data', {})
                    self.model_counter = data.get('model_counter', 0)
                    self.recommendation_counter = data.get('recommendation_counter', 0)
            except:
                self.learning_models = {}

    def save_learning(self):
        """Save learning system data to JSON file."""
        os.makedirs('data', exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump({
                'models': self.learning_models,
                'recommendations': self.recommendations,
                'training_data': self.training_data,
                'model_counter': self.model_counter,
                'recommendation_counter': self.recommendation_counter
            }, f, indent=2)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def createlearningmodel(self, ctx, model_type: str, *, description: str):
        """Create learning model. Usage: !createlearningmodel <threat|incident|response|pattern> description"""
        valid_types = ['threat', 'incident', 'response', 'pattern', 'behavior', 'anomaly']
        if model_type not in valid_types:
            await ctx.send(f"❌ Invalid model type. Use: {', '.join(valid_types)}")
            return
        
        self.model_counter += 1
        model_id = self.model_counter
        
        model_data = {
            "id": model_id,
            "type": model_type,
            "description": description,
            "enabled": True,
            "created_by": ctx.author.id,
            "created_at": get_now_pst().isoformat(),
            "accuracy": 0.0,
            "training_samples": 0,
            "predictions_made": 0,
            "last_trained": None,
            "confidence_threshold": 0.75,
            "version": "1.0"
        }
        
        self.learning_models[str(model_id)] = model_data
        self.save_learning()
        
        embed = discord.Embed(
            title=f"✅ Learning Model #{model_id} Created",
            description=f"**Type:** {model_type.upper()}",
            color=discord.Color.green()
        )
        embed.add_field(name="Description", value=description, inline=False)
        embed.add_field(name="Status", value="🟢 Ready for training", inline=True)
        embed.add_field(name="Accuracy", value="0%", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def trainmodel(self, ctx, model_id: int, sample_count: int, accuracy: float):
        """Train learning model. Usage: !trainmodel <model_id> <samples> <accuracy_percent>"""
        model_key = str(model_id)
        if model_key not in self.learning_models:
            await ctx.send("❌ Learning model not found.")
            return
        
        if not 0 <= accuracy <= 100:
            await ctx.send("❌ Accuracy must be between 0-100.")
            return
        
        model = self.learning_models[model_key]
        model["training_samples"] += sample_count
        model["accuracy"] = accuracy / 100.0
        model["last_trained"] = get_now_pst().isoformat()
        
        self.save_learning()
        
        embed = discord.Embed(
            title=f"🧠 Model #{model_id} Trained",
            description=f"**Type:** {model['type'].upper()}",
            color=discord.Color.blue()
        )
        embed.add_field(name="New Samples", value=sample_count, inline=True)
        embed.add_field(name="Total Samples", value=model["training_samples"], inline=True)
        embed.add_field(name="Accuracy", value=f"{accuracy:.1f}%", inline=True)
        embed.add_field(name="Last Trained", value=model["last_trained"], inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def predictwitmodel(self, ctx, model_id: int, *, input_data: str):
        """Make prediction with model. Usage: !predictwitmodel <model_id> data"""
        model_key = str(model_id)
        if model_key not in self.learning_models:
            await ctx.send("❌ Learning model not found.")
            return
        
        model = self.learning_models[model_key]
        
        if model["training_samples"] == 0:
            await ctx.send("❌ Model must be trained before making predictions.")
            return
        
        self.recommendation_counter += 1
        recommendation_id = self.recommendation_counter
        
        # Simulate prediction based on model accuracy
        prediction_confidence = model["accuracy"]
        
        recommendation_data = {
            "id": recommendation_id,
            "model_id": model_id,
            "model_type": model["type"],
            "input": input_data,
            "prediction": f"Predicted {model['type']} action based on training",
            "confidence": prediction_confidence,
            "created_at": get_now_pst().isoformat(),
            "created_by": ctx.author.id,
            "accepted": False,
            "feedback": None
        }
        
        self.recommendations[str(recommendation_id)] = recommendation_data
        model["predictions_made"] += 1
        self.save_learning()
        
        confidence_pct = prediction_confidence * 100
        
        embed = discord.Embed(
            title=f"🧠 Model Prediction #{recommendation_id}",
            description=recommendation_data["prediction"],
            color=discord.Color.green() if confidence_pct >= 75 else discord.Color.yellow()
        )
        embed.add_field(name="Input", value=input_data[:100], inline=False)
        embed.add_field(name="Model Type", value=model["type"].upper(), inline=True)
        embed.add_field(name="Confidence", value=f"{confidence_pct:.1f}%", inline=True)
        embed.add_field(name="Recommendation ID", value=recommendation_id, inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def feedbackprediction(self, ctx, recommendation_id: int, feedback: str):
        """Provide feedback on prediction. Usage: !feedbackprediction <recommendation_id> correct|incorrect|partial"""
        recommendation_key = str(recommendation_id)
        if recommendation_key not in self.recommendations:
            await ctx.send("❌ Recommendation not found.")
            return
        
        valid_feedback = ['correct', 'incorrect', 'partial']
        if feedback not in valid_feedback:
            await ctx.send(f"❌ Invalid feedback. Use: {', '.join(valid_feedback)}")
            return
        
        recommendation = self.recommendations[recommendation_key]
        recommendation["feedback"] = feedback
        self.save_learning()
        
        embed = discord.Embed(
            title=f"✅ Feedback Recorded #{recommendation_id}",
            description=f"Marked as: {feedback.upper()}",
            color=discord.Color.green()
        )
        embed.add_field(name="Model Type", value=recommendation["model_type"].upper(), inline=True)
        embed.add_field(name="Confidence", value=f"{recommendation['confidence']*100:.1f}%", inline=True)
        embed.add_field(name="Timestamp", value=get_now_pst().strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def generaterecommendations(self, ctx):
        """Generate AI recommendations based on learning. Usage: !generaterecommendations"""
        if not self.learning_models:
            await ctx.send("ℹ️ No learning models configured.")
            return
        
        embed = discord.Embed(
            title="🧠 AI Recommendations",
            color=discord.Color.blue()
        )
        
        for model_id, model in list(self.learning_models.items())[:5]:
            if model["accuracy"] > 0.7:
                recommendation_text = f"Model #{model_id} ({model['type']}) is performing well with {model['accuracy']*100:.0f}% accuracy."
                embed.add_field(
                    name=f"✅ {model['type'].upper()}",
                    value=recommendation_text,
                    inline=False
                )
            elif model["training_samples"] < 50:
                embed.add_field(
                    name=f"⚠️ {model['type'].upper()}",
                    value=f"Model needs more training data. Current: {model['training_samples']} samples.",
                    inline=False
                )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def modelinfo(self, ctx, model_id: int):
        """View model information and performance."""
        model_key = str(model_id)
        if model_key not in self.learning_models:
            await ctx.send("❌ Learning model not found.")
            return
        
        model = self.learning_models[model_key]
        
        embed = discord.Embed(
            title=f"🧠 Learning Model #{model_id}",
            description=model["description"],
            color=discord.Color.blue()
        )
        embed.add_field(name="Type", value=model["type"].upper(), inline=True)
        embed.add_field(name="Version", value=model["version"], inline=True)
        embed.add_field(name="Status", value="🟢 Active" if model["enabled"] else "🔴 Disabled", inline=True)
        embed.add_field(name="Accuracy", value=f"{model['accuracy']*100:.1f}%", inline=True)
        embed.add_field(name="Training Samples", value=model["training_samples"], inline=True)
        embed.add_field(name="Predictions Made", value=model["predictions_made"], inline=True)
        embed.add_field(name="Confidence Threshold", value=f"{model['confidence_threshold']*100:.0f}%", inline=True)
        embed.add_field(name="Last Trained", value=model["last_trained"] or "Never", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def listlearningmodels(self, ctx):
        """List all learning models."""
        if not self.learning_models:
            await ctx.send("ℹ️ No learning models.")
            return
        
        embed = discord.Embed(
            title=f"🧠 Learning Models ({len(self.learning_models)})",
            color=discord.Color.blue()
        )
        
        for model_id, model in list(self.learning_models.items())[:10]:
            status = "🟢 ACTIVE" if model["enabled"] else "🔴 DISABLED"
            embed.add_field(
                name=f"#{model_id} | {model['type'].upper()}",
                value=f"Accuracy: {model['accuracy']*100:.1f}% | Samples: {model['training_samples']} | Predictions: {model['predictions_made']} | {status}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def learningstats(self, ctx):
        """View learning system statistics."""
        embed = discord.Embed(
            title="🧠 Learning System Statistics",
            color=discord.Color.blue()
        )
        
        total_models = len(self.learning_models)
        active_models = sum(1 for m in self.learning_models.values() if m["enabled"])
        total_samples = sum(m.get("training_samples", 0) for m in self.learning_models.values())
        total_predictions = sum(m.get("predictions_made", 0) for m in self.learning_models.values())
        avg_accuracy = sum(m.get("accuracy", 0) for m in self.learning_models.values()) / max(total_models, 1)
        
        embed.add_field(name="Total Models", value=total_models, inline=True)
        embed.add_field(name="Active Models", value=active_models, inline=True)
        embed.add_field(name="Average Accuracy", value=f"{avg_accuracy*100:.1f}%", inline=True)
        embed.add_field(name="Total Training Samples", value=total_samples, inline=True)
        embed.add_field(name="Total Predictions", value=total_predictions, inline=True)
        embed.add_field(name="Recommendations Made", value=len(self.recommendations), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoLearningSystemCog(bot))
