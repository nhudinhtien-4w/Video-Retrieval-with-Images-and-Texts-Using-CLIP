import google.generativeai as genai
import logging
import os
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LlmService:
    def __init__(self, api_keys=None):
        """
        api_keys: List of API keys or single API key string (can be comma-separated)
        """
        # Handle comma-separated string
        if isinstance(api_keys, str):
            # Split by comma and clean whitespace
            api_keys = [k.strip().strip('"\'') for k in api_keys.split(',')]
        
        # Filter out None and empty strings
        self.api_keys = [k for k in (api_keys or []) if k and k.strip()]
        
        if not self.api_keys:
            logger.warning("No LLM API Key provided. Reprompting disabled.")
            self.model = None
            self.current_key_index = -1
            return

        self.current_key_index = 0
        self.model = None
        
        logger.info(f"LLM Service: Loaded {len(self.api_keys)} API key(s)")
        
        # Try to initialize with first key
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize Gemini model with current API key"""
        if self.current_key_index < 0 or self.current_key_index >= len(self.api_keys):
            logger.error("No more API keys available.")
            self.model = None
            return False
            
        try:
            current_key = self.api_keys[self.current_key_index]
            genai.configure(api_key=current_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            logger.info(f"Gemini LLM Service initialized with API key #{self.current_key_index + 1}/{len(self.api_keys)}")
            return True
        except Exception as e:
            logger.error(f"Failed to init Gemini with key #{self.current_key_index + 1}: {e}")
            self.model = None
            return False
    
    def _rotate_key(self):
        """Rotate to next API key"""
        self.current_key_index += 1
        if self.current_key_index >= len(self.api_keys):
            logger.warning("All API keys exhausted. Resetting to first key.")
            self.current_key_index = 0
        
        logger.info(f"Rotating to API key #{self.current_key_index + 1}/{len(self.api_keys)}")
        return self._initialize_model()

    def refine_for_clip(self, user_query: str, max_retries=None):
        """
        Input: "xe cứu thương chạy trên phố" (Vietnamese)
        Output: "An ambulance driving fast on a busy city street with buildings around" (English Visual Description)
        """
        if not self.model:
            return user_query

        # Default max_retries to number of available keys
        if max_retries is None:
            max_retries = len(self.api_keys)

        # --- PROMPT TỐI ƯU CHO CLIP (TEXT-TO-IMAGE) ---
        prompt = f"""
        You are an expert in rewriting search queries for OpenAI CLIP (Contrastive Language-Image Pre-training).
        
        TASK: Translate the user's query into English (if it's not) and rewrite it into a DETAILED VISUAL DESCRIPTION of the scene.
        Focus on: Objects, Actions, Colors, Background, Lighting.
        Keep it concise (under 50 words).
        
        USER QUERY: "{user_query}"
        
        OUTPUT: Return ONLY the rewritten English text string. Do not add quotes or explanations.
        """

        retry_count = 0
        while retry_count < max_retries:
            try:
                response = self.model.generate_content(prompt)
                refined_query = response.text.strip()
                
                logger.info(f"LLM Reprompt: '{user_query}' -> '{refined_query}'")
                return refined_query
            
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if error is quota/rate limit related
                is_quota_error = any(keyword in error_msg for keyword in [
                    'quota', 'rate limit', 'resource exhausted', '429', 'too many requests'
                ])
                
                if is_quota_error and retry_count < max_retries - 1:
                    logger.warning(f"API key #{self.current_key_index + 1} quota exceeded: {e}")
                    logger.info(f"Attempting to rotate to next API key... (retry {retry_count + 1}/{max_retries})")
                    
                    # Rotate to next key
                    if self._rotate_key():
                        retry_count += 1
                        time.sleep(0.5)  # Small delay before retry
                        continue
                    else:
                        logger.error("Failed to rotate to next key.")
                        break
                else:
                    logger.error(f"LLM Error (not quota related or no more retries): {e}")
                    break
        
        # Fallback: Trả về query gốc nếu tất cả keys đều thất bại
        logger.warning(f"All API keys failed or exhausted. Returning original query.")
        return user_query