
# Online Course Content Generation API

This project provides an API for generating detailed sections of online courses using OpenAI's GPT-3.5 model. It uses FastAPI to create the endpoints and Pydantic for data validation.

## Features

- Generate comprehensive course content with a specified word count.
- Ensure the content consists of complete sentences.
- Summarize or expand content to meet word count requirements.
- Utilize multiple OpenAI API keys in a round-robin manner for load distribution.

## Prerequisites

- Python 3.8+
- OpenAI API keys (at least one)

## Setup

1. **Clone the repository:**

    ```bash
    git clone https://github.com/Praveen9131/online_course_content_generation.git
    cd online_course_content_generation
    ```

2. **Create a `.env` file:**

    Create a `.env` file in the root directory of the project with the following content:

    ```env
    OPENAI_API_KEY_1=your_first_openai_api_key
    OPENAI_API_KEY_2=your_second_openai_api_key
    # Add more API keys if you have them
    ```

3. **Install the required dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Run the application:**

    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```

## API Endpoints

### Generate Article

- **URL:** `/generate-article`
- **Method:** `POST`
- **Request Body:**

    ```json
    {
        "sections": [
            {
                "title": "Introduction to AI",
                "word_count": "1000 to 1500",
                "info": "This section should cover the basics of AI and its applications."
            },
            {
                "title": "Advanced Machine Learning",
                "word_count": "1500",
                "info": "Detailed information about advanced machine learning techniques."
            }
        ],
        "prefixes": [
            "Welcome to the AI course.",
            "This course is designed to help you understand AI from the ground up."
        ],
        "save_conversation_history": true
    }
    ```

- **Response:**

    ```json
    {
        "result": [
            {
                "title": "Introduction to AI",
                "content": "Generated content for Introduction to AI...",
                "word_count": 1200
            },
            {
                "title": "Advanced Machine Learning",
                "content": "Generated content for Advanced Machine Learning...",
                "word_count": 1500
            }
        ]
    }
    ```

## How It Works

1. **Environment Variables:**

    The API keys are loaded from the `.env` file. The keys are stored in a list and used in a round-robin manner to distribute the load.

2. **Request Processing:**

    The `process_requests` function handles incoming requests, iterating through the sections to generate the requested content.

3. **Text Generation:**

    The `generate_article` function constructs a prompt and makes a request to the OpenAI API to generate the content. It ensures the generated text meets the specified word count and consists of complete sentences.

4. **Word Count Adjustment:**

    The `adjust_word_count` function either summarizes or expands the generated text to fit within the specified word count range.

5. **Completing Sentences:**

    The `complete_text` function ensures that the generated text ends with a complete sentence.

## Dependencies

- `fastapi`
- `pydantic`
- `openai`
- `python-dotenv`
- `uvicorn`

Install dependencies using:

```bash
pip install -r requirements.txt
```

## Running Tests

To run the tests, use the following command:

```bash
pytest
```

## Contributing

Feel free to open issues or submit pull requests for any improvements or bug fixes.

## License

This project is licensed under the MIT License.
