import aiohttp
import os
from typing import Optional, Dict, Any
import base64
import json
import logging

class DirectAPI:
    """Direct implementation of NovelAI API without using the SDK"""
    
    def __init__(self):
        if "NAI_USERNAME" not in os.environ or "NAI_PASSWORD" not in os.environ:
            raise RuntimeError("Please ensure that NAI_USERNAME and NAI_PASSWORD are set in your environment")

        self.username = os.environ["NAI_USERNAME"]
        self.password = os.environ["NAI_PASSWORD"]
        
        self.logger = logging.getLogger("NovelAI")
        handler = logging.StreamHandler()
        self.logger.addHandler(handler)
        
        self.api_token = None
        self.session = None
        
        # Base URLs
        self.base_url = "https://api.novelai.net"
        self.text_url = "https://text.novelai.net"
        self.image_url = "https://image.novelai.net"
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self.login()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login(self):
        """Login to NovelAI and get access token"""
        login_url = f"{self.base_url}/user/login"
        
        login_data = {
            "key": self.username,
            "secret": self.password
        }
        
        try:
            async with self.session.post(login_url, json=login_data) as response:
                if response.status != 201 and response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"Login failed with status {response.status}: {error_text}")
                    raise Exception("Authentication", 401, f"Login failed: {error_text}")
                
                data = await response.json()
                self.api_token = data.get("accessToken")
                
                if not self.api_token:
                    raise Exception("Authentication", 401, "No access token received")
                
                self.logger.info("Successfully authenticated with NovelAI")
        except aiohttp.ClientError as e:
            self.logger.error(f"Connection error: {str(e)}")
            raise Exception("Connection", 502, str(e))
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token for API requests"""
        if not self.api_token:
            raise ValueError("Not authenticated. Call login() first.")
        
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def generate_text(self, prompt: str, model: str = "kayra-v1", 
                           max_length: int = 80, temperature: float = 1.0,
                           repetition_penalty: float = 2.8,
                           repetition_penalty_range: int = 2048,
                           repetition_penalty_slope: float = 0.02,
                           length_penalty: float = 0.0,
                           stop_sequences: list = None) -> Dict[str, Any]:
        """Generate text from NovelAI's LLM models"""
        if not stop_sequences:
            stop_sequences = [[85], [198]]  # Default stop sequences from original code
            
        url = f"{self.text_url}/ai/generate"
        
        payload = {
            "input": prompt,
            "model": model,
            "parameters": {
                "max_length": max_length,
                "min_length": 1,
                "temperature": temperature,
                "repetition_penalty": repetition_penalty,
                "repetition_penalty_range": repetition_penalty_range,
                "repetition_penalty_slope": repetition_penalty_slope,
                "length_penalty": length_penalty,
                "stop_sequences": stop_sequences,
                "logit_bias_exp": [],  # Required field as per API docs
                "use_string": True
            }
        }
        
        try:
            async with self.session.post(url, json=payload, headers=self.get_headers()) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"Text generation failed with status {response.status}: {error_text}")
                    raise Exception("TextGeneration", response.status, error_text)
                
                data = await response.json()
                return data
        except aiohttp.ClientError as e:
            self.logger.error(f"Connection error during text generation: {str(e)}")
            raise Exception("Connection", 502, str(e))
    
    async def generate_voice(self, text: str, voice: str, seed: int = -1, 
                            opus: bool = False, version: str = 'v2') -> bytes:
        """Generate voice using NovelAI's TTS service"""
        url = f"{self.base_url}/ai/generate-voice"
        
        payload = {
            "text": text,
            "voice": voice,
            "seed": seed,
            "opus": opus,
            "version": version
        }
        
        try:
            async with self.session.post(url, json=payload, headers=self.get_headers()) as response:
                if response.status != 200 and response.status != 201:
                    error_text = await response.text()
                    self.logger.error(f"Voice generation failed with status {response.status}: {error_text}")
                    raise Exception("VoiceGeneration", response.status, error_text)
                
                audio_data = await response.read()
                return audio_data
        except aiohttp.ClientError as e:
            self.logger.error(f"Connection error during voice generation: {str(e)}")
            raise Exception("Connection", 502, str(e))"