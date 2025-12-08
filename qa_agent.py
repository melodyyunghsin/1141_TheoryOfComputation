"""
QA Agent - Main Agent with LLM Integration
Integrates web search tools with LLM API for intelligent question answering.
"""

import requests
import json
import os
from dotenv import load_dotenv
from qa_tool import web_search, format_search_results

# Load environment variables
load_dotenv()


class QAAgent:
    """
    Main QA Agent that combines web search with LLM reasoning.
    
    Workflow:
    1. Receive user question
    2. Search web for relevant information
    3. Send question + context to LLM
    4. Return LLM's answer
    """
    
    def __init__(self, api_url=None, api_key=None):
        """
        Initialize the QA Agent.
        
        :param api_url: LLM API base URL (default: from .env)
        :param api_key: API key (default: from .env)
        """
        self.api_url = api_url or os.getenv("API_BASE_URL", "https://api-gateway.netdb.csie.ncku.edu.tw")
        self.api_key = api_key or os.getenv("API_KEY", "")
        
        if not self.api_key:
            raise ValueError("API_KEY not found. Please set it in .env file.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.default_model = "gpt-oss:20b"
        self.conversation_history = []
        self.max_history = 5  # Keep last 5 exchanges
    
    def _should_use_search(self, question: str) -> bool:
        """
        Determine if web search is needed for this question.
        
        :param question: User's question
        :return: True if search is needed, False otherwise
        """
        # Keywords that suggest search is needed
        search_keywords = [
            'search', 'find', 'look up', 'what is', 'who is', 'when', 'where',
            'latest', 'current', 'news', 'today', '2025', '2024',
            '搜尋', '查', '找', '是什麼', '是誰', '什麼時候', '哪裡', 
            '最新', '現在', '新聞', '今天', '台灣', '總統', '首都'
        ]
        
        # Chat keywords suggest no search needed
        chat_keywords = [
            'hello', 'hi', 'hey', 'thanks', 'thank you', 'bye', 'goodbye',
            'how are you', 'what can you do', 'tell me about yourself',
            '你好', '謝謝', '再見', '你是誰', '你會什麼', '介紹一下'
        ]
        
        question_lower = question.lower()
        
        # Check if it's clearly a chat message
        for keyword in chat_keywords:
            if keyword in question_lower:
                return False
        
        # Check if search is explicitly or implicitly needed
        for keyword in search_keywords:
            if keyword in question_lower:
                return True
        
        # If question is very short and conversational, probably no search
        if len(question.split()) <= 3 and not any(char in question for char in ['?', '？']):
            return False
        
        # Default: use search for questions
        return '?' in question or '？' in question or len(question.split()) > 5
    
    def search_and_answer(self, question: str, use_search: bool = None, max_results: int = 3, show_sources: bool = False) -> dict:
        """
        Main workflow: Search web and get LLM answer.
        
        :param question: User's question
        :param use_search: Whether to search web (None = auto-detect, True/False = force)
        :param max_results: Number of search results to use
        :param show_sources: Whether to show source URLs (default: False)
        :return: Dictionary with 'question', 'search_results', 'answer'
        """
        
        # Auto-detect if search is needed
        if use_search is None:
            use_search = self._should_use_search(question)
            if use_search:
                print("🔍 [Using web search]")
            else:
                print("💬 [Direct chat mode]")
        
        # Step 1: Search web if needed
        search_results = []
        context = ""
        
        if use_search:
            search_results = web_search(question, max_results=max_results)
            
            if search_results:
                context = self._build_context(search_results)
        
        # Step 2: Query LLM with conversation history
        llm_response = self._query_llm(question, context, show_sources)
        
        if llm_response:
            answer = llm_response.get('message', {}).get('content', 'No response')
            print(f"✅ Got answer from LLM\n")
            
            # Add to conversation history
            self._add_to_history(question, answer)
            
            # Add sources if requested
            if show_sources and search_results:
                answer += "\n\n📚 Sources:\n"
                for idx, result in enumerate(search_results, 1):
                    url = result.get('href', '')
                    if url:
                        answer += f"[{idx}] {url}\n"
        else:
            answer = "❌ Failed to get response from LLM. Please try again."
        
        # Return complete result
        return {
            'question': question,
            'search_results': search_results,
            'context_used': context,
            'answer': answer,
            'success': bool(llm_response)
        }
    
    def _add_to_history(self, question: str, answer: str):
        """
        Add conversation to history and maintain max length.
        
        :param question: User's question
        :param answer: Agent's answer
        """
        self.conversation_history.append({
            'role': 'user',
            'content': question
        })
        self.conversation_history.append({
            'role': 'assistant',
            'content': answer
        })
        
        # Keep only last N exchanges (N*2 messages)
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-(self.max_history * 2):]
    
    def _build_context(self, search_results: list) -> str:
        """
        Build context string from search results.
        
        :param search_results: List of search result dictionaries
        :return: Formatted context string
        """
        context = "Based on the following web search results:\n\n"
        
        for idx, result in enumerate(search_results, 1):
            title = result.get('title', 'No title')
            snippet = result.get('body', '')
            url = result.get('href', '')
            
            context += f"[{idx}] {title}\n"
            context += f"{snippet}\n"
            context += f"Source: {url}\n\n"
        
        return context
    
    def _query_llm(self, question: str, context: str = "", show_sources: bool = False) -> dict:
        """
        Query the LLM API with question and optional context.
        
        :param question: User's question
        :param context: Additional context from web search
        :param show_sources: Whether user wants sources
        :return: LLM response dictionary or None
        """
        
        # Build messages with conversation history
        messages = []
        
        # Add conversation history for context
        if self.conversation_history:
            messages.extend(self.conversation_history)
        
        # Build current prompt
        if context:
            prompt = f"{context}\n\nQuestion: {question}\n\nInstructions:\n- Provide a direct, concise answer\n- If the answer is simple, give it in 1-2 sentences\n- If explanation is needed, keep it brief and to the point\n- Do NOT repeat the question\n- Do NOT use markdown formatting (no **, ##, etc.)\n- Do NOT list sources (they will be added separately if requested)\n- Use plain text only"
        else:
            prompt = question
        
        # Add current question
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Prepare API request
        endpoint = f"{self.api_url}/api/chat"
        payload = {
            "model": self.default_model,
            "messages": messages,
            "stream": False
        }
        
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API Error: {e}")
            return None
    
    def chat(self, message: str, use_search: bool = False) -> str:
        """
        Simple chat without web search (conversational mode).
        
        :param message: User message
        :param use_search: Whether to use web search
        :return: LLM response text
        """
        
        if use_search:
            result = self.search_and_answer(message)
            return result['answer']
        else:
            response = self._query_llm(message)
            if response:
                return response.get('message', {}).get('content', 'No response')
            return "❌ Failed to get response"
    
    def interactive_mode(self):
        """
        Run agent in interactive mode (command-line interface).
        """
        
        print("\n" + "=" * 70)
        print("🤖 QA Agent - Interactive Mode")
        print("=" * 70)
        print("\nFeatures:")
        print("  - Auto-detects if web search is needed")
        print("  - Remembers conversation history")
        print("  - Type 'clear' to clear conversation history")
        print("  - Type 'quit' or 'exit' to exit")
        print("\n" + "=" * 70 + "\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                # Clear history command
                if user_input.lower() in ['clear', 'reset', 'clear history']:
                    self.conversation_history = []
                    print("\n🗑️ Conversation history cleared.\n")
                    continue
                
                # Check if user wants sources
                show_sources = any(keyword in user_input.lower() for keyword in ['來源', '出處', 'source', 'reference', '參考', 'ref'])
                
                # Auto-detect search need and execute
                result = self.search_and_answer(user_input, use_search=None, show_sources=show_sources)
                print(f"Agent: {result['answer']}\n")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")


def main():
    """Main function to run the QA Agent"""
    
    try:
        # Initialize agent
        agent = QAAgent()
        
        print("✅ QA Agent initialized successfully!")
        print(f"📡 API URL: {agent.api_url}")
        print(f"🤖 Default Model: {agent.default_model}")
        
        # Run interactive mode
        agent.interactive_mode()
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\n💡 Please create a .env file with your API_KEY")
        print("   You can copy .env.example and fill in your key.\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
