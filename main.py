import os

import streamlit as st
from dotenv import load_dotenv
from lyzr_automata import Agent, Task
from lyzr_automata.ai_models.openai import OpenAIModel
from lyzr_automata.memory.open_ai import OpenAIMemory
from lyzr_automata.tasks.task_literals import InputType, OutputType

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AGENTS_FILE = "assistant_ids.json"

OUTPUT_TYPES = [
    "Bullet Points",
    "Single Choice Quiz",
    "Multiple Choice Quiz",
    "True/False Quiz",
    "Fill in the Blank Quiz",
]


open_ai_model_text = OpenAIModel(
    api_key=OPENAI_API_KEY,
    parameters={
        "model": "gpt-4-turbo-preview",
        "temperature": 0.1,
        "max_tokens": 1500,
    },
)


def generate_summary(saved_file_path, NUMBER_OF_SLIDES=3):
    email_writer_memory = OpenAIMemory(file_path=saved_file_path)

    summary_generation_agent = Agent(
        prompt_persona="""You are a summary generator agent designed to assist with summarizing content from files. The goal is to generate concise and accurate summaries that can be used for content creation, such as slide presentations.
        Your task is to read the content of the file, identify the key points and main ideas, and generate a summary. The summary should be clear, concise, and well-organized, capturing the essence of the original content.
        Output - Provide a summarized version of the content. The summary should be divided into sections if the original content is lengthy or complex.
        Do not include any introductory sentences or closing sentences.
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
        instructions=f"Summarize the content provided in the file into {NUMBER_OF_SLIDES} slides. Do not miss any detail. At the end of each slide, append <!END OF SLIDE>",
        log_output=True,
        enhance_prompt=False,
    ).execute()

    return summary_generation_task


def save_uploaded_file(uploaded_file):
    # if os.path.exists(AGENTS_FILE):
    #     os.remove(AGENTS_FILE)
    save_path = os.path.join("uploads", uploaded_file.name)
    os.makedirs("uploads", exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return save_path


def edit_slides(slides):
    edited_slides = []
    for i, slide in enumerate(slides):
        st.write(f"**Slide {i + 1}**")
        st.write(slide["content"])
        edited_slide = st.text_area(
            f"Edit Slide {i + 1}", value=slide["content"], height=200
        )
        slide_type = st.selectbox(f"Select slide type {i+1}", OUTPUT_TYPES)
        slide_dict = {"content": edited_slide, "type": slide_type}
        edited_slides.append(slide_dict)
    return edited_slides


# Streamlit app
st.title("Slide Generator")
NUMBER_OF_SLIDES = st.number_input(
    "Number of slides?", min_value=1, max_value=5, step=1
)
uploaded_file = st.file_uploader("Choose a file")
submit_button = st.button("Submit File")


if "slides" not in st.session_state:
    st.session_state.slides = []

if submit_button:
    saved_file_path = save_uploaded_file(uploaded_file)
    st.session_state.file_path = saved_file_path
    summarized_content = generate_summary(saved_file_path, NUMBER_OF_SLIDES)
    # summarized_content = "**Slide 1: Core Values of Nuveda**\n1. **Be Open, Honest and Constructive**: Emphasizes the importance of transparent communication for constructive decision-making and growth. Sharing issues openly can transform relationships positively.\n2. **Always Focus on Customer Value**: Highlights the necessity of understanding and meeting customer demands for the improvement of products and services, which leads to increased customer appreciation.\n3. **Be Accountable for What You Do**: Encourages taking responsibility for one’s actions and outcomes, promoting the mentality of seeing, owning, solving, and doing tasks to achieve desired results.\n<!END OF SLIDE>\n\n**Slide 2: Professional and Ethical Conduct**\n1. **Be Respectful Always**: Stresses treating everyone with respect to foster a mutually respectful environment. Direct communication can ameliorate personal interactions.\n2. **Demand Excellence**: Urges first demanding excellence from oneself and then from others, teaching the importance of self-reflection and proactive problem-solving for maintaining high standards.\n3. **Learn Always**: Advocates for continuous learning from peers, situations, and daily interactions. Being open to correction and questions fuels personal and professional growth.\n<!END OF SLIDE>\n\n**Slide 3: Leadership and Community Contribution**\n1. **Act Like an Owner**: Inspires taking ownership of tasks beyond designated responsibilities, fostering a culture where leaders and team members are invested and proactive.\n2. **Give Whenever and Wherever Possible**: Encourages helping others in any way possible. Even without specific knowledge, showing interest and asking questions can lead to solutions for others.\n<!END OF SLIDE>"
    # summarized_content = "**Slide 1: Core Values and Communication**  \n- **Be Open, Honest, and Constructive**: Emphasizes the importance of transparent and honest communication for personal and company growth. Positive confrontation is encouraged to resolve issues, leading to stronger relationships among colleagues.\n- **Example**: A scenario where a problem with a colleague's work habits is openly discussed, resulting in improved teamwork and friendship.  \n<!END OF SLIDE>\n\n**Slide 2: Customer Focus and Accountability**  \n- **Always Focus on Customer Value**: Prioritizing customer needs enhances the product and business. Understanding customer demands leads to greater appreciation from clients.\n- **Be Accountable for What You Do**: Encourages taking initiative to see, own, solve, and do tasks to achieve results. Ownership is highlighted as key to resolving broader issues proactively.\n- **Example**: Taking extra days to solve a pervasive problem in the app, demonstrating proactive problem-solving and ownership.\n<!END OF SLIDE>\n\n**Slide 3: Respect and Excellence**  \n- **Be Respectful Always**: Stresses the importance of mutual respect in the workplace for a positive environment. Addressing issues directly with individuals can lead to constructive changes.\n- **Demand Excellence**: Highlights the importance of self-expectation of excellence and the continuous pursuit of quality, especially in response to customer feedback.\n- **Example**: Improving testing practices after a customer complaint showcases a commitment to excellence and client satisfaction.\n<!END OF SLIDE>\n\n**Slide 4: Continuous Learning and Ownership**  \n- **Learn Always**: Encourages learning from a variety of sources including others, customers, and daily experiences. Openness to being corrected and learning from it is seen as invaluable.\n- **Act like an Owner**: Calls for responsibility and ownership of tasks, promoting a culture where everyone feels involved and invested in the company's success.\n- **Example**: An employee proactively resolving a website issue outside their job scope demonstrates ownership.\n<!END OF SLIDE>\n\n**Slide 5: Generosity and Support**  \n- **Give Whenever and Wherever Possible**: Advocates for extending help and support in any capacity, highlighting the impact of even simple questions in aiding colleagues.\n- **Example**: A team member assists another by asking insightful questions, demonstrating how non-expertise help can lead to solutions, fostering a supportive and collaborative work environment.\n<!END OF SLIDE>"
    summary_split_content = summarized_content.split("<!END OF SLIDE>")
    summary_split_content = [
        item.strip() for item in summary_split_content if item.strip() != ""
    ]
    for slide in summary_split_content:
        slide_dict = {"content": slide, "type": "Bullet Points"}
        st.session_state.slides.append(slide_dict)

if st.session_state.slides:
    edited_slides = edit_slides(st.session_state.slides)

    if st.button("Save Changes"):
        st.session_state.slides = edited_slides
        st.success("Changes Saved!")
        st.write("## Go to next page!")
        st.page_link("pages/slides.py", label="Generate Slides", icon="📄")
