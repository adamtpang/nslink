import { GoogleGenerativeAI } from "@google/generative-ai";
import { NextResponse } from "next/server";

// Hard to Vary: Define the Strict Schema we want
const PROMPT = `
Analyze this router label image (likely CelcomDigi TP-Link). Extract the following fields strictly in JSON format:
- serial_number (Labelled as S/N)
- default_ssid (Labelled as "2.4G SSID" or just "SSID". If multiple, prefer 2.4G)
- default_pass (Labelled as "Wireless Password/PIN" or "Password")
- mac_address (Labelled as MAC)

If a field is not visible, return null.
Do not guess.
Return ONLY raw JSON.
`;

export async function POST(req: Request) {
  try {
    const { image } = await req.json();

    // Remove data:image/jpeg;base64, prefix if present
    const base64Image = image.replace(/^data:image\/\w+;base64,/, "");

    const genAI = new GoogleGenerativeAI(process.env.GOOGLE_API_KEY!);
    const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

    const result = await model.generateContent([
      PROMPT,
      {
        inlineData: {
          data: base64Image,
          mimeType: "image/jpeg",
        },
      },
    ]);

    const response = await result.response;
    const text = response.text();

    // Cleanup JSON markdown if Gemini adds it
    const jsonString = text.replace(/```json/g, "").replace(/```/g, "").trim();
    const data = JSON.parse(jsonString);

    return NextResponse.json(data);
  } catch (error) {
    console.error("AI Scan Error:", error);
    return NextResponse.json({ error: "Scan Failed" }, { status: 500 });
  }
}