"""TIER-2 DECISION: Constraint Satisfaction Solver"""
import discord
from discord.ext import commands
from datetime import datetime
import json, os
from typing import Dict, List
from cogs.core.pst_timezone import get_now_pst

class ConstraintSatisfactionSolver(commands.Cog):
    """Solve constraint satisfaction problems for decision-making"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/csp_solutions.json'
        self.solutions = {}
        self.load_solutions()
    
    def load_solutions(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.solutions = json.load(f)
                print(f"[CSP] ✅ Loaded {len(self.solutions)} solutions")
            except:
                self.solutions = {}
    
    def solve_csp(self, problem_id: str, variables: Dict, constraints: List[Dict]) -> Dict:
        """Solve constraint satisfaction problem"""
        # Simplified CSP solver
        valid_solutions = []
        
        # Check each variable combination against constraints
        def check_constraints(assignment):
            for constraint in constraints:
                var = constraint.get('variable')
                op = constraint.get('operator')  # '==', '!=', '<', '>'
                val = constraint.get('value')
                
                if var in assignment:
                    result = False
                    if op == '==':
                        result = assignment[var] == val
                    elif op == '!=':
                        result = assignment[var] != val
                    elif op == '<':
                        result = assignment[var] < val
                    elif op == '>':
                        result = assignment[var] > val
                    
                    if not result:
                        return False
            
            return True
        
        # Brute force: try all combinations
        # In production: use more sophisticated algorithms
        # For now, just simulate finding first valid solution
        assignment = variables.copy()
        
        if check_constraints(assignment):
            valid_solutions.append(assignment)
        
        self.solutions[problem_id] = {
            'variables': variables,
            'constraints': constraints,
            'solution': valid_solutions[0] if valid_solutions else None,
            'solution_found': len(valid_solutions) > 0,
            'solved_at': get_now_pst().isoformat()
        }
        
        self._save()
        return {
            'found': len(valid_solutions) > 0,
            'solution': valid_solutions[0] if valid_solutions else None
        }
    
    def _save(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.solutions, f, indent=2, default=str)

async def setup(bot):
    await bot.add_cog(ConstraintSatisfactionSolver(bot))
