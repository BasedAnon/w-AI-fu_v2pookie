import axios from 'axios';
import { Character } from "../characters/character";
import { Result } from "../types/Result";
import { wAIfu } from "../types/Waifu";
import {
    LLM_GEN_ERRORS,
    ILargeLanguageModel,
    LlmGenerationSettings,
} from "./llm_interface";
import { IO } from "../io/io";
import { getCurrentCharacter } from "../characters/characters";

type GPTChatEntry = {
    role: "function" | "system" | "user" | "assistant";
    content: string;
};

const GENERATION_TIMEOUT_MS = 10_000 as const;

export class LargeLanguageModelOpenAI implements ILargeLanguageModel {
    #apiEndpoint: string;
    #apiKey: string;

    constructor() {
        // Switch between OpenAI and local endpoint here
        this.#apiEndpoint = process.env.USE_LOCAL_LLM ? 'http://localhost:5000' : 'https://api.openai.com';
        this.#apiKey = wAIfu.state!.auth.openai.token;
    }

    async initialize(): Promise<void> {
        IO.debug("Loaded LargeLanguageModelOpenAI.");
        return;
    }

    async free(): Promise<void> {
        return;
    }

    async generate(
        prompt: string,
        settings: LlmGenerationSettings
    ): Promise<Result<string, LLM_GEN_ERRORS>> {
        return new Promise(async (resolve) => {
            const data = {
                model: "text-davinci-003", // Adjust model as needed
                prompt: prompt,
                temperature: settings.temperature,
                max_tokens: settings.max_output_length,
                // Add other parameters as needed
            };

            axios.post(`${this.#apiEndpoint}/v1/completions`, data, {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.#apiKey}`
                },
                timeout: GENERATION_TIMEOUT_MS
            }).then(response => {
                const result = response.data.choices[0].text.trim();
                resolve(new Result(true, result, LLM_GEN_ERRORS.NONE));
            }).catch(error => {
                // Handle error (e.g., network error, invalid API key, etc.)
                console.error(error);
                resolve(new Result(false, "API request failed", LLM_GEN_ERRORS.UNDEFINED));
            });
        });
    }
}
