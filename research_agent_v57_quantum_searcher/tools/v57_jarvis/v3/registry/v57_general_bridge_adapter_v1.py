import importlib.util
from pathlib import Path
P=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy/v57_general_mission_bridge_v1.py')
def execute(text):
 s=importlib.util.spec_from_file_location('j57_general_bridge',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m.execute(text)
