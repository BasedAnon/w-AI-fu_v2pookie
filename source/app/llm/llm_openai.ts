import axios from 'axios';

// Assuming these types are defined somewhere in your project
import { Result } from "../types/Result";
import { LLM_GEN_ERRORS } from "./llm_interface";

class OpenAI {
  private baseUrl: string;
  private apiKey: string;

  constructor(baseUrl: string, apiKey: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  async chatCompletionsCreate(model: string, messages: any[], temperature: number): Promise<Result<string, LLM_GEN_ERRORS>> {
    try {
      const response = await axios.post(`${this.baseUrl}/completions`, {
        model: model,
        messages: messages,
        temperature: temperature,
      }, {
        headers: {
          'Content-Type': 'application/json',
          // Assuming API key is not needed for local, but structured to include it if provided
          ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` }),
        },
      });

      // Assuming the structure of the response is similar to OpenAI's and needs to be adapted if different
      const result = response.data.choices[0].message;
      return new Result(true, result, LLM_GEN_ERRORS.NONE);
    } catch (error) {
      console.error(error);
      return new Result(false, "API request failed", LLM_GEN_ERRORS.UNDEFINED);
    }
  }
}

// Example usage
const client = new OpenAI("http://localhost:1234/v1", "not-needed");

async function getCompletion() {
  const completion = await client.chatCompletionsCreate("local-model", [
    { "role": "system", "content": "Always answer in rhymes." },
    { "role": "user", "content": "Introduce yourself." }
  ], 0.7);

  if (completion.success) {
    console.log(completion.data);
  } else {
    console.error("Failed to get completion:", completion.error);
  }
}

getCompletion();
