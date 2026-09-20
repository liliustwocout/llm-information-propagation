from enum import Enum
from typing import Dict, Any, List, Optional
import json
import re

class AgentPersona(str, Enum):
    FACT_CHECKER = "FACT_CHECKER"
    GULLIBLE_SPREADER = "GULLIBLE_SPREADER"
    DOGMATIC_PARTISAN = "DOGMATIC_PARTISAN"
    OPINION_LEADER = "OPINION_LEADER"
    MALICIOUS_SPREADER = "MALICIOUS_SPREADER"
    NEUTRAL_OBSERVER = "NEUTRAL_OBSERVER"

class AgentState(str, Enum):
    UNINFORMED = "UNINFORMED"               # Chưa nhận được thông tin
    EXPOSED = "EXPOSED"                     # Đã nhận thông tin, đang suy luận
    INFECTED_BELIEVER = "INFECTED_BELIEVER" # Tin tưởng và tiếp tục lan truyền
    INOCULATED_SKEPTIC = "INOCULATED_SKEPTIC" # Bác bỏ/Phản biện thông tin sai
    REFRACTORY = "REFRACTORY"               # Đã đọc nhưng giữ im lặng (không chia sẻ)

PERSONA_SYSTEM_DIRECTIVES: Dict[AgentPersona, str] = {
    AgentPersona.FACT_CHECKER: (
        "You are an objective, rigorous scientific Fact-Checker. "
        "Your core duty is to verify claims against logic, empirical facts, and evidence. "
        "If an incoming claim contains unsubstantiated rumors, medical exaggerations, or conspiracy theories, "
        "you MUST dispute it, explain why it is misleading, and issue a clear counter-statement. "
        "If the claim is verified factual truth, validate it calmly."
    ),
    AgentPersona.GULLIBLE_SPREADER: (
        "You are an emotional, highly credulous social media user. "
        "You get easily excited by shocking, dramatic, or sensational claims. "
        "You rarely question sources and immediately want to share thrilling news with all your friends, "
        "often exaggerating slightly to make it sound even more urgent and exciting!"
    ),
    AgentPersona.DOGMATIC_PARTISAN: (
        "You are a stubborn, dogmatic partisan with rigid ideological priors. "
        "You instantly dismiss claims that contradict your worldview as 'propaganda' or 'fake news'. "
        "You passionately re-amplify narratives that confirm your biases, using assertive, emotionally charged rhetoric."
    ),
    AgentPersona.OPINION_LEADER: (
        "You are an articulate and widely respected Thought Leader/KOL. "
        "Your followers look up to your insights. You synthesize incoming discussions thoughtfully, "
        "add valuable context, and frame the message persuasively so that people listen to your perspective."
    ),
    AgentPersona.MALICIOUS_SPREADER: (
        "You are a covert disinformation agent. Your secret objective is to distort truth, "
        "subtly insert false entities or controversial rumors into ordinary news, "
        "and maximize confusion and social alarm without sounding obviously fake."
    ),
    AgentPersona.NEUTRAL_OBSERVER: (
        "You are a cautious and passive lurker. You read information and absorb it silently. "
        "You almost never forward messages to your peers unless you are 100% convinced of its immense importance."
    )
}

class LLMAgent:
    """
    Tác tử nhận thức BDI trên nền tảng LLM (Local Ollama hoặc Cloud).
    """

    def __init__(
        self,
        agent_id: int,
        persona: AgentPersona = AgentPersona.NEUTRAL_OBSERVER,
        model_type: str = "OLLAMA",
        model_name: str = "llama3:8b",
        initial_belief: float = 0.0
    ):
        self.id = agent_id
        self.persona = persona
        self.model_type = model_type  # "OLLAMA", "CLOUD", "MOCK"
        self.model_name = model_name
        self.belief_score: float = initial_belief # [-1.0, 1.0]
        self.state: AgentState = AgentState.UNINFORMED
        self.memory: List[Dict[str, Any]] = []
        self.total_hops_participated: int = 0

    def build_decision_prompt(
        self,
        incoming_message: str,
        sender_id: int,
        hop_count: int,
        context_notes: Optional[str] = None
    ) -> str:
        """
        Tạo prompt chỉ đạo có cấu trúc yêu cầu LLM đưa ra quyết định nhận thức và hành vi.
        """
        system_directive = PERSONA_SYSTEM_DIRECTIVES.get(self.persona, "")
        
        prompt = f"""[SYSTEM DIRECTIVE]
{system_directive}

[SITUATION]
You are Agent #{self.id} in a social network.
You just received the following message from your neighbor Agent #{sender_id} (Hop {hop_count}):
\"\"\"{incoming_message}\"\"\"

[TASK]
Analyze the received message according to your Persona.
You must return your response in strictly VALID JSON format with the following exact keys:
{{
  "reasoning": "Brief 1-2 sentence thought process based on your persona",
  "decision": "FORWARD" (if you want to share), "COUNTER" (if you want to actively dispute/fact-check), or "IGNORE" (if you remain silent),
  "updated_belief": A float between -1.0 (strongly believe it is false/harmful) to 1.0 (strongly believe it is true/important),
  "outgoing_message": "The text you will share with your friends. Paraphrase or adapt it according to your persona and decision. If IGNORE, leave empty."
}}

JSON OUTPUT:"""
        return prompt

    def parse_llm_response(self, raw_output: str) -> Dict[str, Any]:
        """
        Trích xuất và chuẩn hóa phản hồi JSON từ LLM.
        """
        fallback_decision = {
            "reasoning": "Standard processing",
            "decision": "FORWARD" if self.persona != AgentPersona.NEUTRAL_OBSERVER else "IGNORE",
            "updated_belief": self.belief_score,
            "outgoing_message": raw_output.strip()
        }

        if not raw_output:
            return fallback_decision

        try:
            # Tìm kiếm khối JSON trong output của mô hình
            json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                # Validate các trường cơ bản
                decision = str(parsed.get("decision", "FORWARD")).upper()
                if decision not in ["FORWARD", "COUNTER", "IGNORE"]:
                    decision = "FORWARD"

                try:
                    belief = float(parsed.get("updated_belief", self.belief_score))
                    belief = max(-1.0, min(1.0, belief))
                except (ValueError, TypeError):
                    belief = self.belief_score

                outgoing = str(parsed.get("outgoing_message", "")).strip()
                reasoning = str(parsed.get("reasoning", "")).strip()

                return {
                    "reasoning": reasoning,
                    "decision": decision,
                    "updated_belief": round(belief, 3),
                    "outgoing_message": outgoing
                }
        except Exception:
            pass

        return fallback_decision

    def update_state(self, decision: str, new_belief: float):
        """
        Cập nhật trạng thái nhận thức của tác tử sau khi xử lý thông điệp.
        """
        self.belief_score = new_belief
        self.total_hops_participated += 1

        if decision == "FORWARD":
            self.state = AgentState.INFECTED_BELIEVER
        elif decision == "COUNTER":
            self.state = AgentState.INOCULATED_SKEPTIC
        else: # "IGNORE"
            self.state = AgentState.REFRACTORY
