from openai import OpenAI

api_key = "inpput your api key here."
client = OpenAI(api_key=api_key)

#gpt4Turbo = "gpt-4-1106-preview"

def generate_responses(prompt, model="gpt-4-turbo-2024-04-09"):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant who provides information to users."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.9,
        max_tokens=4096,
    )

    return response.choices[0].message.content
print(generate_responses("Input prompt here."))