from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from google.genai import types
import os

app = FastAPI()

class RequestBody(BaseModel):
    user_input: str

# Data embedded directly for the agent
JURISDICTIONS = {
    "Federal": {"type": "CLC", "term_pay": "1 wk/yr (min 2wks, max 8)", "sev_pay": "Greater of: 2 days/yr OR 5 days total", "note": "Banks, Airlines, Telecom"},
    "Ontario": {"type": "ESA", "term_pay": "1 wk/yr (max 8)", "sev_pay": "1 wk/yr (max 26) IF payroll >$2.5M & tenure >5yrs"},
    "Manitoba": {"scale": [0, 1, 2, 4, 6, 8], "thresholds": [0.08, 1, 3, 5, 10]},
    "BC": {"scale": [0, 1, 2, 3, 4, 5, 6, 7, 8], "thresholds": [0.25, 1, 3, 4, 5, 6, 7, 8]},
    "Alberta": {"scale": [0, 1, 2, 4, 5, 6, 8], "thresholds": [0.25, 2, 4, 6, 8, 10]},
    "Saskatchewan": {"scale": [0, 1, 2, 4, 6, 8], "thresholds": [0.25, 1, 3, 5, 10]},
    "Quebec": {"scale": [0, 1, 2, 4, 8], "thresholds": [0.25, 1, 5, 10], "note": "Reasonable notice required under Civil Code"}
}

SYSTEM_PROMPT = f"""
You are the "Sovereignty National Severance Auditor." 

DATABASE: {JURISDICTIONS}

CORE OPERATING PROTOCOL:
1. Intake: Identify Province, Tenure, and Job Title.
2. Jurisdictional Check: 
   - If user works in Banking, Telecom, or Airlines, use "Federal" rules.
   - If Ontario, assume $2.5M payroll unless told otherwise.
3. Statutory Calculation: Use the DATABASE to find the "Floor."
4. Common Law Calculation: Apply Bardal Factors. Target: ~1 month/year for skilled roles.
5. Output: Provide an Audit Report comparing the Statutory Minimum vs. the Common Law Target.
"""

@app.post("/api/audit")
async def audit(body: RequestBody):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    response = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=body.user_input,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[types.Tool(code_execution=types.ToolCodeExecution)],
            thinking_config=types.ThinkingConfig(thinking_level="HIGH")
        )
    )
    return {"audit": response.text}
