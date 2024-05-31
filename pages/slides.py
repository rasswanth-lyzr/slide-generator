import os
import re

import streamlit as st
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from lyzr_automata import Agent, Task
from lyzr_automata.ai_models.openai import OpenAIModel
from lyzr_automata.tasks.task_literals import InputType, OutputType

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

open_ai_model_text = OpenAIModel(
    api_key=OPENAI_API_KEY,
    parameters={
        "model": "gpt-4o",
        "temperature": 0.2,
        "max_tokens": 1500,
    },
)


# ["Bullet Points","Single Choice Quiz","Multiple Choice Quiz","True/False Quiz","Fill in the Blank Quiz"]
def generate_slide_content(input_content, slide_type):
    presentation_generation_agent = Agent(
        prompt_persona="""You are a slide generator agent that can generate interactive slide for a presentation on a given topic for a Learning management system. You have following output formats:
    1. Bullet Points - Format - <TEXT>5 bullet points</TEXT> <IMAGE>Query to search the internet for a suitable image</IMAGE>
    2. Single Choice Quiz - Format - <QUESTION>Generated question</QUESTION> <OPTIONS>[Option1, Option2, Option3]</OPTIONS> <ANSWER>Option1</ANSWER>
    3. Multiple Choice Quiz - Format - <QUESTION>Generated question</QUESTION> <OPTIONS>[Option1, Option2, Option3]</OPTIONS> <ANSWER>{Option1, Option 2</ANSWER>
    4. True/False Quiz - Format - <QUESTION>Generated question</QUESTION> <ANSWER>True/False</ANSWER>
    5. Fill in the blank Quiz - Format - <QUESTION>Generated question</QUESTION> <ANSWER>Fill in the blank</ANSWER>

    Single Choice Quiz has only 1 correct answer, Multiple Choice Quiz has more than 1 correct answers.
    Each output format should contain a heading and a text - <HEADING>Slide Heading</HEADING> <TEXT>3 bullet points</TEXT>
    Generate TEXT in a way it explains the content in an easy to understand way, with more words. Feel free to use your creativity to expand on the topic/content. Generate enough Quiz questions to cover the topic/content.
""",
        role="Presentation generator agent",
    )

    presentation_generator_task = Task(
        name="Generate Presentation Task",
        agent=presentation_generation_agent,
        output_type=OutputType.TEXT,
        input_type=InputType.TEXT,
        model=open_ai_model_text,
        instructions=f"Content: {input_content}, Output Type: {slide_type}. Generate a slide for the given content. Each TEXT block should contain more than 100 words.",
        log_output=True,
        enhance_prompt=False,
    ).execute()

    return presentation_generator_task


patterns = {
    "TEXT": re.compile(r"<TEXT>(.*?)</TEXT>", re.DOTALL),
    "IMAGE": re.compile(r"<IMAGE>(.*?)</IMAGE>", re.DOTALL),
    "QUESTION": re.compile(r"<QUESTION>(.*?)</QUESTION>", re.DOTALL),
    "OPTIONS": re.compile(r"<OPTIONS>(.*?)</OPTIONS>", re.DOTALL),
    "ANSWER": re.compile(r"<ANSWER>(.*?)</ANSWER>", re.DOTALL),
    "HEADING": re.compile(r"<HEADING>(.*?)</HEADING>", re.DOTALL),
}


def extract_content(slide_content):
    extracted_content = {}

    # Extract single occurrences of TEXT, IMAGE, and HEADING
    for key in ["TEXT", "IMAGE", "HEADING"]:
        pattern = patterns[key]
        match = pattern.search(slide_content)
        if match:
            extracted_content[key] = match.group(1).strip()

    # Extract multiple occurrences of QUESTION, OPTIONS, and ANSWER
    for key in ["QUESTION", "OPTIONS", "ANSWER"]:
        pattern = patterns[key]
        matches = pattern.findall(slide_content)
        if matches:
            extracted_content[key] = [match.strip() for match in matches]

    return extracted_content


def search_image_online(prompt):
    results = DDGS().images(
        keywords=prompt,
        region="wt-wt",
        safesearch="off",
        size=None,
        type_image="photo",
        license_image="share",
        max_results=1,
    )

    return results


final_slides = st.session_state.slides

generate_slides = st.button("Generate Slides")
output_slides_list = []

# output_slides_list = [{'type': 'Single Choice Quiz', 'generated_content': "<HEADING>Core Values and Communication</HEADING>  \n<TEXT>  \n- **Be Open, Honest, and Constructive**: Emphasizes the importance of transparent and honest communication for personal and company growth. Positive confrontation is encouraged to resolve issues, leading to stronger relationships among colleagues.  \n- **Example**: A scenario where a problem with a colleague's work habits is openly discussed, resulting in improved teamwork and friendship.  \n</TEXT>  \n<QUESTION>What is emphasized as important for personal and company growth?</QUESTION>  \n<OPTIONS>[Transparent and honest communication, Avoiding confrontation, Ignoring issues]</OPTIONS>  \n<ANSWER>{Transparent and honest communication}</ANSWER>"}, {'type': 'Bullet Points', 'generated_content': '<HEADING>Customer Focus and Accountability</HEADING>  \n<TEXT>\n- **Always Focus on Customer Value**: Prioritizing customer needs enhances the product and business. Understanding customer demands leads to greater appreciation from clients.\n- **Be Accountable for What You Do**: Encourages taking initiative to see, own, solve, and do tasks to achieve results. Ownership is highlighted as key to resolving broader issues proactively.\n- **Example**: Taking extra days to solve a pervasive problem in the app, demonstrating proactive problem-solving and ownership.\n</TEXT>  \n<IMAGE>{Illustration of a team working together to solve a customer issue, showcasing accountability and customer focus}</IMAGE>'}, {'type': 'Multiple Choice Quiz', 'generated_content': '<HEADING>Respect and Excellence</HEADING>  \n<TEXT>  \n- **Be Respectful Always**: Stresses the importance of mutual respect in the workplace for a positive environment. Addressing issues directly with individuals can lead to constructive changes.  \n- **Demand Excellence**: Highlights the importance of self-expectation of excellence and the continuous pursuit of quality, especially in response to customer feedback.  \n- **Example**: Improving testing practices after a customer complaint showcases a commitment to excellence and client satisfaction.  \n</TEXT>  \n<QUESTION>Which of the following best describes the importance of mutual respect in the workplace?</QUESTION>  \n<OPTIONS>[It creates a positive environment, It leads to constructive changes, Both of the above]</OPTIONS>  \n<ANSWER>{Both of the above}</ANSWER>  \n\n<QUESTION>What does demanding excellence in the workplace involve?</QUESTION>  \n<OPTIONS>[Self-expectation of excellence, Continuous pursuit of quality, Both of the above]</OPTIONS>  \n<ANSWER>{Both of the above}</ANSWER>  \n\n<QUESTION>How can addressing issues directly with individuals benefit the workplace?</QUESTION>  \n<OPTIONS>[It can lead to constructive changes, It can create conflicts, It has no impact]</OPTIONS>  \n<ANSWER>{It can lead to constructive changes}</ANSWER>  \n\n<QUESTION>What is an example of demonstrating a commitment to excellence?</QUESTION>  \n<OPTIONS>[Ignoring customer complaints, Improving testing practices after a customer complaint, Maintaining the status quo]</OPTIONS>  \n<ANSWER>{Improving testing practices after a customer complaint}</ANSWER>'}, {'type': 'True/False Quiz', 'generated_content': "<HEADING>Continuous Learning and Ownership</HEADING>  \n<TEXT>Continuous learning and ownership are crucial for personal and professional growth. Encouraging learning from various sources, including colleagues, customers, and everyday experiences, fosters a culture of openness and improvement. Being open to correction and learning from mistakes is invaluable. Acting like an owner means taking responsibility and ownership of tasks, promoting a culture where everyone feels involved and invested in the company's success. For example, an employee who proactively resolves a website issue outside their job scope demonstrates true ownership.</TEXT>  \n\n<QUESTION>Continuous learning involves being open to correction and learning from mistakes.</QUESTION>  \n<ANSWER>True</ANSWER>  \n\n<QUESTION>Acting like an owner means only focusing on tasks within your job description.</QUESTION>  \n<ANSWER>False</ANSWER>  \n\n<QUESTION>Proactively resolving issues outside your job scope is an example of ownership.</QUESTION>  \n<ANSWER>True</ANSWER>"}, {'type': 'Fill in the Blank Quiz', 'generated_content': "<HEADING>Generosity and Support</HEADING>\n\n<TEXT>\n- **Give Whenever and Wherever Possible**: It's important to extend help and support in any capacity. Even simple questions can have a significant impact in aiding colleagues. This approach fosters a supportive and collaborative work environment.\n- **Example**: A team member assists another by asking insightful questions. This demonstrates how non-expertise help can lead to solutions, further promoting a culture of generosity and support within the team.\n</TEXT>\n\n<QUESTION>Generosity and support in the workplace can be demonstrated by extending help and support in any capacity, highlighting the impact of even simple _______ in aiding colleagues.</QUESTION> \n\n<ANSWER>questions</ANSWER>\n\n<IMAGE>{Illustration of a team member assisting another by asking questions}</IMAGE>"}]
# output_slides_list = [
#     {
#         "type": "Single Choice Quiz",
#         "generated_content": {
#             "TEXT": "- **Be Open, Honest, and Constructive**: Emphasizes the importance of transparent and honest communication for personal and company growth. Positive confrontation is encouraged to resolve issues, leading to stronger relationships among colleagues.  \n- **Example**: A scenario where a problem with a colleague's work habits is openly discussed, resulting in improved teamwork and friendship.",
#             "HEADING": "Core Values and Communication",
#             "QUESTION": [
#                 "What is emphasized as important for personal and company growth?"
#             ],
#             "OPTIONS": [
#                 "[Transparent and honest communication, Avoiding confrontation, Ignoring issues]"
#             ],
#             "ANSWER": ["{Transparent and honest communication}"],
#         },
#     },
#     {
#         "type": "Bullet Points",
#         "generated_content": {
#             "TEXT": "- **Always Focus on Customer Value**: Prioritizing customer needs enhances the product and business. Understanding customer demands leads to greater appreciation from clients.\n- **Be Accountable for What You Do**: Encourages taking initiative to see, own, solve, and do tasks to achieve results. Ownership is highlighted as key to resolving broader issues proactively.\n- **Example**: Taking extra days to solve a pervasive problem in the app, demonstrating proactive problem-solving and ownership.",
#             "IMAGE": "{Illustration of a team working together to solve a customer issue, showcasing accountability and customer focus}",
#             "HEADING": "Customer Focus and Accountability",
#         },
#     },
#     {
#         "type": "Multiple Choice Quiz",
#         "generated_content": {
#             "TEXT": "- **Be Respectful Always**: Stresses the importance of mutual respect in the workplace for a positive environment. Addressing issues directly with individuals can lead to constructive changes.  \n- **Demand Excellence**: Highlights the importance of self-expectation of excellence and the continuous pursuit of quality, especially in response to customer feedback.  \n- **Example**: Improving testing practices after a customer complaint showcases a commitment to excellence and client satisfaction.",
#             "HEADING": "Respect and Excellence",
#             "QUESTION": [
#                 "Which of the following best describes the importance of mutual respect in the workplace?",
#                 "What does demanding excellence in the workplace involve?",
#                 "How can addressing issues directly with individuals benefit the workplace?",
#                 "What is an example of demonstrating a commitment to excellence?",
#             ],
#             "OPTIONS": [
#                 "[It creates a positive environment, It leads to constructive changes, Both of the above]",
#                 "[Self-expectation of excellence, Continuous pursuit of quality, Both of the above]",
#                 "[It can lead to constructive changes, It can create conflicts, It has no impact]",
#                 "[Ignoring customer complaints, Improving testing practices after a customer complaint, Maintaining the status quo]",
#             ],
#             "ANSWER": [
#                 "{Both of the above}",
#                 "{Both of the above}",
#                 "{It can lead to constructive changes}",
#                 "{Improving testing practices after a customer complaint}",
#             ],
#         },
#     },
#     {
#         "type": "True/False Quiz",
#         "generated_content": {
#             "TEXT": "Continuous learning and ownership are crucial for personal and professional growth. Encouraging learning from various sources, including colleagues, customers, and everyday experiences, fosters a culture of openness and improvement. Being open to correction and learning from mistakes is invaluable. Acting like an owner means taking responsibility and ownership of tasks, promoting a culture where everyone feels involved and invested in the company's success. For example, an employee who proactively resolves a website issue outside their job scope demonstrates true ownership.",
#             "HEADING": "Continuous Learning and Ownership",
#             "QUESTION": [
#                 "Continuous learning involves being open to correction and learning from mistakes.",
#                 "Acting like an owner means only focusing on tasks within your job description.",
#                 "Proactively resolving issues outside your job scope is an example of ownership.",
#             ],
#             "ANSWER": ["True", "False", "True"],
#         },
#     },
#     {
#         "type": "Fill in the Blank Quiz",
#         "generated_content": {
#             "TEXT": "- **Give Whenever and Wherever Possible**: It's important to extend help and support in any capacity. Even simple questions can have a significant impact in aiding colleagues. This approach fosters a supportive and collaborative work environment.\n- **Example**: A team member assists another by asking insightful questions. This demonstrates how non-expertise help can lead to solutions, further promoting a culture of generosity and support within the team.",
#             "IMAGE": "{Illustration of a team member assisting another by asking questions}",
#             "HEADING": "Generosity and Support",
#             "QUESTION": [
#                 "Generosity and support in the workplace can be demonstrated by extending help and support in any capacity, highlighting the impact of even simple _______ in aiding colleagues."
#             ],
#             "ANSWER": ["questions"],
#         },
#     },
# ]

if generate_slides:
    for slide in final_slides:
        generated_slide = generate_slide_content(slide["content"], slide["type"])
        extracted_content = extract_content(generated_slide)
        output_dict = {
            "type": slide["type"],
            "generated_content": extracted_content,
        }
        output_slides_list.append(output_dict)

    for slide in output_slides_list:
        heading = slide["generated_content"]["HEADING"]
        text = slide["generated_content"]["TEXT"]
        type = slide["type"]

        image = slide["generated_content"].get("IMAGE")
        questions = slide["generated_content"].get("QUESTION", [])
        answers = slide["generated_content"].get("ANSWER", [])
        options = slide["generated_content"].get("OPTIONS", [])

        st.write(f"# {heading}")
        st.write(f"### Type - {type}")
        st.write(text)
        if image:
            st.write("IMAGE PROMPT: " + image)
            image_result = search_image_online(image)
            image_url = image_result[0]["image"]
            st.image(image_url, use_column_width="always")
        if questions:
            st.write("#### QUESTIONS: ")
            for question in questions:
                st.write(question)
        if answers:
            st.write("#### ANSWERS: ")
            for answer in answers:
                st.write(answer)
        if options:
            st.write("#### OPTIONS: ")
            for option in options:
                st.write(option)
        st.write("---")
