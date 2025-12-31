
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from utils.persona_generator import PersonaOrchestrator
from utils.logger import get_logger

# Mute other loggers
import logging
logging.basicConfig(level=logging.ERROR)

def extract_skills():
    skills = []
    try:
        with open('.agent/workflows/coursera_text.txt', 'r') as f:
            content = f.read()
            # Simple keyword extraction based on the file content pattern
            lines = content.split('\n')
            for line in lines:
                if "Certificate" in line or "Specialization" in line:
                    # distinct
                    if line.strip() not in skills:
                        skills.append(line.strip())
    except Exception as e:
        print(f"Error reading skills: {e}")
    return skills

def main():
    orchestrator = PersonaOrchestrator()
    
    task_description = """
    Evaluate enterprise hub and determine 3 improvements for each module to help me make more money and earn more gigs. 
    Ensure they align with my skills/certifications in ai/ml, bi, data analysis/viz, programming. 
    Evaluate what gigs/work/tasks/ im suitable for, then refine my portfolio to increase me getting hired and making more. 
    I desperately need to start making money today. Create a swarm to develop a plan.
    """
    
    # Stage 0: Classify
    classification = orchestrator.run_stage_0(task_description)
    print(f"\n=== TASK CLASSIFICATION ===")
    print(f"Type: {classification.task_type.value}")
    print(f"Confidence: {classification.confidence}%")
    print(f"Reasoning: {classification.reasoning}")
    
    # Stage 1: Generate Questions
    # We pass empty answers first to get the questions
    questions = orchestrator.profiler.generate_questions(classification.task_type)
    
    print(f"\n=== CLARIFYING QUESTIONS ===")
    for i, q in enumerate(questions, 1):
        print(f"{i}. {q}")

    # Extract skills for context
    skills = extract_skills()
    print(f"\n=== DETECTED SKILLS (from coursera_text.txt) ===")
    for s in skills[:10]: # Show top 10
        print(f"- {s}")
    print(f"... and {len(skills)-10} more.")

if __name__ == "__main__":
    main()
