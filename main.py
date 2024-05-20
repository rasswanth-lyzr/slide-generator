import ast
import os
import random
import re

import streamlit as st
from dotenv import load_dotenv
from lyzr_automata import Agent, Task
from lyzr_automata.ai_models.openai import OpenAIModel
from lyzr_automata.memory.open_ai import OpenAIMemory
from lyzr_automata.tasks.task_literals import InputType, OutputType

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AGENTS_FILE = "assistant_ids.json"


def create_image_for_slides(input_text):
    open_ai_model_image = OpenAIModel(
        api_key=OPENAI_API_KEY,
        parameters={
            "n": 1,
            "model": "dall-e-3",
        },
    )

    storyboard_creation_task = Task(
        name="Storyboard Image Creation",
        output_type=OutputType.IMAGE,
        input_type=InputType.TEXT,
        model=open_ai_model_image,
        log_output=True,
        instructions="Generate an image with the given prompt. Capture every detail. Minimalistic and cartoon style. [IMPORTANT!] Avoid any text or numbers in the image.",
        default_input=input_text,
    ).execute()

    file_path = storyboard_creation_task.local_file_path

    return file_path


open_ai_model_text = OpenAIModel(
    api_key=OPENAI_API_KEY,
    parameters={
        "model": "gpt-4-turbo-preview",
        "temperature": 0.2,
        "max_tokens": 1500,
    },
)


def generate_content(saved_file_path, NUMBER_OF_SLIDES=3):

    email_writer_memory = OpenAIMemory(file_path=saved_file_path)

    summary_generation_agent = Agent(
        prompt_persona="""You are a summary generator agent designed to assist with summarizing content from files. The goal is to generate concise and accurate summaries that can be used for content creation, such as slide presentations.
        Your task is to read the content of the file, identify the key points and main ideas, and generate a summary. The summary should be clear, concise, and well-organized, capturing the essence of the original content.
        Output - Provide a summarized version of the content. The summary should be divided into sections if the original content is lengthy or complex.
    """,
        role="Summary generation agent",
        memory=email_writer_memory,
    )

    summary_generation_task = Task(
        name="Generate Summary Task",
        agent=summary_generation_agent,
        output_type=OutputType.TEXT,
        input_type=InputType.TEXT,
        model=open_ai_model_text,
        instructions=f"Summarize the content provided in the file into {NUMBER_OF_SLIDES} slides. Do not miss any detail.",
        log_output=True,
        enhance_prompt=False,
    ).execute()

    presentation_generation_agent = Agent(
        prompt_persona="""You are a presentation generator agent that can generate interactive presentation on a given topic for a Learning management system. You have 4 output formats:
    1. Heading - Output Format - <HEADING>{Slide Heading}</HEADING>
    2. Text - Output Format - <TEXT>{Content in bullet points}</TEXT>
    3. MCQ - Output Format - <QUESTION>{Generated question here}</QUESTION>, <OPTIONS>[Option1, Option2, Option3]</OPTIONS>, <ANSWER>{Option1}</ANSWER>
    4. Image - Output Format - <IMAGE>{Prompt to generate image}</IMAGE>
    At the end of each slide, append <!END OF SLIDE>
    """,
        role="Presentation generator agent",
    )

    presentation_generator_task = Task(
        name="Generate Presentation Task",
        agent=presentation_generation_agent,
        output_type=OutputType.TEXT,
        input_type=InputType.TEXT,
        model=open_ai_model_text,
        instructions=f"Generate a presentation with ONLY {NUMBER_OF_SLIDES} slides based on the given input content. Make sure all the content fits, don't worry about slide limit. Create an image for each slide. Create MCQs only for important or complex topics. Feel free to use your creativity to generate TEXT.",
        log_output=True,
        enhance_prompt=False,
        previous_output=summary_generation_task,
        input_tasks=[summary_generation_task],
    ).execute()

    return presentation_generator_task


def save_uploaded_file(uploaded_file):
    if os.path.exists(AGENTS_FILE):
        os.remove(AGENTS_FILE)
    save_path = os.path.join("uploads", uploaded_file.name)
    os.makedirs("uploads", exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return save_path


patterns = {
    "TEXT": re.compile(r"<TEXT>(.*?)</TEXT>", re.DOTALL),
    "IMAGE": re.compile(r"<IMAGE>(.*?)</IMAGE>", re.DOTALL),
    "QUESTION": re.compile(r"<QUESTION>(.*?)</QUESTION>", re.DOTALL),
    "OPTIONS": re.compile(r"<OPTIONS>(.*?)</OPTIONS>", re.DOTALL),
    "ANSWER": re.compile(r"<ANSWER>(.*?)</ANSWER>", re.DOTALL),
    "HEADING": re.compile(r"<HEADING>(.*?)</HEADING>", re.DOTALL),
}


def extract_content(slide):
    extracted_content = {}
    for key, pattern in patterns.items():
        match = pattern.search(slide)
        if match:
            extracted_content[key] = match.group(1).strip()
    return extracted_content


def normalize(text):
    return text.strip().lower().replace('"', "")


def template_1(slide):
    cols = st.columns([1, 2])
    with cols[0]:
        st.image(
            slide.get("IMAGE_URL", ""),
            caption=slide.get("IMAGE", ""),
            use_column_width=True,
        )
    with cols[1]:
        for key, value in slide.items():
            if key == "TEXT":
                st.subheader(key)
                st.write(value)
            elif key == "QUESTION":
                st.subheader(key)
                st.write(value)
            elif key == "OPTIONS":
                options = ast.literal_eval(value)
                correct_answer = slide.get("ANSWER", "")
                st.subheader(key)
                for option in options:
                    if normalize(option) == normalize(correct_answer):
                        st.write(f"*- :green[{option}]*")
                    else:
                        st.write(f"*- {option}*")


# Function to display slide with image on the right and text on the left
def template_2(slide):
    cols = st.columns([2, 1])
    with cols[0]:
        for key, value in slide.items():
            if key == "TEXT":
                st.subheader(key)
                st.write(value)
            elif key == "QUESTION":
                st.subheader(key)
                st.write(value)
            elif key == "OPTIONS":
                options = ast.literal_eval(value)
                correct_answer = slide.get("ANSWER", "")
                st.subheader(key)
                for option in options:
                    if normalize(option) == normalize(correct_answer):
                        st.write(f"*- :green[{option}]*")
                    else:
                        st.write(f"*- {option}*")
    with cols[1]:
        st.image(
            slide.get("IMAGE_URL", ""),
            caption=slide.get("IMAGE", ""),
            use_column_width=True,
        )


# Streamlit app
st.title("Slide Generator")
NUMBER_OF_SLIDES = st.number_input(
    "Number of slides?", min_value=1, max_value=5, step=1
)
uploaded_file = st.file_uploader("Choose a file")
submit_button = st.button("Submit")
if submit_button:
    saved_file_path = save_uploaded_file(uploaded_file)
    generated_content = generate_content(saved_file_path, NUMBER_OF_SLIDES)
    # generated_content = '<HEADING>Core Values at Nuveda</HEADING>\n<TEXT>\n- Encourage open, honest, and constructive communication for growth.\n- Prioritize customer value to enhance product and business.\n- Embrace accountability with a proactive "See It, Own It, Solve It, Do It" mindset.\n</TEXT>\n<QUESTION>Which of the following best represents Nuveda\'s approach to accountability?</QUESTION>\n<OPTIONS>["See It, Own It, Solve It, Do It", "Wait for instructions", "Delegate tasks to avoid responsibility"]</OPTIONS>\n<ANSWER>"See It, Own It, Solve It, Do It"</ANSWER>\n<IMAGE>Prompt: Illustration of a team meeting emphasizing open communication, customer focus, and accountability.</IMAGE>\n<!END OF SLIDE>\n\n<HEADING>Maintaining Professional Respect and Demanding Excellence</HEADING>\n<TEXT>\n- Foster a positive working environment with mutual respect.\n- Set and demand excellence from oneself and others.\n- Engage in continuous learning and constructive feedback.\n</TEXT>\n<QUESTION>What is essential for fostering a positive working environment according to Nuveda?</QUESTION>\n<OPTIONS>["Mutual respect and politeness", "Competitive mindset", "Isolation of teams"]</OPTIONS>\n<ANSWER>"Mutual respect and politeness"</ANSWER>\n<IMAGE>Prompt: Visual representation of a respectful interaction between colleagues with a background of excellence and learning.</IMAGE>\n<!END OF SLIDE>\n\n<HEADING>Ownership and Generosity In The Workplace</HEADING>\n<TEXT>\n- Take responsibility and ownership of tasks, regardless of role.\n- Be generous with assistance and curiosity to solve problems.\n</TEXT>\n<QUESTION>What does Nuveda emphasize to ensure the organization thrives?</QUESTION>\n<OPTIONS>["Acting like an owner", "Following orders", "Keeping knowledge to oneself"]</OPTIONS>\n<ANSWER>"Acting like an owner"</ANSWER>\n<IMAGE>Prompt: Image depicting an employee taking ownership of their work with a background of generosity and teamwork.</IMAGE>\n<!END OF SLIDE>'
    # generated_content = '<HEADING>Core Value 1: Be Open, Honest, and Constructive</HEADING>\n<TEXT>\n- Emphasize open, honest communication for constructive decisions.\n- Address issues directly to foster transparency and growth.\n- Encourages a culture of clear and positive dialogue.\n</TEXT>\n<IMAGE>Prompt to generate image: Illustration of two colleagues engaging in an open and honest discussion, with transparent thought bubbles showing constructive feedback.</IMAGE>\n<QUESTION>Why is open and honest communication important in Nuveda\'s culture?</QUESTION>\n<OPTIONS>["It fosters an environment of transparency and growth", "It reduces the need for meetings", "It eliminates all workplace challenges"]</OPTIONS>\n<ANSWER>It fosters an environment of transparency and growth</ANSWER>\n<!END OF SLIDE>\n\n<HEADING>Core Value 2: Always Focus on Customer Value</HEADING>\n<TEXT>\n- Understand and cater to customer needs for product and business improvement.\n- Shift perspective to see customer demands as valuable.\n- Prioritizes customer satisfaction in every decision.\n</TEXT>\n<IMAGE>Prompt to generate image: A graphic showing the transition from viewing customer demands as burdens to seeing them as opportunities for growth.</IMAGE>\n<!END OF SLIDE>\n\n<HEADING>Core Value 3: Be Accountable for What You Do</HEADING>\n<TEXT>\n- Promote personal accountability and proactive problem-solving.\n- Encourage addressing potential issues and thinking ahead.\n- Accountability leads to achieving desired outcomes.\n</TEXT>\n<IMAGE>Prompt to generate image: Visualization of a person standing firmly on the ground with various tasks and challenges being juggled, symbolizing accountability.</IMAGE>\n<QUESTION>What does personal accountability in the workplace encourage?</QUESTION>\n<OPTIONS>["Avoiding responsibilities", "Proactive problem-solving and thinking ahead", "Leaving issues to be solved by others"]</OPTIONS>\n<ANSWER>Proactive problem-solving and thinking ahead</ANSWER>\n<!END OF SLIDE>\n\n<HEADING>Core Value 4: Be Respectful Always</HEADING>\n<TEXT>\n- Advocate for mutual respect to foster a positive work environment.\n- Address issues with civility and understanding.\n- Respect is foundational to a collaborative culture.\n</TEXT>\n<IMAGE>Prompt to generate image: A diverse group of employees in a circle, listening attentively to each other, symbolizing mutual respect.</IMAGE>\n<!END OF SLIDE>'
    slides = generated_content.split("<!END OF SLIDE>")
    slides_content = [extract_content(slide) for slide in slides if slide.strip()]

    for slide in slides_content:
        if "IMAGE" in slide:
            slide["IMAGE_URL"] = create_image_for_slides(slide["IMAGE"])
            # slide["IMAGE_URL"] = "img2.jpg"

    for i, slide in enumerate(slides_content):
        headr_text = slide["HEADING"]
        st.header(f":red[{headr_text}]")
        slide.pop("HEADING")
        template = random.choice([template_1, template_2])
        template(slide)

        st.markdown("---")
