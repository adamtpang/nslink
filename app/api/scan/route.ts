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

    // Gemini on Replicate typically expects a prompt and image input
    // We use the alias 'google/gemini-1.5-pro'

    const prompt = `
    Analyze this router label image. Extract the following fields strictly in JSON format:
    - serial_number (Labelled as S/N)
    - default_ssid (Labelled as "2.4G SSID" or just "SSID". If multiple, prefer 2.4G. Example: "B4B@celcomdigi_2.4Ghz")
    - default_pass (Labelled as "Wireless Password/PIN" or "Password")
    - target_ssid (Leave this null, user will input later)

    If a field is not visible, return null.
    Do not guess.
    Return ONLY raw JSON. No markdown code blocks.
    `;

    const output = await replicate.run(
      "google/gemini-1.5-pro",
      {
        input: {
          image: image,
          prompt: prompt,
        }
      }
    );

    // Replicate output for Gemini might be a stream or string.
    // We handle both cases.
    const resultText = Array.isArray(output) ? output.join("") : String(output);

    console.log("Replicate Gemini Output:", resultText);

    // Cleanup JSON markdown if present
    const jsonString = resultText.replace(/```json/g, '').replace(/```/g, '').trim();

    try {
      const parsedData = JSON.parse(jsonString);
      return NextResponse.json(parsedData);
    } catch (e) {
      console.error("JSON Parse Error:", e);
      // Fallback regex extraction
      const snMatch = resultText.match(/S\/N[:\s]*([A-Z0-9]+)/i);
      if (snMatch) {
        return NextResponse.json({
          serial_number: snMatch[1],
          default_ssid: "",
          default_pass: "",
          target_ssid: null
        });
      }
      return NextResponse.json({ error: 'Failed to parse AI response' }, { status: 500 });
    }

  } catch (error) {
    console.error('Scan Error:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}