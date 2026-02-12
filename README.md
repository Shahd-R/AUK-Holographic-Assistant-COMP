
# AUK AI Holographic Assistant
[![MIT License](https://img.shields.io/badge/License-Apache2.0-red.svg)](https://choosealicense.com/licenses/apache-2.0/)

An innovative Holographic Assistant delivering intuitive interactions through NLP and immersive 3D visuals. Enhances Human-Computer interaction (HCI) via intuitive voice-based interactions. Provides real-time, intelligent access to academic and administrive services at AUK.




## Authors

- [Homer Alnowaif](https://www.github.com/Gwizzlyy)
- [Maryam AlMulla](https://www.github.com/maryamalmullax)
- [Shahd Abdouh](https://www.github.com/Shahd-R)
- [Jasem AlSanea](https://www.github.com/jals27)
- Under Supervision of [Dr. Marwa Sharawi](https://www.researchgate.net/profile/Marwa-Sharawi-2)


## Features

- Local fine-tuned and trained LLaMA model on AUK data.
- Voice Activation using OpenWakeWord & RealtimeSTT.
- Speech-to-text and text-to-speech.
- Fallback to web and OpenAI GPT-4 for fact-checks.
- MPV-controlled avatar with idle/talking animations.


## Installation

Clone the Repository

```bash
  git clone https://github.com/Shahd-R/AUK-Holographic-Assistant-COMP.git
```
Create a Python Environment

```bash
    python -m venv env
    source env/bin/activate # Windows: env\Scripts\activate
```
## Deployment

To deploy this project, first download the [AI Model](https://huggingface.co/Gwizzly/model500).

Create a Python 3.12 Environment and run
```bash
  pip install -r requirements.txt
```
Download [mpv](https://mpv.io/) and add it to PATH (User PATH Variables) and setup the pipe socket .

Launch ```python main.py``` after secrets are configured.

Change Wakeword activation to other modes like ```manual_recorder()```.
```python
if __name__ == "__main__":
    mpv_process = start_mpv_player()
    try:
        manual_recorder() #Comment out all the code in between "try" and "except KeyboardInterrupt"
    except KeyboardInterrupt:
        print("\nTerminated.")
        if mpv_process:
            mpv_process.terminate()
```

Manual Mode:
`m` for typing
`[ENTER]` for push-to-talk

Voice Activation Mode: say "Hello Wolfy!" and ask your question.



## Environment Variables / Secrets

To run this project, you will need to add the following environment variables.

`ELEVENLABS_KEY`

`onnx_path`

`model_path`

`mpv_path`

## Web lookup Functionality
On running as-is, program will look up queries on DuckDuckGo using its API for questions the llm model feels unconfident in its answer. It always outputs the first result which can be hit-or-miss. The API also has a bit of a bug where it sometimes gives an Error 202 (RateLimit). In the case of either of these being bothersome,that portion of the code can be commented out and the program will then default to apologising and stating that it is unconfident to answer the user query instead.
```python
        ####################### WEB SEARCH CAPABILITY ######################
        # Can be used to use DuckDuckGo for looking up the question when the llms confidence is low
        # Outputs the first web result it finds
        #If removed, the AI will instead apologise and state that they are unsure of the answer instead.
    
        
    elif low_conf in words:
        print(" Low confidence detected ; using web search...")
        global search_query
        global yay
        search_query= locc
        results = search_client.text(
            keywords=search_query,
            region="wt_wt",
            safesearch="off",
            max_results=1
        )
        print(results)
        output= results[0]["body"]
        
        print(f"\nAssistant says:" + results[0]["body"])
        play_response(output)
       # start_recorder()
    
    #######################################################################################
```
## Example Questions
- "How many credits do I need to graduate from AUK?"
- "How can I pay my tuiton?"
- "What documents do I need to apply?"
- "Who is the president of AUK?"
## Project Structure

```
.
├── main.py                 # Updated Main script
├── model.gguf              # LLaMA model file
├── Hellow_wolfy!.onnx      # Wakeword model
├── p_idle.mp4              # Idle animation video
├── p_talking.mp4           # Talking animation video
├── requirements.txt        # (Updated) Includes all the dependencies
└── README.md
```
## Acknowledgements

 - [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT)
 - [Augmentoolkit](https://github.com/e-p-armstrong/augmentoolkit)



## License

[Apache 2.0](https://choosealicense.com/licenses/apache-2.0/)

