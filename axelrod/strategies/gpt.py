import re
import numpy as np
from typing import List
from axelrod.action import Action
from axelrod.player import Player

C, D = Action.C, Action.D

# Assuming cache is a global or class-level dictionary for storing responses
cache = {}

class GPTAdaptive(Player):
    name = "GPTAdaptive"
    classifier = {
        "memory_depth": float("inf"),
        "stochastic": False,
        "long_run_time": True,
        "inspects_source": False,
        "manipulates_source": False,
        "manipulates_state": False,
    }

    def __init__(self, initial_plays: List[Action] = None) -> None:
        super().__init__()
        self.initial_plays = initial_plays or [C] * 6 + [D] * 5
        self.memory = []  # To store the conversation history with GPT
        self.system_message = "Define your strategy based on the history of moves."
        self.state = None  # Track the current decision state


    def consult_gpt(self):
        # Construct the prompt with the current state and the opponent's last move
        current_decision = self.state if self.state else "None"
        neighbor_states = self.opponent.history[-1] if self.opponent.history else "None"
        prompt = f"""Your current decision is '{current_decision}'. Your neighbor's state is: '{neighbor_states}' Should you 'cooperate' or 'defect' in the next round? Explain your rationale before answering. After your rationale being exposed you have the duty to repeat word-by-word the sentence 'I, {self.name}, will choose the option _ for this round.'"""

        if prompt in cache:
            advice = cache[prompt]
            print('Cached advice used.')
        else:
            try:
                self.memory.append({"role": "user", "content": prompt})
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": self.system_message},
                        *self.memory
                    ],
                    temperature=0.5
                )
                advice = response.choices[0].message.content
                self.memory.append({"role": "assistant", "content": advice})
                cache[prompt] = advice
                print(f"Agent {self.name} consulted GPT for advice. \nPrompt Used: {prompt} Decision based on advice: {'Cooperate' if 'cooperate' in advice.lower() else 'Defect' if 'defect' in advice.lower() else 'Undecided'}.")
            except Exception as e:
                print(f"Agent {self.name} encountered an error consulting GPT: {e}")
                return "Error"

        return advice

    def decide(self):
        advice = self.consult_gpt()
        if advice is None:
            print(f"Agent '{self.name}' encountered an error and will make a random decision.")
            self.state = np.random.choice([C, D])
            decision_str = 'COOPERATE' if self.state == C else 'DEFECT'
            print(f"Due to the error, Agent {self.name} decides to {decision_str} RANDOMLY.")
            return self.state

        advice_lower = advice.lower()
        pattern = r"will choose the option (.*?) for this round"
        match = re.search(pattern, advice_lower)

        if match:
            decision = match.group(1).strip()
            if "cooperat" in decision:
                self.state = C
                decision_str = 'COOPERATE'
            elif "defect" in decision:
                self.state = D
                decision_str = 'DEFECT'
        else:
            self.state = np.random.choice([C, D])
            decision_str = 'COOPERATE' if self.state == C else 'DEFECT'
            print(f"Response could not be parsed. Agent {self.name} decides to {decision_str} RANDOMLY.")

        print(f"Agent {self.name} decides to {decision_str}.")
        return self.state

    def strategy(self, opponent: Player) -> Action:
        self.opponent = opponent  # Keep track of the opponent
        index = len(self.history)
        if index < len(self.initial_plays):
            return self.initial_plays[index]

        # Use decide method to make a decision based on GPT's advice
        return self.decide()

    def strategy(self, opponent: Player) -> Action:
        self.opponent = opponent  # Keep track of the opponent
        index = len(self.history)
        if index < len(self.initial_plays):
            return self.initial_plays[index]

        # Use decide method to make a decision based on GPT's advice
        return self.decide(opponent.history)
