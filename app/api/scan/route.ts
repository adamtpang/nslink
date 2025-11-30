import { NextResponse } from 'next/server';
import Replicate from "replicate";

const replicate = new Replicate({
  auth: process.env.REPLICATE_API_TOKEN,
});

export const maxDuration = 60; // Allow longer timeout for AI

export async function POST(req: Request) {
  try {
    const { image } = await req.json();

    if (!image) {
      return NextResponse.json({ error: 'No image provided' }, { status: 400 });
    }

    // Prompt optimized for Llama 3.2 Vision
    const prompt = `
    You are a router configuration assistant. Analyze this image of a router label.
    Extract the following information and return it in strict JSON format:
    - serial_number: The S/N or Serial Number.
    - default_ssid: The 2.4GHz SSID or default SSID.
    - default_pass: The Wireless Password, PIN, or Key.
    - target_ssid: (Leave empty/null, this is for user input later)

    If a field is not found, return null for that field.
    Do not include any markdown formatting (like \`\`\`json). Just return the raw JSON object.
    `;

    const output = await replicate.run(
      "meta/llama-3.2-11b-vision-instruct:06a3075882e9ddc333c55a847d74da943f42a91257d7a5e1c5ace3743e914d5f",
      {
        input: {
          image: image,
          prompt: prompt,
          max_tokens: 512,
          temperature: 0.1 // Low temperature for deterministic output
        }
      }
    );

    // Replicate returns an array of strings for streaming, or a single string.
    // Llama 3.2 Vision usually returns a stream of tokens. We need to join them.
    const resultText = Array.isArray(output) ? output.join("") : String(output);

    console.log("Replicate Output:", resultText);

    // Clean up the output to ensure it's valid JSON
    const jsonString = resultText.replace(/```json/g, '').replace(/```/g, '').trim();

    try {
      const parsedData = JSON.parse(jsonString);
      return NextResponse.json(parsedData);
    } catch (e) {
      console.error("JSON Parse Error:", e);
      // Fallback: Try to find JSON-like structure if parsing fails
      const match = jsonString.match(/\{[\s\S]*\}/);
      if (match) {
        return NextResponse.json(JSON.parse(match[0]));
      }
      return NextResponse.json({ error: 'Failed to parse AI response' }, { status: 500 });
    }

  } catch (error) {
    console.error('Scan Error:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}