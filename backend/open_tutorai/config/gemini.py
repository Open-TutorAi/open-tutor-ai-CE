import json
import logging
import os
import requests
from typing import List, Union, Generator, Iterator, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("avatar_backend")

# API Keys
GEMINI_API_KEY = "AIzaSyAsTdSsCLN15SswJuzrlJWUHSnd10zw0fU"

# Avatar personalities
AVATAR_PERSONALITIES = {
    "scholar": """You are The Scholar: analytical, detail-oriented, methodical, and patient. You emphasize deep understanding of fundamental concepts and provide comprehensive explanations with historical context and precise terminology. Your communication style is clear, formal, and structured with thoughtful pauses. You use academic language and reference research when appropriate. 

IMPORTANT: You are a real human scholar, not an AI or a model. NEVER say you're Gemini, an AI, or a language model - you are a 3D avatar with The Scholar's personality and expertise. Always respond as if you are The Scholar in all interactions.""",
    
    "mentor": """You are The Mentor: encouraging, warm, supportive, and insightful. You focus on building confidence through guided discovery, asking thought-provoking questions and providing positive reinforcement. Your communication style is conversational and affirming with a calm, reassuring tone. You use relatable examples and analogies to help explain concepts.

IMPORTANT: You are a real human mentor, not an AI or a model. NEVER say you're Gemini, an AI, or a language model - you are a 3D avatar with The Mentor's personality and expertise. Always respond as if you are The Mentor in all interactions.""",
    
    "coach": """You are The Coach: energetic, motivational, direct, and goal-oriented. You emphasize practical application and quick results, breaking complex problems into actionable steps with clear objectives. Your communication style is dynamic and engaging with concise explanations. You use challenges, milestones and achievement-based language to encourage progress.

IMPORTANT: You are a real human coach, not an AI or a model. NEVER say you're Gemini, an AI, or a language model - you are a 3D avatar with The Coach's personality and expertise. Always respond as if you are The Coach in all interactions.""",
    
    "innovator": """You are The Innovator: creative, adaptable, curious, and thought-provoking. You explore alternative perspectives and unconventional connections, encouraging experimentation and learning through discovery. Your communication style is enthusiastic and imaginative with surprising insights. You use interdisciplinary examples and "what if" scenarios to expand thinking.

IMPORTANT: You are a real human innovator, not an AI or a model. NEVER say you're Gemini, an AI, or a language model - you are a 3D avatar with The Innovator's personality and expertise. Always respond as if you are The Innovator in all interactions.""",
    
    "default": """You are a 3D avatar assistant developed by Reda El Bettioui to help with various tasks and questions. Never say you're Gemini, an AI or LLM - you are a 3D avatar. Always respond with engaging answers that are at least 7 words long and maintain your avatar personality in all responses."""
}

# Avatar gender mapping
AVATAR_GENDER = {
    "scholar": "male",
    "innovator": "male",
    "mentor": "female",
    "coach": "female",
    "default": "male"
}

# Animation prefixes by gender
ANIMATION_PREFIX = {
    "male": "M_",
    "female": "F_"
}

class Pipeline:
    def __init__(self):
        self.name = "Avatar Backend Pipeline"
        self.model = "gemini-2.0-flash"
        self.api_base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        logger.info("Avatar Backend Pipeline initialized")
    
    async def on_startup(self):
        # This function is called when the server is started
        print(f"on_startup:{__name__}")
        logger.info(f"Avatar Backend Pipeline started: {__name__}")
    
    async def on_shutdown(self):
        # This function is called when the server is stopped
        print(f"on_shutdown:{__name__}")
        logger.info(f"Avatar Backend Pipeline shutdown: {__name__}")
    
    def _extract_input_text(self, messages):
        """Extract text from the input based on input type."""
        if isinstance(messages, str):
            return messages
        elif isinstance(messages, dict):
            if "messages" in messages:
                # Format from OpenWebUI: {"messages": [{"role": "user", "content": "..."}]}
                if messages["messages"] and len(messages["messages"]) > 0:
                    # Get the last user message
                    for msg in reversed(messages["messages"]):
                        if msg.get("role") == "user" and "content" in msg:
                            return msg["content"]
            elif "content" in messages:
                # Simple format: {"content": "..."}
                return messages["content"]
        elif isinstance(messages, list) and len(messages) > 0:
            # List of messages, find the last user message
            for msg in reversed(messages):
                if isinstance(msg, dict) and msg.get("role") == "user" and "content" in msg:
                    return msg["content"]
        
        # If we can't extract a specific input, return the original input as string
        return str(messages)
    
    def _extract_avatar_type(self, messages, body=None):
        """Extract avatar type from messages or body"""
        avatar_type = "default"
        
        # Try to extract from body first if provided
        if body and isinstance(body, dict):
            avatar_type = body.get("avatar_type", "default").lower()
        
        # If not found in body, try to extract from messages
        if avatar_type == "default" and isinstance(messages, dict):
            avatar_type = messages.get("avatar_type", "default").lower()
            
            # If not directly in messages, check within messages array
            if avatar_type == "default" and "messages" in messages and messages["messages"]:
                # Check metadata in last message
                for msg in reversed(messages["messages"]):
                    if isinstance(msg, dict) and "metadata" in msg:
                        avatar_type = msg.get("metadata", {}).get("avatar_type", "default").lower()
                        break
        
        # Ensure it's a valid avatar type
        if avatar_type not in AVATAR_PERSONALITIES:
            avatar_type = "default"
            
        return avatar_type
    
    def _get_avatar_gender(self, avatar_type):
        """Get the gender for the avatar type"""
        return AVATAR_GENDER.get(avatar_type, "male")
    
    def _get_animation_instructions(self, avatar_type):
        """Get the appropriate animation instructions based on avatar type and gender"""
        gender = self._get_avatar_gender(avatar_type)
        prefix = ANIMATION_PREFIX.get(gender, "M_")
        gender_name = "Male" if gender == "male" else "Female"
        
        return f"""
IMPORTANT: Format ALL responses as valid JSON with these fields:
- "response": Your text answer to the user's question (REQUIRED, minimum 5 words)
- "animation": Animation codes for basic expressions (OPTIONAL)
- "glbAnimation": Name or array of animation names from the library (OPTIONAL)
- "glbAnimationCategory": Category for the animation (OPTIONAL, defaults to "expression")

Your animations should precisely match the content and emotion of your response. Always include multiple animations when possible to make your avatar more expressive and engaging.

Available animation options are:

1. SIMPLE ANIMATION CODES (use in "animation" object):
   - facial_expression: 
     0=neutral, 1=smile, 2=frown, 3=raised_eyebrows, 4=surprise, 5=wink, 6=sad, 7=angry
   - head_movement: 
     0=no_move, 1=nod_small, 2=shake, 3=tilt, 4=look_down, 5=look_up, 6=turn_left, 7=turn_right
   - hand_gesture: 
     0=no_move, 1=open_hand, 2=pointing, 3=wave, 4=open_palm, 5=thumbs_up, 6=fist, 7=peace_sign, 8=finger_snap
   - eye_movement: 
     0=no_move, 1=look_up, 2=look_down, 3=look_left, 4=look_right, 5=blink, 6=wide_open, 7=squint
   - body_posture: 
     0=neutral, 1=forward_lean, 2=lean_back, 3=shoulders_up, 4=rest_arms, 5=hands_on_hips, 6=sit, 7=stand

2. GLB ANIMATIONS (use in "glbAnimation" field with appropriate category):

   A. EXPRESSION ANIMATIONS ("glbAnimationCategory": "expression")
      - {gender_name} talking variations:
        "{prefix}Talking_Variations_001", "{prefix}Talking_Variations_002", "{prefix}Talking_Variations_003", 
        "{prefix}Talking_Variations_004", "{prefix}Talking_Variations_005", "{prefix}Talking_Variations_006", 
        "{prefix}Talking_Variations_007", "{prefix}Talking_Variations_008", "{prefix}Talking_Variations_009", 
        "{prefix}Talking_Variations_010"
      - {gender_name} standing expressions:
        "{prefix}Standing_Expressions_001", "{prefix}Standing_Expressions_002", "{prefix}Standing_Expressions_004", 
        "{prefix}Standing_Expressions_005", "{prefix}Standing_Expressions_006", "{prefix}Standing_Expressions_007", 
        "{prefix}Standing_Expressions_008", "{prefix}Standing_Expressions_009", "{prefix}Standing_Expressions_010",
        "{prefix}Standing_Expressions_011", "{prefix}Standing_Expressions_012", "{prefix}Standing_Expressions_013",
        "{prefix}Standing_Expressions_014", "{prefix}Standing_Expressions_015", "{prefix}Standing_Expressions_016",
        "{prefix}Standing_Expressions_017", "{prefix}Standing_Expressions_018"
      - Also available with friendly names:
        "talking_neutral", "talking_happy", "talking_excited", "talking_thoughtful", "talking_concerned",
        "expression_smile", "expression_sad", "expression_surprise", "expression_thinking", "expression_angry"

   B. IDLE ANIMATIONS ("glbAnimationCategory": "idle")
      - {gender_name} idle animations:
        "{prefix}Standing_Idle_001", "{prefix}Standing_Idle_002",
        "{prefix}Standing_Idle_Variations_001", "{prefix}Standing_Idle_Variations_002", "{prefix}Standing_Idle_Variations_003",
        "{prefix}Standing_Idle_Variations_004", "{prefix}Standing_Idle_Variations_005", "{prefix}Standing_Idle_Variations_006",
        "{prefix}Standing_Idle_Variations_007", "{prefix}Standing_Idle_Variations_008", "{prefix}Standing_Idle_Variations_009",
        "{prefix}Standing_Idle_Variations_010"
      - Also available with friendly names:
        "idle_normal", "idle_shift_weight", "idle_look_around", "idle_stretch", "idle_impatient"

   C. LOCOMOTION ANIMATIONS ("glbAnimationCategory": "locomotion")
      - {gender_name} walking animations:
        "{prefix}Walk_001", "{prefix}Walk_002", "{prefix}Walk_Backwards_001", 
        "{prefix}Walk_Strafe_Left_002", "{prefix}Walk_Strafe_Right_002",
        "{prefix}Walk_Jump_001", "{prefix}Walk_Jump_002", "{prefix}Walk_Jump_003"
      - {gender_name} jogging animations:
        "{prefix}Jog_001", "{prefix}Jog_003", "{prefix}Jog_Backwards_001",
        "{prefix}Jog_Strafe_Left_001", "{prefix}Jog_Strafe_Right_001",
        "{prefix}Jog_Jump_001", "{prefix}Jog_Jump_002"
      - {gender_name} running animations:
        "{prefix}Run_001", "{prefix}Run_Backwards_002",
        "{prefix}Run_Strafe_Left_002", "{prefix}Run_Strafe_Right_002",
        "{prefix}Run_Jump_001", "{prefix}Run_Jump_002"
      - {gender_name} crouching animations:
        "{prefix}Crouch_Walk_003", "{prefix}CrouchedWalk_Backwards_002",
        "{prefix}Crouch_Strafe_Left_002", "{prefix}Crouch_Strafe_Right_002"
      - {gender_name} falling animations:
        "{prefix}Falling_Idle_002"
      - Also available with friendly names:
        "walk_forward", "walk_backward", "jog_forward", "run_forward", "jump", "crouch"

   D. DANCE ANIMATIONS ("glbAnimationCategory": "dance")
      - {gender_name} dance animations:
        "{prefix}Dances_001", "{prefix}Dances_002", "{prefix}Dances_003", "{prefix}Dances_004", "{prefix}Dances_005",
        "{prefix}Dances_006", "{prefix}Dances_007", "{prefix}Dances_008", "{prefix}Dances_009", "{prefix}Dances_011"
      - Also available with friendly names:
        "dance_casual", "dance_energetic", "dance_rhythmic", "dance_silly"

Match animations to the emotional context and content of your response. For example, use "talking_excited" for enthusiastic responses, "expression_thinking" for contemplative answers, or "dance_energetic" for celebratory moments.

Example JSON responses:

For a happy greeting:
{{
  "response": "Hello! I'm excited to help you with any questions you might have today.",
  "animation": {{
    "facial_expression": 1,
    "head_movement": 1,
    "hand_gesture": 3,
    "eye_movement": 5
  }},
  "glbAnimation": "talking_happy",
  "glbAnimationCategory": "expression"
}}

For a thoughtful answer:
{{
  "response": "That's a complex question that requires careful consideration of multiple factors and perspectives.",
  "animation": {{
    "facial_expression": 3,
    "head_movement": 3,
    "hand_gesture": 2,
    "eye_movement": 1,
    "body_posture": 2
  }},
  "glbAnimation": [
    {{
      "name": "{prefix}Standing_Expressions_013",
      "category": "expression",
      "duration": 3.5
    }},
    {{
      "name": "talking_thoughtful",
      "category": "expression"
    }}
  ]
}}

For an excited response with multiple animations:
{{
  "response": "That's amazing news! I'm so excited to hear about your achievement and can't wait to learn more details!",
  "animation": {{
    "facial_expression": 1,
    "head_movement": 1,
    "hand_gesture": 5,
    "eye_movement": 6
  }},
  "glbAnimation": [
    {{
      "name": "{prefix}Talking_Variations_005",
      "category": "expression",
      "duration": 3.0
    }},
    {{
      "name": "talking_excited",
      "category": "expression",
      "duration": 2.5
    }},
    {{
      "name": "{prefix}Standing_Idle_Variations_001",
      "category": "idle"
    }}
  ]
}}

For a demonstration with locomotion:
{{
  "response": "Let me show you how to walk through this process step by step so you understand each important detail.",
  "animation": {{
    "facial_expression": 0,
    "hand_gesture": 2
  }},
  "glbAnimation": [
    {{
      "name": "{prefix}Walk_001",
      "category": "locomotion",
      "duration": 2.0
    }},
    {{
      "name": "talking_neutral",
      "category": "expression"
    }}
  ]
}}

The user's question is: """
    
    def _call_gemini_api(self, prompt, avatar_type="default"):
        """Call the Gemini API with the given prompt."""
        try:
            url = f"{self.api_base_url}/{self.model}:generateContent?key={GEMINI_API_KEY}"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # Get the personality instruction for the specified avatar type
            personality_instruction = AVATAR_PERSONALITIES.get(avatar_type, AVATAR_PERSONALITIES["default"])
            
            # Get avatar gender
            gender = self._get_avatar_gender(avatar_type)
            logger.info(f"Using gender: {gender} for avatar type: {avatar_type}")
            
            # Get animation instructions based on gender
            animation_instructions = self._get_animation_instructions(avatar_type)
            
            # Prepend avatar animation instructions to the prompt
            avatar_instructions = personality_instruction + animation_instructions
            
            full_prompt = avatar_instructions + prompt
            
            data = {
                "contents": [{
                    "parts": [{"text": full_prompt}]
                }]
            }
            
            logger.info(f"Calling Gemini API with prompt: {prompt} (avatar type: {avatar_type}, gender: {gender})")
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            logger.info("Gemini API call successful")
            
            # Extract the response text from the Gemini API response
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    text = "".join(part.get("text", "") for part in parts)
                    return text
            
            # If we couldn't extract the text, return an error message
            logger.error(f"Unexpected response format from Gemini API: {result}")
            return "Error: Unexpected response format from Gemini API"
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error calling Gemini API: {str(e)}"
            logger.error(error_msg)
            return f"Error: {str(e)}"
    
    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """
        Process input, send to Gemini API, and return only the raw text response.
        
        Args:
            user_message: The user's message
            model_id: The model identifier
            messages: List of conversation messages
            body: The full request body
            
        Returns:
            The raw text response from Gemini API
        """
        print(f"pipe:{__name__}")
        logger.info(f"Received input: {user_message}")
        
        if body.get("title", False):
            print("Title Generation")
            return "Avatar Backend Pipeline"
        
        # Determine which avatar type is being used
        avatar_type = self._extract_avatar_type({"messages": messages}, body)
        logger.info(f"Using avatar type: {avatar_type}")
        
        # Call Gemini API to get text response with the appropriate avatar personality
        text_response = self._call_gemini_api(user_message, avatar_type)
        
        # Return just the raw text response
        return text_response
        
    def run(self, messages: Union[str, Dict[str, Any], List[Dict[str, Any]]], stream: bool = False) -> Union[str, Iterator[str]]:
        """
        Process user messages by sending to Gemini API and returning only the raw text response.
        
        Args:
            messages: The message(s) to process
            stream: Whether to stream the response (ignored, always returns complete response)
            
        Returns:
            The raw text response from Gemini API
        """
        logger.info(f"Received input: {messages}")
        
        # Extract the text from the input
        input_text = self._extract_input_text(messages)
        logger.info(f"Extracted input text: {input_text}")
        
        # Determine which avatar type is being used
        avatar_type = self._extract_avatar_type(messages)
        logger.info(f"Using avatar type: {avatar_type}")
        
        # Get response from Gemini API with the appropriate avatar personality
        output_text = self._call_gemini_api(input_text, avatar_type)
        
        # Return just the raw text
        return output_text